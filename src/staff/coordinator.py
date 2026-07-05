import json
import uuid
import os
import secrets

from datetime import datetime
from typing import Tuple, Any
from . import auth as staff_auth
from .index_db import (
    create_staff_index, open_staff_index, close_staff_index,
    add_staff_summary, get_staff_by_username, get_all_staff,
    update_staff_active, delete_staff_summary, get_staff_summary
)
from .staff_db import (
    create_staff_db, open_staff_db, get_profile, save_profile,
    get_availability, set_availability, get_holidays, set_holidays
)
from ..crypto_engine import get_master_key, verify_mep
from ..staff import auth as staff_auth

class StaffCoordinator:
    def __init__(self, root_data_dir: str):
        self.root_data_dir = root_data_dir
        # Ensure staff index exists (create if not)
        staff_data_dir = os.path.join(root_data_dir, 'staff')
        if not os.path.exists(os.path.join(staff_data_dir, 'index.db')):
            create_staff_index(root_data_dir)

    def handle(self, method: str, path: str, body: str = None, headers: dict = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        # Public endpoints
        if path == '/auth/login' and method == 'POST':
            return self._login(body)
        if path == '/auth/logout' and method == 'POST':
            return self._logout(token)

        # All other endpoints require valid session
        session = staff_auth.verify_session(token)
        if not session:
            return {'error': 'Unauthorized'}, 401

        # Routes
        if path == '/staff/me' and method == 'GET':
            return self._get_my_profile(session)
        if path == '/staff/me' and method == 'PUT':
            return self._update_my_profile(session, body)
        if path == '/staff/me/availability' and method == 'GET':
            return self._get_my_availability(session)
        if path == '/staff/me/availability' and method == 'PUT':
            return self._update_my_availability(session, body)
        if path == '/staff/me/holidays' and method == 'GET':
            return self._get_my_holidays(session)
        if path == '/staff/me/holidays' and method == 'PUT':
            return self._update_my_holidays(session, body)
        if path == '/staff/me/password' and method == 'PUT':
            return self._change_my_password(session, body)

        # Admin only
        if session['role'] != 'admin':
            return {'error': 'Forbidden'}, 403
        if path == '/staff' and method == 'GET':
            return self._list_staff()
        if path == '/staff' and method == 'POST':
            return self._create_staff(body)
        if path.startswith('/staff/approve/'):
            uuid_str = path.split('/')[-1]
            if method == 'POST':
                return self._approve_staff(uuid_str, body)
        if path.startswith('/staff/'):
            uuid_str = path.split('/')[-1]
            if method == 'DELETE':
                return self._delete_staff(uuid_str, body)
            if method == 'GET':
                return self._get_staff_detail(uuid_str)
        return {'error': 'Not found'}, 404

    # --- Helper to open staff DB for a user ---
    def _open_staff_db_for_uuid(self, uuid_str: str):
        """
        Return (db_conn, staff_dict) for the given staff UUID.
        Closes the index connection before returning.
        """
        index_conn = open_staff_index(self.root_data_dir)
        try:
            staff = get_staff_summary(index_conn, uuid_str)
            if not staff:
                close_staff_index(index_conn)
                return None, None
            db_dir = os.path.join(self.root_data_dir, 'staff', 'databases')
            os.makedirs(db_dir, exist_ok=True)
            db_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
            close_staff_index(index_conn)   # we no longer need the index
            return db_conn, staff
        except:
            close_staff_index(index_conn)
            raise

    # --- Endpoints ---
    def _login(self, body):
        data = _parse_body(body)
        username = data.get('username', '')
        password = data.get('password', '')
        result = staff_auth.login(self.root_data_dir, username, password)
        if result:
            return result, 200
        return {'error': 'Invalid credentials or inactive account'}, 401

    def _logout(self, token):
        staff_auth.logout(token)
        return {'success': True}, 200

    def _get_my_profile(self, session):
        db_conn, _ = self._open_staff_db_for_uuid(session['user_uuid'])
        try:
            profile = get_profile(db_conn)
            # Remove sensitive fields
            for k in ('password_hash', 'password_salt'):
                profile.pop(k, None)
            return profile, 200
        finally:
            db_conn.close()

    def _update_my_profile(self, session, body):
        data = _parse_body(body)
        db_conn, _ = self._open_staff_db_for_uuid(session['user_uuid'])
        try:
            profile = get_profile(db_conn)
            allowed = ['full_name', 'display_name', 'email', 'phone', 'timezone',
                       'default_hourly_rate', 'default_meeting_link_pattern', 'bio',
                       'payout_taxes_json', 'payment_methods_json']
            for key in allowed:
                if key in data:
                    profile[key] = data[key]
            profile['updated_at'] = datetime.utcnow().isoformat()
            save_profile(db_conn, profile)
            return {'success': True}, 200
        finally:
            db_conn.close()

    def _get_my_availability(self, session):
        db_conn, _ = self._open_staff_db_for_uuid(session['user_uuid'])
        try:
            return get_availability(db_conn), 200
        finally:
            db_conn.close()

    def _update_my_availability(self, session, body):
        data = _parse_body(body)
        slots = data.get('slots', [])
        # For non-admin, set status to 'pending'
        if session['role'] != 'admin':
            for s in slots:
                s['status'] = 'pending'
        db_conn, _ = self._open_staff_db_for_uuid(session['user_uuid'])
        try:
            set_availability(db_conn, slots)
            return {'success': True}, 200
        finally:
            db_conn.close()

    def _get_my_holidays(self, session):
        db_conn, _ = self._open_staff_db_for_uuid(session['user_uuid'])
        try:
            return get_holidays(db_conn), 200
        finally:
            db_conn.close()

    def _update_my_holidays(self, session, body):
        data = _parse_body(body)
        holidays = data.get('holidays', [])
        if session['role'] != 'admin':
            for h in holidays:
                h['status'] = 'pending'
        db_conn, _ = self._open_staff_db_for_uuid(session['user_uuid'])
        try:
            set_holidays(db_conn, holidays)
            return {'success': True}, 200
        finally:
            db_conn.close()

    def _change_my_password(self, session, body):
        data = _parse_body(body)
        old_pw = data.get('old_password', '')
        new_pw = data.get('new_password', '')
        if len(new_pw) < 6:
            return {'error': 'New password too short'}, 400
        db_conn, _ = self._open_staff_db_for_uuid(session['user_uuid'])
        try:
            profile = get_profile(db_conn)
            from ..students.crypto import verify_password, hash_password
            if not verify_password(old_pw, profile['password_salt'], profile['password_hash']):
                return {'error': 'Incorrect old password'}, 403
            new_salt = secrets.token_bytes(16)
            new_hash, _ = hash_password(new_pw, new_salt)
            profile['password_salt'] = new_salt
            profile['password_hash'] = new_hash
            profile['password_last_changed'] = datetime.utcnow().isoformat()
            profile['must_change_password'] = False
            save_profile(db_conn, profile)
            return {'success': True}, 200
        finally:
            db_conn.close()

    # Admin endpoints
    def _list_staff(self):
        index_conn = open_staff_index(self.root_data_dir)
        try:
            staff = get_all_staff(index_conn)
            return staff, 200
        finally:
            close_staff_index(index_conn)

    def _create_staff(self, body):
        data = _parse_body(body)
        username = data.get('username', '')
        role = data.get('role', 'teacher')
        full_name = data.get('full_name', '')
        password = data.get('password', '')
        if not username or not password:
            return {'error': 'username and password required'}, 400
        if role not in ['admin', 'teacher', 'front_office', 'back_office', 'bot']:
            return {'error': 'Invalid role'}, 400
        new_uuid = uuid.uuid4().hex
        db_dir = os.path.join(self.root_data_dir, 'staff', 'databases')
        db_key = create_staff_db(db_dir, new_uuid)
        # Save profile
        db_conn = open_staff_db(db_dir, new_uuid, db_key)
        try:
            from ..students.crypto import hash_password
            salt = secrets.token_bytes(16)
            pw_hash, _ = hash_password(password, salt)
            profile = {
                'uuid': new_uuid,
                'username': username,
                'full_name': full_name,
                'display_name': full_name,
                'email': '',
                'phone': '',
                'timezone': 'Asia/Yangon',
                'default_hourly_rate': 0,
                'default_meeting_link_pattern': '',
                'bio': '',
                'role': role,
                'is_active': False,   # must be approved
                'password_hash': pw_hash,
                'password_salt': salt,
                'password_last_changed': datetime.utcnow().isoformat(),
                'must_change_password': False,
                'payout_taxes_json': '{}',
                'payment_methods_json': '{}',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            save_profile(db_conn, profile)
        finally:
            db_conn.close()
        # Add to index
        index_conn = open_staff_index(self.root_data_dir)
        try:
            add_staff_summary(index_conn, new_uuid, username, role, db_key, is_active=False)
        finally:
            close_staff_index(index_conn)
        return {'uuid': new_uuid}, 201

    def _approve_staff(self, uuid_str, body):
        data = _parse_body(body)
        mep_password = data.get('mep_password', '')
        if not verify_mep(self.root_data_dir, mep_password):
            return {'error': 'Invalid master encryption password'}, 403
        index_conn = open_staff_index(self.root_data_dir)
        try:
            update_staff_active(index_conn, uuid_str, True)
            # Also update the profile's is_active flag
            staff = get_staff_summary(index_conn, uuid_str)
            if not staff:
                return {'error': 'Staff not found'}, 404
            db_dir = os.path.join(self.root_data_dir, 'staff', 'databases')
            db_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
            try:
                profile = get_profile(db_conn)
                profile['is_active'] = True
                save_profile(db_conn, profile)
            finally:
                db_conn.close()
            return {'success': True}, 200
        finally:
            close_staff_index(index_conn)

    def _delete_staff(self, uuid_str, body):
        # Requires MEP re-entry
        data = _parse_body(body)
        mep_password = data.get('mep_password', '')
        if not verify_mep(self.root_data_dir, mep_password):
            return {'error': 'Invalid master encryption password'}, 403
        # Remove per-staff DB
        db_dir = os.path.join(self.root_data_dir, 'staff', 'databases')
        db_path = os.path.join(db_dir, f"{uuid_str}.sqlite")
        if os.path.exists(db_path):
            os.remove(db_path)
        # Remove index entry
        index_conn = open_staff_index(self.root_data_dir)
        try:
            delete_staff_summary(index_conn, uuid_str)
        finally:
            close_staff_index(index_conn)
        return {'success': True}, 200

    def _get_staff_detail(self, uuid_str):
        index_conn = open_staff_index(self.root_data_dir)
        try:
            staff = get_staff_summary(index_conn, uuid_str)
            if not staff:
                return {'error': 'Not found'}, 404
            db_dir = os.path.join(self.root_data_dir, 'staff', 'databases')
            db_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
            try:
                profile = get_profile(db_conn)
                # Remove sensitive
                for k in ('password_hash', 'password_salt'):
                    profile.pop(k, None)
                return profile, 200
            finally:
                db_conn.close()
        finally:
            close_staff_index(index_conn)

def _parse_body(body: str) -> Any:
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}
