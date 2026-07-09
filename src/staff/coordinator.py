import json
import os
from typing import Tuple, Any
from . import auth as staff_auth
from .index_db import create_staff_index
from .profile import (
    handle_own_profile, handle_update_own_profile,
    handle_own_availability, handle_own_holidays, handle_change_own_password
)
from .management import (
    handle_list_staff, handle_list_staff_detailed,
    handle_get_staff_detail, handle_update_staff_profile,
    handle_create_staff, handle_approve_staff, handle_delete_staff,
    handle_list_teachers, handle_reset_staff_password
)

class StaffCoordinator:
    def __init__(self, root_data_dir: str):
        self.root_data_dir = root_data_dir
        staff_data_dir = os.path.join(root_data_dir, 'staff')
        if not os.path.exists(os.path.join(staff_data_dir, 'index.db')):
            create_staff_index(root_data_dir)

    def handle(self, method: str, path: str, body: str = None, headers: dict = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')

        # Public
        if path == '/auth/login' and method == 'POST':
            data = _parse_body(body)
            username = data.get('username', '')
            password = data.get('password', '')
            result = staff_auth.login(self.root_data_dir, username, password)
            return (result, 200) if result else ({'error': 'Invalid credentials'}, 401)

        if path == '/auth/logout' and method == 'POST':
            staff_auth.logout(token)
            return {'success': True}, 200

        # Authenticated
        session = staff_auth.verify_session(token)
        if not session:
            return {'error': 'Unauthorized'}, 401

        # Open routes (any authenticated user)
        if path == '/staff/teachers' and method == 'GET':
            return handle_list_teachers(self.root_data_dir)

        if path == '/staff/me':
            if method == 'GET':
                return handle_own_profile(self.root_data_dir, session)
            if method == 'PUT':
                return handle_update_own_profile(self.root_data_dir, session, body)
        if path.startswith('/staff/me/availability'):
            return handle_own_availability(self.root_data_dir, session, method, body)
        if path.startswith('/staff/me/holidays'):
            return handle_own_holidays(self.root_data_dir, session, method, body)
        if path == '/staff/me/password' and method == 'PUT':
            return handle_change_own_password(self.root_data_dir, session, body)

        # Admin / Back-office routes
        if session['role'] not in ('admin', 'back_office'):
            return {'error': 'Forbidden'}, 403

        if path == '/staff':
            if method == 'GET':
                return handle_list_staff(self.root_data_dir)
            if method == 'POST' and session['role'] == 'admin':
                return handle_create_staff(self.root_data_dir, body)
        if path == '/staff/detailed' and method == 'GET':
            return handle_list_staff_detailed(self.root_data_dir)
        if path.startswith('/staff/approve/') and session['role'] == 'admin':
            uuid_str = path.split('/')[-1]
            return handle_approve_staff(self.root_data_dir, uuid_str, body)
        if path.startswith('/staff/'):
            uuid_str = path.split('/')[-1]
            if method == 'GET':
                return handle_get_staff_detail(self.root_data_dir, uuid_str)
            if method == 'PUT':
                if session['role'] == 'admin' or session['user_uuid'] == uuid_str:
                    return handle_update_staff_profile(self.root_data_dir, uuid_str, body)
                return {'error': 'Forbidden'}, 403
            if method == 'PUT' and path.endswith('/password'):
                if session['role'] == 'admin':
                    return handle_reset_staff_password(self.root_data_dir, uuid_str, body)
                return {'error': 'Forbidden'}, 403
            if method == 'DELETE' and session['role'] == 'admin':
                return handle_delete_staff(self.root_data_dir, uuid_str, body)

        return {'error': 'Not found'}, 404

def _parse_body(body):
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}