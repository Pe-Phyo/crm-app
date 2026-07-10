import os
from datetime import datetime
from typing import List, Dict, Optional

from ..students import index_db as index
from ..students import student_db as student


class AttendanceService:
    def __init__(self, data_dir: str, master_key: bytes, root_data_dir: str = None):
        self.data_dir = data_dir
        self.master_key = master_key
        self.root_data_dir = root_data_dir if root_data_dir else data_dir

    def _open_student_conn(self, uuid: str):
        """Open the student's encrypted database connection."""
        conn = index.open_index_db_with_key(self.data_dir, self.master_key)
        try:
            key = index.get_student_db_key(conn, uuid)
        finally:
            index.close_index_db(conn)
        if not key:
            raise ValueError(f"Student {uuid} not found")
        student_db_dir = os.path.join(self.data_dir, 'students')
        return student.open_student_db(student_db_dir, uuid, key)

    def get_attendance(self, student_uuid: str) -> List[Dict]:
        """Return all attendance records for a student."""
        sconn = self._open_student_conn(student_uuid)
        try:
            return student.get_attendance(sconn)
        finally:
            sconn.close()

    def add_attendance(self, student_uuid: str, meeting_id: str = '', date: str = '', status: str = 'absent') -> int:
        """Mark attendance for a student. Returns the new record ID."""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        sconn = self._open_student_conn(student_uuid)
        try:
            log_id = student.add_attendance(sconn, meeting_id, date, status)
            # Update attendance percentage in index
            pct = student.get_attendance_percentage(sconn)
            conn = index.open_index_db_with_key(self.data_dir, self.master_key)
            try:
                index.update_student_summary(conn, student_uuid, attendance_percentage=pct)
            finally:
                index.close_index_db(conn)
            sconn.commit()
            return log_id
        finally:
            sconn.close()

    def update_attendance(self, student_uuid: str, log_id: int, status: str):
        """Change the status of an existing attendance record."""
        sconn = self._open_student_conn(student_uuid)
        try:
            student.update_attendance(sconn, log_id, status)
            pct = student.get_attendance_percentage(sconn)
            conn = index.open_index_db_with_key(self.data_dir, self.master_key)
            try:
                index.update_student_summary(conn, student_uuid, attendance_percentage=pct)
            finally:
                index.close_index_db(conn)
            sconn.commit()
        finally:
            sconn.close()

    def delete_attendance(self, student_uuid: str, log_id: int):
        """Delete an attendance record."""
        sconn = self._open_student_conn(student_uuid)
        try:
            student.delete_attendance(sconn, log_id)
            pct = student.get_attendance_percentage(sconn)
            conn = index.open_index_db_with_key(self.data_dir, self.master_key)
            try:
                index.update_student_summary(conn, student_uuid, attendance_percentage=pct)
            finally:
                index.close_index_db(conn)
            sconn.commit()
        finally:
            sconn.close()