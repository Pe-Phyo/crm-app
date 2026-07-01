#!/usr/bin/env python3
import os
import sqlite3
import webbrowser
import threading
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from datetime import datetime

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DIRECTORY, 'data')
MEETINGS_DB = os.path.join(DATA_DIR, 'meetings', 'meetings.db')

# ============================================================
#  DATABASE INIT
# ============================================================

def init_meetings_db():
    os.makedirs(os.path.dirname(MEETINGS_DB), exist_ok=True)
    conn = sqlite3.connect(MEETINGS_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            nickname TEXT NOT NULL,
            type TEXT NOT NULL,
            student_ids TEXT NOT NULL,
            student_names TEXT NOT NULL,
            link TEXT NOT NULL,
            count INTEGER DEFAULT 8,
            rate INTEGER DEFAULT 0,
            homework TEXT DEFAULT '',
            comments TEXT DEFAULT '',
            attendance TEXT DEFAULT '',
            created TEXT DEFAULT CURRENT_TIMESTAMP,
            updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ============================================================
#  API HANDLERS
# ============================================================

def get_db():
    return sqlite3.connect(MEETINGS_DB)

def rows_to_meetings(rows):
    meetings = []
    for row in rows:
        meetings.append({
            'id': row[0],
            'day': row[1],
            'time': row[2],
            'nickname': row[3],
            'type': row[4],
            'student_ids': row[5].split(',') if row[5] else [],
            'student_names': row[6].split(',') if row[6] else [],
            'link': row[7],
            'count': row[8],
            'rate': row[9],
            'homework': row[10] or '',
            'comments': row[11] or '',
            'attendance': row[12].split(',') if row[12] else [],
            'created': row[13],
            'updated': row[14]
        })
    return meetings

def get_meetings():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM meetings ORDER BY day, time')
    rows = c.fetchall()
    conn.close()
    return rows_to_meetings(rows), 200

def add_meeting(body):
    try:
        import json
        data = json.loads(body)
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO meetings (
                id, day, time, nickname, type, student_ids, student_names,
                link, count, rate, homework, comments, attendance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['id'],
            data['day'],
            data['time'],
            data['nickname'],
            data['type'],
            ','.join(data.get('student_ids', [])),
            ','.join(data.get('student_names', [])),
            data['link'],
            data.get('count', 8),
            data.get('rate', 0),
            data.get('homework', ''),
            data.get('comments', ''),
            ','.join(data.get('attendance', []))
        ))
        conn.commit()
        conn.close()
        return {'success': True, 'id': data['id']}, 200
    except Exception as e:
        return {'error': str(e)}, 500

def update_meeting(meeting_id, body):
    try:
        import json
        data = json.loads(body)
        conn = get_db()
        c = conn.cursor()
        
        # Build the update query dynamically based on what fields are provided
        fields = []
        values = []
        
        if 'day' in data:
            fields.append('day = ?')
            values.append(data['day'])
        if 'time' in data:
            fields.append('time = ?')
            values.append(data['time'])
        if 'nickname' in data:
            fields.append('nickname = ?')
            values.append(data['nickname'])
        if 'type' in data:
            fields.append('type = ?')
            values.append(data['type'])
        if 'student_ids' in data:
            fields.append('student_ids = ?')
            values.append(','.join(data['student_ids']))
        if 'student_names' in data:
            fields.append('student_names = ?')
            values.append(','.join(data['student_names']))
        if 'link' in data:
            fields.append('link = ?')
            values.append(data['link'])
        if 'count' in data:
            fields.append('count = ?')
            values.append(data['count'])
        if 'rate' in data:
            fields.append('rate = ?')
            values.append(data['rate'])
        if 'homework' in data:
            fields.append('homework = ?')
            values.append(data['homework'])
        if 'comments' in data:
            fields.append('comments = ?')
            values.append(data['comments'])
        if 'attendance' in data:
            fields.append('attendance = ?')
            values.append(','.join(data['attendance']))
        
        # Always update the timestamp
        fields.append('updated = CURRENT_TIMESTAMP')
        
        # Add the meeting_id at the end
        values.append(meeting_id)
        
        # Build and execute the query
        query = f"UPDATE meetings SET {', '.join(fields)} WHERE id = ?"
        c.execute(query, values)
        
        conn.commit()
        conn.close()
        return {'success': True}, 200
    except Exception as e:
        print(f"Error updating meeting: {e}")  # This will show in the terminal
        return {'error': str(e)}, 500

def delete_meeting(meeting_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
        conn.commit()
        conn.close()
        return {'success': True}, 200
    except Exception as e:
        return {'error': str(e)}, 500

# ============================================================
#  HTTP SERVER
# ============================================================

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def route_api(self, method, path, body=None):
        if path == '/api/meetings':
            if method == 'GET': return get_meetings()
            if method == 'POST': return add_meeting(body)
        elif path.startswith('/api/meetings/'):
            meeting_id = path.split('/')[-1]
            if method == 'PUT': return update_meeting(meeting_id, body)
            if method == 'DELETE': return delete_meeting(meeting_id)
        return {'error': 'Not found'}, 404

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            data, status = self.route_api('GET', parsed.path)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data, status = self.route_api('POST', parsed.path, body)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data, status = self.route_api('PUT', parsed.path, body)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            data, status = self.route_api('DELETE', parsed.path)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            return
        self.send_response(404)
        self.end_headers()

# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    import json
    init_meetings_db()
    os.chdir(DIRECTORY)

    server_thread = threading.Thread(target=lambda: HTTPServer(("", PORT), CORSRequestHandler).serve_forever(), daemon=True)
    server_thread.start()

    time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT}/launch/index.html")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")