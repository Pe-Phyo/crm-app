import json
from typing import Tuple, Any

from .attendance import AttendanceService
from ..staff import auth as staff_auth
from ..students import auth as student_auth  # legacy token check


class TeacherCoordinator:
    def __init__(self, data_dir: str, master_key: bytes, root_data_dir: str = None):
        self.data_dir = data_dir
        self.master_key = master_key
        self.root_data_dir = root_data_dir if root_data_dir else data_dir
        self.attendance_service = AttendanceService(data_dir, master_key, root_data_dir)

    def handle(self, method: str, path: str, body: str = None, headers: dict = None, query: str = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        if not student_auth.verify_token(token) and not staff_auth.verify_session(token):
            return {'error': 'Unauthorized'}, 401

        # Attendance endpoints
        if path == '/teacher/attendance' and method == 'GET':
            return self._get_attendance(query)      # pass query string
        if path == '/teacher/attendance' and method == 'POST':
            return self._add_attendance(body)
        if path.startswith('/teacher/attendance/'):
            parts = path.split('/')
            if len(parts) == 4 and parts[3].isdigit():
                log_id = int(parts[3])
                if method == 'PUT':
                    return self._update_attendance(log_id, body)
                if method == 'DELETE':
                    return self._delete_attendance(log_id, body)
        return {'error': 'Not found'}, 404

    def _get_attendance(self, query: str = None):
        # Extract student_uuid from query string (e.g., "student_uuid=abc123")
        from urllib.parse import parse_qs
        params = parse_qs(query) if query else {}
        student_uuid = params.get('student_uuid', [None])[0]
        if not student_uuid:
            return {'error': 'student_uuid required'}, 400
        try:
            records = self.attendance_service.get_attendance(student_uuid)
            return records, 200
        except ValueError as e:
            return {'error': str(e)}, 404

    def _add_attendance(self, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        student_uuid = data.get('student_uuid', '')
        meeting_id = data.get('meeting_id', '')
        date = data.get('date', '')
        status = data.get('status', 'absent')
        if not student_uuid:
            return {'error': 'student_uuid required'}, 400
        try:
            log_id = self.attendance_service.add_attendance(student_uuid, meeting_id, date, status)
            return {'id': log_id}, 201
        except ValueError as e:
            return {'error': str(e)}, 404

    def _update_attendance(self, log_id: int, body: str) -> Tuple[Any, int]:
        data = _parse_body(body)
        student_uuid = data.get('student_uuid', '')
        status = data.get('status')
        if not student_uuid or not status:
            return {'error': 'student_uuid and status required'}, 400
        try:
            self.attendance_service.update_attendance(student_uuid, log_id, status)
            return {'success': True}, 200
        except ValueError as e:
            return {'error': str(e)}, 404

    def _delete_attendance(self, log_id: int, body: str = None) -> Tuple[Any, int]:
        data = _parse_body(body) if body else {}
        student_uuid = data.get('student_uuid', '')
        if not student_uuid:
            return {'error': 'student_uuid required'}, 400
        try:
            self.attendance_service.delete_attendance(student_uuid, log_id)
            return {'success': True}, 200
        except ValueError as e:
            return {'error': str(e)}, 404


def _parse_body(body: str) -> Any:
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}