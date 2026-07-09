import json
import os
import ssl
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from .meetings import coordinator as meetings_coordinator
from .students.coordinator import StudentCoordinator
from . import crypto_engine
from .staff.coordinator import StaffCoordinator
from .dashboard.coordinator import DashboardCoordinator
from urllib.parse import parse_qs

PORT = 8080
DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # crm-app root
DATA_DIR = os.path.join(DIRECTORY, 'data')
CERTS_DIR = os.path.join(DATA_DIR, 'certs')
STUDENT_DATA_DIR = os.path.join(DATA_DIR, 'students')

def generate_ssl_context():
    """Generate root CA once, then issue a per-session server certificate."""
    os.makedirs(CERTS_DIR, exist_ok=True)
    ca_key_path = os.path.join(CERTS_DIR, 'ca.key')
    ca_cert_path = os.path.join(CERTS_DIR, 'ca.crt')

    # Load or create CA
    if not os.path.exists(ca_key_path) or not os.path.exists(ca_cert_path):
        print("🔐 Generating Root CA...")
        ca_key = rsa.generate_private_key(65537, 2048, default_backend())
        ca_subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CRM App Local CA")])
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(ca_subj)
            .issuer_name(ca_subj)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(ca_key, hashes.SHA256(), default_backend())
        )
        with open(ca_key_path, 'wb') as f:
            f.write(ca_key.private_bytes(serialization.Encoding.PEM,
                                         serialization.PrivateFormat.TraditionalOpenSSL,
                                         serialization.NoEncryption()))
        with open(ca_cert_path, 'wb') as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        print("✅ CA created.")
    else:
        with open(ca_key_path, 'rb') as f:
            ca_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
        with open(ca_cert_path, 'rb') as f:
            ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())

    # Generate server cert valid for this session
    print("🔐 Issuing session server certificate...")
    server_key = rsa.generate_private_key(65537, 2048, default_backend())
    server_subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_subj)
        .issuer_name(ca_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(hours=24))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(ca_key, hashes.SHA256(), default_backend())
    )

    # Save temporarily
    server_key_path = os.path.join(CERTS_DIR, 'server.key')
    server_cert_path = os.path.join(CERTS_DIR, 'server.crt')
    with open(server_key_path, 'wb') as f:
        f.write(server_key.private_bytes(serialization.Encoding.PEM,
                                         serialization.PrivateFormat.TraditionalOpenSSL,
                                         serialization.NoEncryption()))
    with open(server_cert_path, 'wb') as f:
        f.write(server_cert.public_bytes(serialization.Encoding.PEM))

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(server_cert_path, server_key_path)
    print("✅ Server certificate ready.")
    return ctx


class RequestHandler(SimpleHTTPRequestHandler):
    student_coordinator = None
    staff_coordinator = None
    dashboard_coordinator = None

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def translate_path(self, path):
        if path.startswith('/students/'):
            return os.path.join(DIRECTORY, 'launch', path[1:])
        if path.startswith('/dashboard/'):
            return os.path.join(DIRECTORY, 'launch', path[1:])
        return super().translate_path(path)

    def _route_api(self, method, path, body):
        # Dashboard API
        if path.startswith('/api/dashboard'):
            if self.dashboard_coordinator:
                rel_path = path[len('/api'):]
                headers = {k: v for k, v in self.headers.items()}
                # Extract query string from the full request path
                query = urlparse(self.path).query
                return self.dashboard_coordinator.handle(method, rel_path, body, headers, query=query)

        # Meetings API
        if path.startswith('/api/meetings'):
            query = urlparse(self.path).query
            return meetings_coordinator.handle(method, path, body, query=query)

        # Location data (timezone list)
        if path == '/api/locations':
            if method == 'GET':
                return self._get_locations()

        # Upcoming events (holidays/exams/school breaks)
        if path == '/api/events/upcoming':
            if method == 'GET':
                query = urlparse(self.path).query
                params = parse_qs(query)
                days = int(params.get('days', [14])[0])
                return self._get_upcoming_events(days)
        if path == '/api/events/meta':
            if method == 'GET':
                return self._get_events_meta()

        # Staff API
        if path.startswith('/api/auth/staff'):
            # Map /api/auth/staff/login → /auth/login, etc.
            sub = path[len('/api/auth/staff'):]
            if not sub.startswith('/'):
                sub = '/' + sub
            rel_path = '/auth' + sub
            if self.staff_coordinator:
                headers = {k: v for k, v in self.headers.items()}
                return self.staff_coordinator.handle(method, rel_path, body, headers)
        elif path.startswith('/api/staff'):
            if self.staff_coordinator:
                rel_path = path[len('/api'):]
                headers = {k: v for k, v in self.headers.items()}
                return self.staff_coordinator.handle(method, rel_path, body, headers)

        # Student API
        if path.startswith('/api/auth') or path.startswith('/api/students') or path.startswith('/api/actions'):
            if self.student_coordinator:
                rel_path = path[len('/api'):]
                headers = {k: v for k, v in self.headers.items()}
                return self.student_coordinator.handle(method, rel_path, body, headers)

        return {'error': 'Not found'}, 404

    def _get_locations(self):
        import json, os
        loc_file = os.path.join(DATA_DIR, 'utils', 'timezone_data.json')
        if not os.path.exists(loc_file):
            return {'error': 'Location data missing'}, 500
        with open(loc_file, 'r') as f:
            data = json.load(f)
        return {'locations': data.get('locations', [])}, 200

    def _get_upcoming_events(self, days=14):
        import json
        from datetime import date, timedelta
        data_file = os.path.join(DATA_DIR, 'utils', 'holidays.json')
        if not os.path.exists(data_file):
            return {'events': []}, 200
        with open(data_file, 'r') as f:
            data = json.load(f)
        today = date.today()
        end_date = today + timedelta(days=days)
        events = []
        for country_code, country_data in data.items():
            if country_code == 'meta':
                continue
            for category, items in country_data.items():
                for item in items:
                    start_str = item.get('start')
                    if not start_str:
                        continue
                    try:
                        event_date = date.fromisoformat(start_str)
                    except:
                        continue
                    if today <= event_date <= end_date:
                        events.append({
                            'date': start_str,
                            'end': item.get('end'),
                            'name': item['name'],
                            'type': category,
                            'country': country_code,
                            'notes': item.get('notes', '')
                        })
        events.sort(key=lambda e: e['date'])
        return {'events': events}, 200

    def _get_events_meta(self):
        import json
        data_file = os.path.join(DATA_DIR, 'utils', 'holidays.json')
        if not os.path.exists(data_file):
            return {'meta': {}}, 200
        with open(data_file, 'r') as f:
            data = json.load(f)
        return {'meta': data.get('meta', {})}, 200

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            data, status = self._route_api('GET', parsed.path, None)
            self._send_json(data, status)
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            cl = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(cl).decode() if cl > 0 else None
            data, status = self._route_api('POST', parsed.path, body)
            self._send_json(data, status)
            return
        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            cl = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(cl).decode() if cl > 0 else None
            data, status = self._route_api('PUT', parsed.path, body)
            self._send_json(data, status)
            return
        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            cl = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(cl).decode() if cl > 0 else None
            data, status = self._route_api('DELETE', parsed.path, body)
            self._send_json(data, status)
            return
        self.send_response(404)
        self.end_headers()

    def _send_json(self, data, status):
        import json
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def start():
    # Unlock master encryption key (will prompt in terminal)
    crypto_engine.unlock(DATA_DIR)

    # Init meetings DB
    from .meetings.db import init_db
    init_db()

    # Init student coordinator
    os.makedirs(STUDENT_DATA_DIR, exist_ok=True)
    student_coordinator = StudentCoordinator(
        STUDENT_DATA_DIR,
        master_key=crypto_engine.get_master_key(),
        root_data_dir=DATA_DIR
    )
    RequestHandler.student_coordinator = student_coordinator

        # Init staff coordinator
    staff_coordinator = StaffCoordinator(DATA_DIR)
    RequestHandler.staff_coordinator = staff_coordinator

    # Dashboard coordinator
    dashboard_coordinator = DashboardCoordinator()
    RequestHandler.dashboard_coordinator = dashboard_coordinator

    # SSL context
    ssl_context = generate_ssl_context()

    os.chdir(DIRECTORY)
    httpd = HTTPServer(("", PORT), RequestHandler)
    httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(1)
    webbrowser.open(f"https://localhost:{PORT}/launch/index.html")
    print(f"🔒 HTTPS server on https://localhost:{PORT}")
    print(f"   Meetings: /launch/meetings/meetings.html")
    print(f"   Students: /students/students.html")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        httpd.shutdown()