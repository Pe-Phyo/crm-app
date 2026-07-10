import json
import uuid
import os
from typing import Tuple, Any

from . import auth as auth_module
from . import index_db as index
from . import student_db as student
from ..staff import auth as staff_auth


class StudentCoordinator:
    def __init__(self, data_dir: str, master_key: bytes = None, root_data_dir: str = None):
        self.data_dir = data_dir
        self.master_key = master_key
        self.root_data_dir = root_data_dir if root_data_dir else data_dir

    def handle(self, method: str, path: str, body: str = None, headers: dict = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        if not auth_module.verify_token(token) and not staff_auth.verify_session(token):
            return {'error': 'Unauthorized'}, 401

        # Auth endpoints (unchanged)
        if path == '/auth/status' and method == 'GET':
            return self._status()
        if path == '/auth/setup' and method == 'POST':
            return self._setup(body)
        if path == '/auth/login' and method == 'POST':
            return self._login(body)

        # All student routes require index DB
        try:
            conn = index.open_index_db_with_key(self.data_dir, self.master_key)
        except Exception as e:
            return {'error': f'Cannot open index: {str(e)}'}, 500

        try:
            # Only profile endpoints
            if path == '/students' and method == 'GET':
                return self._list_students(conn)
            if path == '/students' and method == 'POST':
                return self._create_student(conn, body)
            if path.startswith('/students/'):
                parts = path.split('/')
                student_uuid = parts[2]
                if len(parts) == 3:
                    if method == 'GET':
                        return self._get_student(conn, student_uuid)
                    if method == 'PUT':
                        return self._update_student(conn, student_uuid, body)
                    if method == 'DELETE':
                        return self._delete_student(conn, student_uuid, body)
            return {'error': 'Not found'}, 404
        finally:
            index.close_index_db(conn)

    # ---- Auth ----
    def _status(self):
        index_db_path = os.path.join(self.data_dir, 'index.db')
        return {'setup': os.path.exists(index_db_path)}, 200

    def _setup(self, body: str) -> Tuple[Any, int]:
        if os.path.exists(os.path.join(self.data_dir, 'index.db')):
            return {'error': 'Already set up'}, 400
        data = _parse_body(body)
        password = data.get('password', '')
        if len(password) < 6:
            return {'error': 'Password too short'}, 400
        try:
            auth_module.setup_master_password(self.data_dir, password, root_data_dir=self.root_data_dir)
            return {'success': True}, 200
        except ValueError as e:
            return {'error': str(e)}, 400

    def _login(self, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        password = data.get('password', '')
        token = auth_module.login(self.root_data_dir, password)
        if token is None:
            return {'error': 'Invalid password'}, 401
        return {'token': token}, 200

    # ---- Student CRUD (profile only) ----
    def _list_students(self, conn) -> Tuple[Any, int]:
        return index.get_all_students(conn), 200

    def _create_student(self, conn, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        new_uuid = uuid.uuid4().hex
        student_db_dir = os.path.join(self.data_dir, 'students')
        key = student.create_student_db(student_db_dir, new_uuid)

        profile = {
            'uuid': new_uuid,
            'name': data.get('name', ''),
            'location': '',
            'timezone': data.get('timezone', ''),
            'age_group': data.get('age_group', 'Adult'),
            'academic_year': data.get('academic_year', ''),
            'telegram': data.get('telegram', ''),
            'is_minor': data.get('is_minor', False),
            'parent_name': data.get('parent_name', ''),
            'school_name': data.get('school_name', ''),
            'educational_goals': data.get('educational_goals', ''),
            'behavioral_comments': '',
            'general_comments': data.get('general_comments', ''),
            'birthdate': data.get('birthdate', '')
        }

        sconn = student.open_student_db(student_db_dir, new_uuid, key)
        try:
            student.save_profile(sconn, profile)
            student.set_phones(sconn, data.get('phones', []))
            student.set_emails(sconn, data.get('emails', []))
            student.set_parent_phones(sconn, data.get('parent_phones', []))
            student.set_parent_emails(sconn, data.get('parent_emails', []))
            student.set_relationships(sconn, data.get('linked_students', []))
            sconn.commit()
        finally:
            sconn.close()

        # Index entry (minimal)
        tz_label = data.get('timezone_label', '')
        flag = index.get_flag_for_timezone_label(self.root_data_dir, tz_label) if tz_label else index.get_flag_for_timezone(self.root_data_dir, data.get('timezone', ''))
        index.add_student_summary(
            conn,
            uuid=new_uuid,
            name=profile['name'],
            location='',
            timezone=profile['timezone'],
            rate=0,
            last_payment_date='',
            attendance_percentage=0.0,
            meeting_times_summary='',
            status='active',
            db_key=key,
            flag=flag
        )

        return {'uuid': new_uuid}, 201

    def _get_student(self, conn, uuid: str) -> Tuple[Any, int]:
        key = index.get_student_db_key(conn, uuid)
        if not key:
            return {'error': 'Student not found'}, 404
        student_db_dir = os.path.join(self.data_dir, 'students')
        sconn = student.open_student_db(student_db_dir, uuid, key)
        try:
            profile = student.get_profile(sconn)
            profile['phones'] = student.get_phones(sconn)
            profile['emails'] = student.get_emails(sconn)
            profile['parent_phones'] = student.get_parent_phones(sconn)
            profile['parent_emails'] = student.get_parent_emails(sconn)
            profile['relationships'] = student.get_relationships(sconn)
            profile['meeting_times'] = student.get_meeting_times(sconn)  # re-added
        finally:
            sconn.close()
        return profile, 200

    def _update_student(self, conn, uuid: str, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        key = index.get_student_db_key(conn, uuid)
        if not key:
            return {'error': 'Student not found'}, 404
        student_db_dir = os.path.join(self.data_dir, 'students')
        sconn = student.open_student_db(student_db_dir, uuid, key)
        try:
            profile = student.get_profile(sconn)
            allowed = ['name', 'timezone', 'age_group', 'academic_year', 'telegram',
                       'parent_name', 'school_name', 'educational_goals', 'general_comments',
                       'is_minor', 'birthdate']
            for field in allowed:
                if field in data:
                    profile[field] = data[field]
            student.save_profile(sconn, profile)

            if 'phones' in data:
                student.set_phones(sconn, data['phones'])
            if 'emails' in data:
                student.set_emails(sconn, data['emails'])
            if 'parent_phones' in data:
                student.set_parent_phones(sconn, data['parent_phones'])
            if 'parent_emails' in data:
                student.set_parent_emails(sconn, data['parent_emails'])
            if 'linked_students' in data:
                student.set_relationships(sconn, data['linked_students'])

            if 'timezone' in data:
                tz_label = data.get('timezone_label', '')
                flag = index.get_flag_for_timezone_label(self.root_data_dir, tz_label) if tz_label else index.get_flag_for_timezone(self.root_data_dir, data['timezone'])
                index.update_student_summary(conn, uuid, timezone=data['timezone'], flag=flag)
            if 'name' in data:
                index.update_student_summary(conn, uuid, name=data['name'])

            sconn.commit()
        finally:
            sconn.close()
        return {'success': True}, 200

    def _delete_student(self, conn, uuid: str, body: str = None) -> Tuple[Any, int]:
        # Password required for deletion
        data = _parse_body(body) if body else {}
        password = data.get('password', '')
        if not password:
            return {'error': 'Password required'}, 400
        if not auth_module.verify_master_password(self.root_data_dir, password):
            return {'error': 'Invalid password'}, 403
        key = index.get_student_db_key(conn, uuid)
        if not key:
            return {'error': 'Student not found'}, 404
        student_db_dir = os.path.join(self.data_dir, 'students')
        db_path = os.path.join(student_db_dir, f"{uuid}.sqlite")
        if os.path.exists(db_path):
            os.remove(db_path)
        index.delete_student_summary(conn, uuid)
        return {'success': True}, 200


def _parse_body(body: str) -> Any:
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}