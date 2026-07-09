import json
import uuid
import os
from datetime import datetime
from typing import Tuple, Any

from . import auth as auth_module
from . import index_db as index
from . import student_db as student
from ..staff import auth as staff_auth
from ..meetings.db import add_meeting as add_meeting_db   # NEW import

# ------------------------------------------------------------
class StudentCoordinator:
    def __init__(self, data_dir: str, master_key: bytes = None, root_data_dir: str = None):
        self.data_dir = data_dir
        self.master_key = master_key
        self.root_data_dir = root_data_dir if root_data_dir else data_dir

    def handle(self, method: str, path: str, body: str = None, headers: dict = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        # Accept either student token (legacy) or staff token
        if not auth_module.verify_token(token) and not staff_auth.verify_session(token):
            return {'error': 'Unauthorized'}, 401
        # Routes without auth
        if path == '/auth/status' and method == 'GET':
            return self._status()
        if path == '/auth/setup' and method == 'POST':
            return self._setup(body)
        if path == '/auth/login' and method == 'POST':
            return self._login(body)

        # Open index DB
        try:
            conn = index.open_index_db_with_key(self.data_dir, self.master_key)
        except Exception as e:
            return {'error': f'Cannot open index: {str(e)}'}, 500

        try:
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
                elif len(parts) == 4 and parts[3] == 'attendance':
                    if method == 'GET':
                        return self._get_attendance(conn, student_uuid)
                    if method == 'POST':
                        return self._add_attendance(conn, student_uuid, body)
                elif len(parts) == 5 and parts[3] == 'attendance':
                    log_id = int(parts[4])
                    if method == 'PUT':
                        return self._update_attendance(conn, student_uuid, log_id, body)
                    if method == 'DELETE':
                        return self._delete_attendance(conn, student_uuid, log_id)
                elif len(parts) == 4 and parts[3] == 'payments':
                    if method == 'GET':
                        return self._get_payments(conn, student_uuid)
                    if method == 'POST':
                        return self._add_payment(conn, student_uuid, body)
            if path == '/actions' and method == 'GET':
                return self._list_actions(conn)
            if path == '/actions' and method == 'POST':
                return self._add_action(conn, body)
            if path.startswith('/actions/'):
                parts = path.split('/')
                action_id = int(parts[2])
                if method == 'PUT':
                    return self._update_action(conn, action_id, body)
                if method == 'DELETE':
                    return self._delete_action(conn, action_id)
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

    # ---- Student CRUD ----
    def _list_students(self, conn) -> Tuple[Any, int]:
        students = index.get_all_students(conn)
        if students:
            print("DEBUG first student timezone:", students[0].get('timezone'))
        else:
            print("DEBUG no students")
        return students, 200

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
            'rate': data.get('rate', 0),
            'birthdate': data.get('birthdate', ''),
            'teacher_id': data.get('teacher_id', '')
        }

        meeting_times = data.get('meeting_times', [])
        summary = ', '.join([f"{mt['day'][:3]} {mt['time']} ({'Group' if mt.get('type')=='group' else 'Private'})" for mt in meeting_times])

        # ---- Compute flag (use label if available, otherwise fall back to offset) ----
        tz_label = data.get('timezone_label', '')
        if tz_label:
            student_flag = index.get_flag_for_timezone_label(self.root_data_dir, tz_label)
        else:
            student_flag = index.get_flag_for_timezone(self.root_data_dir, data.get('timezone', ''))

        # Index entry
        index.add_student_summary(
            conn,
            uuid=new_uuid,
            name=profile['name'],
            location='',
            timezone=profile['timezone'], 
            rate=profile['rate'],
            last_payment_date='',
            attendance_percentage=0.0,
            meeting_times_summary=summary,
            status='active',
            db_key=key,
            flag=student_flag
        )

        # Per‑student DB population
        student_conn = student.open_student_db(student_db_dir, new_uuid, key)
        try:
            student.save_profile(student_conn, profile)
            student.set_phones(student_conn, data.get('phones', []))
            student.set_emails(student_conn, data.get('emails', []))
            student.set_parent_phones(student_conn, data.get('parent_phones', []))
            student.set_parent_emails(student_conn, data.get('parent_emails', []))
            student.set_relationships(student_conn, data.get('linked_students', []))
            for mt in meeting_times:
                mid = uuid.uuid4().hex
                mt['meeting_id'] = mid
                student.add_meeting_time(
                    student_conn,
                    name=mt.get('name', 'Unnamed'),
                    day=mt.get('day', 'Monday'),
                    time=mt.get('time', '09:00'),
                    mtype=mt.get('type', 'private'),
                    is_in_person=mt.get('is_in_person', False),
                    meeting_id=mid
                )
            student_conn.commit()
        finally:
            student_conn.close()

        # ---- Create meeting entries in the shared meetings DB ----
        from ..meetings.db import add_meeting as add_meeting_db, get_db, update_meeting
        student_name = data.get('name', '')
        teacher_id = data.get('teacher_id', '')

        private_times = [mt for mt in meeting_times if mt.get('type') != 'group']
        group_times = [mt for mt in meeting_times if mt.get('type') == 'group']

        # Private meetings: each slot gets its own ID, but all share a package_id
        if private_times:
            package_id = uuid.uuid4().hex
            for mt in private_times:
                slot_id = uuid.uuid4().hex
                try:
                    add_meeting_db({
                        'id': slot_id,
                        'day': mt.get('day', 'Monday'),
                        'time': mt.get('time', '09:00'),
                        'nickname': f"{student_name} (Private)",
                        'type': 'private',
                        'student_ids': [new_uuid],
                        'student_names': [student_name],
                        'link': mt.get('link', ''),
                        'count': 1,
                        'rate': profile['rate'],
                        'homework': '',
                        'comments': '',
                        'attendance': [],
                        'teacher_id': teacher_id,
                        'package_id': package_id
                    })
                    mt['meeting_id'] = slot_id
                except Exception as e:
                    print(f"Warning: could not create private meeting: {e}")

        # Group meetings: reuse existing group or create new
        for mt in group_times:
            group_meeting_id = mt.get('meeting_id')
            group_name = mt.get('name', 'Unnamed')
            if group_meeting_id:
                # Existing group: add student to it
                conn_meetings = get_db()
                c = conn_meetings.cursor()
                c.execute("SELECT student_ids, student_names, count FROM meetings WHERE id=?", (group_meeting_id,))
                row = c.fetchone()
                conn_meetings.close()
                if row:
                    existing_ids = row[0].split(',') if row[0] else []
                    existing_names = row[1].split(',') if row[1] else []
                    if len(existing_ids) >= 9:
                        print(f"Warning: group '{group_name}' is full (9 seats). Student not added.")
                        continue
                    existing_ids.append(new_uuid)
                    existing_names.append(student_name)
                    new_count = len(existing_ids)
                    update_meeting(group_meeting_id, {
                        'student_ids': existing_ids,
                        'student_names': existing_names,
                        'count': new_count
                    })
                else:
                    group_meeting_id = uuid.uuid4().hex
                    add_meeting_db({
                        'id': group_meeting_id,
                        'day': mt.get('day', 'Monday'),
                        'time': mt.get('time', '09:00'),
                        'nickname': group_name,
                        'type': 'group',
                        'student_ids': [new_uuid],
                        'student_names': [student_name],
                        'link': mt.get('link', ''),
                        'count': 1,
                        'rate': profile['rate'],
                        'homework': '',
                        'comments': '',
                        'attendance': [],
                        'teacher_id': teacher_id
                    })
            else:
                group_meeting_id = uuid.uuid4().hex
                add_meeting_db({
                    'id': group_meeting_id,
                    'day': mt.get('day', 'Monday'),
                    'time': mt.get('time', '09:00'),
                    'nickname': group_name,
                    'type': 'group',
                    'student_ids': [new_uuid],
                    'student_names': [student_name],
                    'link': mt.get('link', ''),
                    'count': 1,
                    'rate': profile['rate'],
                    'homework': '',
                    'comments': '',
                    'attendance': [],
                    'teacher_id': teacher_id
                })
            mt['meeting_id'] = group_meeting_id

        # Reopen student DB and insert meeting times with real meeting IDs
        student_conn = student.open_student_db(student_db_dir, new_uuid, key)
        try:
            for mt in meeting_times:
                student.add_meeting_time(
                    student_conn,
                    name=mt.get('name', 'Unnamed'),
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
        key = index.get_student_db_key(conn, uuid)
        if not key:
            return {'error': 'Student not found'}, 404
        student_db_dir = os.path.join(self.data_dir, 'students')
        student_conn = student.open_student_db(student_db_dir, uuid, key)
        try:
            profile = student.get_profile(student_conn)
            profile['phones'] = student.get_phones(student_conn)
            profile['emails'] = student.get_emails(student_conn)
            profile['parent_phones'] = student.get_parent_phones(student_conn)
            profile['parent_emails'] = student.get_parent_emails(student_conn)
            profile['relationships'] = student.get_relationships(student_conn)
            profile['meeting_times'] = student.get_meeting_times(student_conn)
            profile['attendance'] = student.get_attendance(student_conn)
            profile['payments'] = student.get_payments(student_conn)
            profile['homework_reading'] = student.get_homework_reading(student_conn)
            profile['attendance_percentage'] = student.get_attendance_percentage(student_conn)
            profile['meeting_times_summary'] = student.get_meeting_times_summary(student_conn)
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
            profile = student.get_profile(student_conn)
            # Update scalar fields
            allowed = ['name', 'timezone', 'age_group', 'academic_year', 'telegram',
                       'parent_name', 'school_name', 'educational_goals', 'general_comments', 'rate',
                       'is_minor', 'birthdate', 'teacher_id']
            for field in allowed:
                if field in data:
                    profile[field] = data[field]
            student.save_profile(student_conn, profile)

            if 'phones' in data:
                student.set_phones(student_conn, data['phones'])
            if 'emails' in data:
                student.set_emails(student_conn, data['emails'])
            if 'parent_phones' in data:
                student.set_parent_phones(student_conn, data['parent_phones'])
            if 'parent_emails' in data:
                student.set_parent_emails(student_conn, data['parent_emails'])
            if 'linked_students' in data:
                student.set_relationships(student_conn, data['linked_students'])
            # Update flag if timezone changed (use label if sent)
            if 'timezone' in data:
                tz_label = data.get('timezone_label', '')
                if tz_label:
                    new_flag = index.get_flag_for_timezone_label(self.root_data_dir, tz_label)
                else:
                    new_flag = index.get_flag_for_timezone(self.root_data_dir, data['timezone'])
                index.update_student_summary(conn, uuid, timezone=data['timezone'], flag=new_flag)
            if 'meeting_times' in data:
                student_conn.execute("DELETE FROM meeting_times")
                for mt in data['meeting_times']:
                    student.add_meeting_time(
                        student_conn,
                        name=mt.get('name', 'Unnamed'),
                        day=mt.get('day', 'Monday'),
                        time=mt.get('time', '09:00'),
                        mtype=mt.get('type', 'private'),
                        is_in_person=mt.get('is_in_person', False),
                        meeting_id=mt.get('meeting_id')
                    )
                summary = student.get_meeting_times_summary(student_conn)
                index.update_student_summary(conn, uuid, meeting_times_summary=summary)

            if 'rate' in data:
                index.update_student_summary(conn, uuid, rate=data['rate'])
            if 'name' in data:
                index.update_student_summary(conn, uuid, name=data['name'])

            student_conn.commit()
        finally:
            student_conn.close()
        return {'success': True}, 200

    def _delete_student(self, conn, uuid: str, body: str = None) -> Tuple[Any, int]:
        data = _parse_body(body)
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

    # ---- Attendance, Payments, Actions (unchanged) ----
    def _get_attendance(self, conn, uuid):
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        sconn = student.open_student_db(os.path.join(self.data_dir, 'students'), uuid, key)
        try:
            return student.get_attendance(sconn), 200
        finally:
            sconn.close()

    def _add_attendance(self, conn, uuid, body):
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        data = _parse_body(body)
        meeting_id = data.get('meeting_id', '')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        status = data.get('status', 'absent')
        sconn = student.open_student_db(os.path.join(self.data_dir, 'students'), uuid, key)
        try:
            log_id = student.add_attendance(sconn, meeting_id, date, status)
            pct = student.get_attendance_percentage(sconn)
            index.update_student_summary(conn, uuid, attendance_percentage=pct)
            sconn.commit()
            return {'id': log_id}, 201
        finally:
            sconn.close()

    def _update_attendance(self, conn, uuid, log_id, body):
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        data = _parse_body(body)
        status = data.get('status')
        if not status: return {'error': 'status required'}, 400
        sconn = student.open_student_db(os.path.join(self.data_dir, 'students'), uuid, key)
        try:
            student.update_attendance(sconn, log_id, status)
            pct = student.get_attendance_percentage(sconn)
            index.update_student_summary(conn, uuid, attendance_percentage=pct)
            sconn.commit()
            return {'success': True}, 200
        finally:
            sconn.close()

    def _delete_attendance(self, conn, uuid, log_id):
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        sconn = student.open_student_db(os.path.join(self.data_dir, 'students'), uuid, key)
        try:
            student.delete_attendance(sconn, log_id)
            pct = student.get_attendance_percentage(sconn)
            index.update_student_summary(conn, uuid, attendance_percentage=pct)
            sconn.commit()
            return {'success': True}, 200
        finally:
            sconn.close()

    def _get_payments(self, conn, uuid):
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        sconn = student.open_student_db(os.path.join(self.data_dir, 'students'), uuid, key)
        try:
            return student.get_payments(sconn), 200
        finally:
            sconn.close()

    def _add_payment(self, conn, uuid, body):
        key = index.get_student_db_key(conn, uuid)
        if not key: return {'error': 'Student not found'}, 404
        data = _parse_body(body)
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        amount = data.get('amount', 0)
        sconn = student.open_student_db(os.path.join(self.data_dir, 'students'), uuid, key)
        try:
            pid = student.add_payment(sconn, date, amount, None)
            index.update_student_summary(conn, uuid, last_payment_date=date)
            sconn.commit()
            return {'id': pid}, 201
        finally:
            sconn.close()

    # ---- Actions ----
    def _list_actions(self, conn):
        return index.get_action_items(conn), 200

    def _add_action(self, conn, body):
        data = _parse_body(body)
        text = data.get('text', '')
        if not text: return {'error': 'text required'}, 400
        id = index.add_action_item(conn, text)
        return {'id': id}, 201

    def _update_action(self, conn, action_id, body):
        data = _parse_body(body)
        index.update_action_item(conn, action_id, text=data.get('text'), done=data.get('done'))
        return {'success': True}, 200

    def _delete_action(self, conn, action_id):
        index.delete_action_item(conn, action_id)
        return {'success': True}, 200

def _parse_body(body: str) -> Any:
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}