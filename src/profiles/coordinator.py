import json
import os
from typing import Tuple, Any
from . import db as profile_db
from ..staff import auth as staff_auth
from ..staff.index_db import open_staff_index, close_staff_index, get_staff_summary

class ProfileCoordinator:
    def __init__(self, root_data_dir: str):
        self.root_data_dir = root_data_dir
        self.profile_data_dir = os.path.join(root_data_dir, 'data', 'profiles')

    def handle(self, method: str, path: str, body: str = None,
               headers: dict = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        session = staff_auth.verify_session(token)
        if not session:
            return {'error': 'Unauthorized'}, 401

        # Route to correct handler
        if path == '/staff/me':
            if method == 'GET':
                return self._handle_get_own_profile(session)
            if method == 'PUT':
                return self._handle_update_own_profile(session, body)
        elif path.startswith('/staff/me/availability'):
            return self._handle_availability(session, method, body)
        elif path.startswith('/staff/me/holidays'):
            return self._handle_holidays(session, method, body)
        elif path.startswith('/staff/me/capabilities'):
            # Schema endpoint handled separately
            if path == '/staff/me/capabilities/schema' and method == 'GET':
                return self._handle_capabilities_schema(session)
            # Default CRUD for capabilities
            return self._handle_capabilities(session, method, body)

        return {'error': 'Not found'}, 404

    def _get_profile_conn(self, session):
        """Open the profile DB for the logged-in user."""
        index_conn = open_staff_index(self.root_data_dir)
        try:
            staff = get_staff_summary(index_conn, session['user_uuid'])
        finally:
            close_staff_index(index_conn)
        if not staff or not staff.get('profile_db_key'):
            return None
        return profile_db.open_profile_db(
            self.profile_data_dir, session['user_uuid'], staff['profile_db_key'])

    def _handle_get_own_profile(self, session):
        conn = self._get_profile_conn(session)
        if not conn:
            return {'error': 'Profile not found'}, 404
        try:
            details = profile_db.get_profile_details(conn)
            phones = profile_db.get_phones(conn)
            emails = profile_db.get_emails(conn)
            result = {
                **details,
                'phones': phones,
                'emails': emails,
                # Include role and username from session? Might be needed for frontend
                'role': session.get('role', ''),
                'uuid': session['user_uuid'],
            }
            return result, 200
        finally:
            conn.close()

    def _handle_update_own_profile(self, session, body):
        data = _parse_body(body)
        conn = self._get_profile_conn(session)
        if not conn:
            return {'error': 'Profile not found'}, 404
        try:
            details = profile_db.get_profile_details(conn)
            # Update only allowed fields
            allowed_fields = [
                'full_name', 'display_name', 'email', 'phone', 'timezone',
                'default_hourly_rate', 'default_meeting_link_pattern', 'bio',
                'languages'
            ]
            for key in allowed_fields:
                if key in data:
                    details[key] = data[key]

            profile_db.save_profile_details(conn, details)

            # Multi-value fields
            if 'phones' in data:
                profile_db.set_phones(conn, data['phones'])
            if 'emails' in data:
                profile_db.set_emails(conn, data['emails'])

            return {'success': True}, 200
        finally:
            conn.close()

    def _handle_availability(self, session, method, body):
        conn = self._get_profile_conn(session)
        if not conn:
            return {'error': 'Profile not found'}, 404
        try:
            if method == 'GET':
                slots = profile_db.get_availability(conn)
                return {'slots': slots}, 200
            elif method == 'PUT':
                data = _parse_body(body)
                slots = data.get('slots', [])
                # Non-admin users have their availability set to pending
                if session['role'] != 'admin':
                    for s in slots:
                        s['status'] = 'pending'
                profile_db.set_availability(conn, slots)
                return {'success': True}, 200
        finally:
            conn.close()

    def _handle_holidays(self, session, method, body):
        conn = self._get_profile_conn(session)
        if not conn:
            return {'error': 'Profile not found'}, 404
        try:
            if method == 'GET':
                holidays = profile_db.get_holidays(conn)
                return holidays, 200  # returning list directly as per existing pattern
            elif method == 'PUT':
                data = _parse_body(body)
                holidays = data.get('holidays', [])
                if session['role'] != 'admin':
                    for h in holidays:
                        h['status'] = 'pending'
                profile_db.set_holidays(conn, holidays)
                return {'success': True}, 200
        finally:
            conn.close()

    def _handle_capabilities(self, session, method, body):
        conn = self._get_profile_conn(session)
        if not conn:
            return {'error': 'Profile not found'}, 404
        try:
            if method == 'GET':
                return self._get_all_capabilities(conn), 200
            elif method == 'PUT':
                data = _parse_body(body)
                self._update_capabilities(conn, data)
                return {'success': True}, 200
        finally:
            conn.close()

    def _get_all_capabilities(self, conn):
        return {
            'teaching_subjects': profile_db.get_teaching_subjects(conn),
            'teaching_modes': profile_db.get_teaching_modes(conn),
            'teaching_styles': profile_db.get_teaching_styles(conn),
            'student_types': profile_db.get_student_types(conn),
            'curriculum_expertise': profile_db.get_curriculum_expertise(conn),
            'certifications': profile_db.get_certifications(conn),
        }

    def _update_capabilities(self, conn, data):
        if 'teaching_subjects' in data:
            profile_db.set_teaching_subjects(conn, data['teaching_subjects'])
        if 'teaching_modes' in data:
            profile_db.set_teaching_modes(conn, data['teaching_modes'])
        if 'teaching_styles' in data:
            profile_db.set_teaching_styles(conn, data['teaching_styles'])
        if 'student_types' in data:
            profile_db.set_student_types(conn, data['student_types'])
        if 'curriculum_expertise' in data:
            profile_db.set_curriculum_expertise(conn, data['curriculum_expertise'])
        if 'certifications' in data:
            profile_db.set_certifications(conn, data['certifications'])

    def _handle_capabilities_schema(self, session):
        role = session.get('role', 'teacher')
        from .schemas import ROLE_SCHEMAS
        from .schemas import base
        schema = ROLE_SCHEMAS.get(role, base.SCHEMA)
        return schema, 200


def _parse_body(body):
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}