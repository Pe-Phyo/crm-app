import json
from urllib.parse import parse_qs
from typing import Tuple, Any
from .db import get_templates_for_teacher, add_template, update_template, delete_template, get_all_templates
from ...staff import auth as staff_auth
from ...students import auth as student_auth

class PricingCoordinator:
    def __init__(self):
        pass

    def handle(self, method, path, body, headers, query=None):
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        if not student_auth.verify_token(token) and not staff_auth.verify_session(token):
            return {'error': 'Unauthorized'}, 401

        # GET /pricing/templates?teacher_id=... (optional)
        if path == '/pricing/templates' and method == 'GET':
            params = parse_qs(query) if query else {}
            teacher_id = params.get('teacher_id', [None])[0]
            if teacher_id:
                templates = get_templates_for_teacher(teacher_id)
            else:
                templates = get_all_templates()
            return [t.__dict__ for t in templates], 200

        # POST /pricing/templates – create new
        if path == '/pricing/templates' and method == 'POST':
            data = _parse_body(body)
            tid = add_template(data)   # data is dict; add_template expects PackageTemplate but we can adjust if needed
            return {'id': tid}, 201

        # PUT, DELETE /pricing/templates/{id}
        if path.startswith('/pricing/templates/'):
            parts = path.split('/')
            if len(parts) == 4 and parts[3].isdigit():
                tid = int(parts[3])
                if method == 'PUT':
                    data = _parse_body(body)
                    update_template(tid, data)
                    return {'success': True}, 200
                if method == 'DELETE':
                    delete_template(tid)
                    return {'success': True}, 200

        return {'error': 'Not found'}, 404

def _parse_body(body):
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}