import json
from urllib.parse import parse_qs
from typing import Tuple, Any

from .payments.service import PaymentsService
from ..staff import auth as staff_auth
from ..students import auth as student_auth


class FrontOfficeCoordinator:
    def __init__(self, data_dir: str, master_key: bytes, root_data_dir: str = None):
        self.data_dir = data_dir
        self.master_key = master_key
        self.root_data_dir = root_data_dir if root_data_dir else data_dir
        self.payments_service = PaymentsService(data_dir, master_key)

    def handle(self, method: str, path: str, body: str = None, headers: dict = None,
               query: str = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        if not student_auth.verify_token(token) and not staff_auth.verify_session(token):
            return {'error': 'Unauthorized'}, 401

        # Payments endpoints (path will be /frontoffice/payments)
        if path == '/frontoffice/payments' and method == 'GET':
            return self._get_payments(query)
        if path == '/frontoffice/payments' and method == 'POST':
            return self._add_payment(body)
        if path.startswith('/frontoffice/payments/') and method == 'DELETE':
            parts = path.split('/')
            if len(parts) == 4 and parts[3].isdigit():
                payment_id = int(parts[3])
                return self._delete_payment(payment_id, body)
        return {'error': 'Not found'}, 404

    def _get_payments(self, query: str = None):
        params = parse_qs(query) if query else {}
        student_uuid = params.get('student_uuid', [None])[0]
        if not student_uuid:
            return {'error': 'student_uuid required'}, 400
        try:
            records = self.payments_service.get_payments(student_uuid)
            return records, 200
        except ValueError as e:
            return {'error': str(e)}, 404

    def _add_payment(self, body: str):
        data = _parse_body(body)
        student_uuid = data.get('student_uuid', '')
        amount = data.get('amount', 0)
        date = data.get('date', '')
        if not student_uuid or not amount:
            return {'error': 'student_uuid and amount required'}, 400
        try:
            pid = self.payments_service.add_payment(student_uuid, amount, date)
            return {'id': pid}, 201
        except ValueError as e:
            return {'error': str(e)}, 404

    def _delete_payment(self, payment_id: int, body: str = None):
        data = _parse_body(body) if body else {}
        student_uuid = data.get('student_uuid', '')
        if not student_uuid:
            return {'error': 'student_uuid required'}, 400
        try:
            self.payments_service.delete_payment(student_uuid, payment_id)
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