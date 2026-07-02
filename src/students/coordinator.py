import json
import uuid
import os
from datetime import datetime
from typing import Tuple, Any

from . import auth as auth_module
from . import index_db as index
from . import student_db as student

# ------------------------------------------------------------
class StudentCoordinator:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def handle(self, method: str, path: str, body: str = None, headers: dict = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        # Routes without auth
        if path == '/auth/setup' and method == 'POST':
            return self._setup(body)
        if path == '/auth/login' and method == 'POST':
            return self._login(body)
        # Auth required
        if not auth_module.verify_token(token):
            return {'error': 'Unauthorized'}, 401
        key = auth_module.get_session_key(token)
        if key is None:
            return {'error': 'Session expired'}, 401

        # Open index DB
        try:
            conn = index.open_index_db_with_key(self.data_dir, key)
        except Exception as e:
            return {'error': f'Cannot open index: {str(e)}'}, 500

        try:
            # Routing
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
                    elif method == 'PUT':
                        return self._update_student(conn, student_uuid, body)
                    elif method == 'DELETE':
                        return self._delete_student(conn, student_uuid)
                elif len(parts) == 4 and parts[3] == 'attendance':
                    if method == 'GET':
                        return self._get_attendance(conn, student_uuid)
                    if method == 'POST':
                        return self._add_attendance(conn, student_uuid, body)
                elif len(parts) == 5 and parts[3] == 'attendance':
                    log_id = int(parts[4])
                    if method == 'PUT':
                        return self._update_attendance(conn, student_uuid, log_id, body)
                    elif method == 'DELETE':
                        return self._delete_attendance(conn, student_uuid, log_id)
                elif len(parts) == 4 and parts[3] == 'payments':
                    if method == 'GET':
                        return self._get_payments(conn, student_uuid)
                    if method == 'POST':
                        return self._add_payment(conn, student_uuid, body)  # multipart later
            if path == '/actions' and method == 'GET':
                return self._list_actions(conn)
            if path == '/actions' and method == 'POST':
                return self._add_action(conn, body)
            if path.startswith('/actions/'):
                parts = path.split('/')
                action_id = int(parts[2])
                if method == 'PUT':
                    return self._update_action(conn, action_id, body)
                elif method == 'DELETE':
                    return self._delete_action(conn, action_id)
            return {'error': 'Not found'}, 404
        finally:
            index.close_index_db(conn)

    # Auth handlers
    def _setup(self, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        password = data.get('password', '')
        if len(password) < 6:
            return {'error': 'Password too short'}, 400
        auth_module.setup_master_password(self.data_dir, password)
        return {'success': True}, 200

    def _login(self, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        password = data.get('password', '')
        token = auth_module.login(self.data_dir, password)
        if token is None:
            return {'error': 'Invalid password'}, 401
        return {'token': token}, 200

    # Student list
    def _list_students(self, conn) -> Tuple[Any, int]:
        students = index.get_all_students(conn)
        return students, 200

    def _create_student(self, conn, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        # Generate UUID
        new_uuid = uuid.uuid4().hex
        # Create per-student DB
        student_db_dir = os.path.join(self.data_dir, 'students')
        key = student.create_student_db(student_db_dir, new_uuid)
        # Build profile from data
        profile = {
            'uuid': new_uuid,
            'name': data.get('name', ''),
            'location': data.get('location', ''),
            'timezone': data.get('timezone', ''),
            'age_group': data.get('age_group', ''),
            'academic_year': data.get('academic_year', ''),
            'phone': data.get('phone', ''),
            'telegram': data.get('telegram', ''),
            'email': data.get('email', ''),
            'is_minor': data.get('is_minor', False),
            'parent_name': data.get('parent_name', ''),
            'parent_phone': data.get('parent_phone', ''),
            'educational_goals': data.get('educational_goals', ''),
            'behavioral_comments': data.get('behavioral_comments', ''),
            'general_comments': data.get('general_comments', ''),
            'rate': data.get('rate', 0)
        }
        # Also handle meeting times if provided in data
        meeting_times = data.get('meeting_times', [])
        # Add summary to index
        summary = ', '.join([f"{mt['day'][:3]} {mt['time']} ({'Group' if mt.get('type')=='group' else 'Private'})" for mt in meeting_times])
        index.add_student_summary(
            conn,
            uuid=new_uuid,
            name=profile['name'],
            location=profile['location'],
            rate=profile['rate'],
            last_payment_date='',
            attendance_percentage=0.0,
            meeting_times_summary=summary,
            status='active',
            db_key=key
        )
        # Open student DB and save profile + meeting times
        student_conn = student.open_student_db(student_db_dir, new_uuid, key)
        try:
            student.save_profile(student_conn, profile)
            for mt in meeting_times:
                student.add_meeting_time(
                    student_conn,
                    day=mt.get('day', 'Monday'),
                    time=mt.get('time', '09:00'),
                    mtype=mt.get('type', 'private'),
                    is_in_person=mt.get('is_in_person', False),
                    meeting_id=mt.get('meeting_id')
                )
            student_conn.commit()
        finally:
            student_conn.close()
        return {'uuid': new_uuid}, 201

    def _get_student(self, conn, uuid: str) -> Tuple[Any, int]:
        # Get key from index
        key = index.get_student_db_key(conn, uuid)
        if not key:
            return {'error': 'Student not found'}, 404
        student_db_dir = os.path.join(self.data_dir, 'students')
        student_conn = student.open_student_db(student_db_dir, uuid, key)
        try:
            profile = student.get_profile(student_conn)
            profile['meeting_times'] = student.get_meeting_times(student_conn)
            profile['attendance'] = student.get_attendance(student_conn)
            profile['payments'] = student.get_payments(student_conn)
            profile['homework_reading'] = student.get_homework_reading(student_conn)
            profile['attendance_percentage'] = student.get_attendance_percentage(student_conn)
        finally:
            student_conn.close()
        return profile, 200

    def _update_student(self, conn, uuid: str, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        key = index.get_student_db_key(conn, uuid)
        if not key:
            return {'error': 'Student not found'}, 404
        student_db_dir = os.path.join(self.data_dir, 'students')
        student_conn = student.open_student_db(student_db_dir, uuid, key)
        try:
            # Update profile fields
            profile = student.get_profile(student_conn)
            for field in profile.keys():
                if field in data:
                    profile[field] = data[field]
            student.save_profile(student_conn, profile)
            # Update meeting times if provided
            if 'meeting_times' in data:
                # Replace all meeting times
                student_conn.execute("DELETE FROM meeting_times")
                for mt in data['meeting_times']:
                    student.add_meeting_time(
                        student_conn,
                        day=mt.get('day', 'Monday'),
                        time=mt.get('time', '09:00'),
                        mtype=mt.get('type', 'private'),
                        is_in_person=mt.get('is_in_person', False),
                        meeting_id=mt.get('meeting_id')
                    )
                # Update summary in index
                summary = student.get_meeting_times_summary(student_conn)
                index.update_student_summary(conn, uuid, meeting_times_summary=summary)
            # Update rate if changed
            if 'rate' in data:
                index.update_student_summary(conn, uuid, rate=data['rate'])
            # Update name/location
            if 'name' in data:
                index.update_student_summary(conn, uuid, name=data['name'])
            if 'location' in data:
                index.update_student_summary(conn, uuid, location=data['location'])
            student_conn.commit()
        finally:
            student_conn.close()
        return {'success': True}, 200

    def _delete_student(self, conn, uuid: str) -> Tuple[Any, int]:
        key = index.get_student_db_key(conn, uuid)
        if not key:
            return {'error': 'Student not found'}, 404
        # Delete the per-student DB file
        student_db_dir = os.path.join(self.data_dir, 'students')
        db_path = os.path.join(student_db_dir, f"{uuid}.sqlite")
        if os.path.exists(db_path):
            os.remove(db_path)
        # Remove from index
        index.delete_student_summary(conn, uuid)
        return {'success': True}, 200

    # Attendance
    def _get_attendance(self, conn, uuid: str) -> Tuple[Any, int]:
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        student_db_dir = os.path.join(self.data_dir, 'students')
        student_conn = student.open_student_db(student_db_dir, uuid, key)
        try:
            attendance = student.get_attendance(student_conn)
        finally:
            student_conn.close()
        return attendance, 200

    def _add_attendance(self, conn, uuid: str, body: str) -> Tuple[Any, int]:
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        data = _parse_body(body)
        meeting_id = data.get('meeting_id', '')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        status = data.get('status', 'absent')
        student_db_dir = os.path.join(self.data_dir, 'students')
        student_conn = student.open_student_db(student_db_dir, uuid, key)
        try:
            log_id = student.add_attendance(student_conn, meeting_id, date, status)
            # Update attendance percentage in index
            pct = student.get_attendance_percentage(student_conn)
            index.update_student_summary(conn, uuid, attendance_percentage=pct)
            student_conn.commit()
        finally:
            student_conn.close()
        return {'id': log_id}, 201

    def _update_attendance(self, conn, uuid: str, log_id: int, body: str) -> Tuple[Any, int]:
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        data = _parse_body(body)
        status = data.get('status')
        if not status:
            return {'error': 'status required'}, 400
        student_db_dir = os.path.join(self.data_dir, 'students')
        student_conn = student.open_student_db(student_db_dir, uuid, key)
        try:
            student.update_attendance(student_conn, log_id, status)
            pct = student.get_attendance_percentage(student_conn)
            index.update_student_summary(conn, uuid, attendance_percentage=pct)
            student_conn.commit()
        finally:
            student_conn.close()
        return {'success': True}, 200

    def _delete_attendance(self, conn, uuid: str, log_id: int) -> Tuple[Any, int]:
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        student_db_dir = os.path.join(self.data_dir, 'students')
        student_conn = student.open_student_db(student_db_dir, uuid, key)
        try:
            student.delete_attendance(student_conn, log_id)
            pct = student.get_attendance_percentage(student_conn)
            index.update_student_summary(conn, uuid, attendance_percentage=pct)
            student_conn.commit()
        finally:
            student_conn.close()
        return {'success': True}, 200

    # Payments
    def _get_payments(self, conn, uuid: str) -> Tuple[Any, int]:
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        student_db_dir = os.path.join(self.data_dir, 'students')
        student_conn = student.open_student_db(student_db_dir, uuid, key)
        try:
            payments = student.get_payments(student_conn)
        finally:
            student_conn.close()
        return payments, 200

    def _add_payment(self, conn, uuid: str, body: str) -> Tuple[Any, int]:
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        data = _parse_body(body)
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        amount = data.get('amount', 0)
        # receipt_image is not handled here; we'll support multipart later
        student_db_dir = os.path.join(self.data_dir, 'students')
        student_conn = student.open_student_db(student_db_dir, uuid, key)
        try:
            payment_id = student.add_payment(student_conn, date, amount, None)
            # Update last_payment_date in index
            index.update_student_summary(conn, uuid, last_payment_date=date)
            student_conn.commit()
        finally:
            student_conn.close()
        return {'id': payment_id}, 201

    # Action items
    def _list_actions(self, conn) -> Tuple[Any, int]:
        items = index.get_action_items(conn)
        return items, 200

    def _add_action(self, conn, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        text = data.get('text', '')
        if not text:
            return {'error': 'text required'}, 400
        id = index.add_action_item(conn, text)
        return {'id': id}, 201

    def _update_action(self, conn, action_id: int, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        index.update_action_item(conn, action_id, text=data.get('text'), done=data.get('done'))
        return {'success': True}, 200

    def _delete_action(self, conn, action_id: int) -> Tuple[Any, int]:
        index.delete_action_item(conn, action_id)
        return {'success': True}, 200

def _parse_body(body: str) -> Any:
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}