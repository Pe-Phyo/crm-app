import os
from typing import List, Dict
from datetime import datetime

from ...students import index_db as index
from ...students import student_db as student


class PaymentsService:
    def __init__(self, data_dir: str, master_key: bytes):
        self.data_dir = data_dir
        self.master_key = master_key

    def _open_student_conn(self, uuid: str):
        conn = index.open_index_db_with_key(self.data_dir, self.master_key)
        try:
            key = index.get_student_db_key(conn, uuid)
        finally:
            index.close_index_db(conn)
        if not key:
            raise ValueError(f"Student {uuid} not found")
        student_db_dir = os.path.join(self.data_dir, 'students')
        return student.open_student_db(student_db_dir, uuid, key)

    def get_payments(self, student_uuid: str) -> List[Dict]:
        sconn = self._open_student_conn(student_uuid)
        try:
            return student.get_payments(sconn)
        finally:
            sconn.close()

    def add_payment(self, student_uuid: str, amount: int, date: str = '', receipt_image: bytes = None) -> int:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        sconn = self._open_student_conn(student_uuid)
        try:
            pid = student.add_payment(sconn, date, amount, receipt_image)
            # Update last_payment_date in index
            conn = index.open_index_db_with_key(self.data_dir, self.master_key)
            try:
                index.update_student_summary(conn, student_uuid, last_payment_date=date)
            finally:
                index.close_index_db(conn)
            sconn.commit()
            return pid
        finally:
            sconn.close()

    def delete_payment(self, student_uuid: str, payment_id: int):
        sconn = self._open_student_conn(student_uuid)
        try:
            student.delete_payment(sconn, payment_id)
            sconn.commit()
        finally:
            sconn.close()