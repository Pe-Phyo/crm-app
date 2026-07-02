import json
from typing import Tuple, Any
from . import db

def handle(method: str, path: str, body: str = None) -> Tuple[Any, int]:
    if path == '/api/meetings':
        if method == 'GET':
            return db.get_meetings(), 200
        if method == 'POST':
            try:
                data = json.loads(body) if body else {}
                meeting_id = db.add_meeting(data)
                return {'success': True, 'id': meeting_id}, 200
            except Exception as e:
                return {'error': str(e)}, 500
    elif path.startswith('/api/meetings/'):
        meeting_id = path.split('/')[-1]
        if method == 'PUT':
            try:
                data = json.loads(body) if body else {}
                db.update_meeting(meeting_id, data)
                return {'success': True}, 200
            except Exception as e:
                return {'error': str(e)}, 500
        elif method == 'DELETE':
            try:
                db.delete_meeting(meeting_id)
                return {'success': True}, 200
            except Exception as e:
                return {'error': str(e)}, 500
    return {'error': 'Not found'}, 404