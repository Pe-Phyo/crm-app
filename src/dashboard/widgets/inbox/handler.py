from datetime import datetime, timedelta

def get_inbox_items(role: str):
    now = datetime.utcnow()
    items = [
        {'id': 1, 'type': 'meeting', 'text': 'Lesson with Thiri', 'time': '10:00 AM (in 20 min)', 'urgent': True, 'timely': True, 'quadrant': 1, 'timestamp': now.isoformat()},
        {'id': 2, 'type': 'error', 'text': 'Failed to decrypt student DB', 'time': 'Just now', 'urgent': True, 'timely': True, 'quadrant': 1, 'timestamp': now.isoformat()},
        {'id': 3, 'type': 'payment', 'text': 'Aung overdue 45 days – 120,000 MMK', 'time': 'Due 15 May', 'urgent': True, 'timely': False, 'quadrant': 2, 'timestamp': now.isoformat()},
        {'id': 4, 'type': 'action', 'text': 'Prepare progress report (high, due today)', 'time': 'Due today', 'urgent': True, 'timely': True, 'quadrant': 1, 'timestamp': now.isoformat()},
        {'id': 5, 'type': 'meeting', 'text': 'Lesson with Alex', 'time': '2:00 PM', 'urgent': False, 'timely': True, 'quadrant': 3, 'timestamp': now.isoformat()},
        {'id': 6, 'type': 'payment', 'text': 'Soe overdue 5 days – 30,000 MMK', 'time': 'Due 30 Jun', 'urgent': False, 'timely': True, 'quadrant': 3, 'timestamp': now.isoformat()},
        {'id': 7, 'type': 'birthday', 'text': 'Alex birthday in 3 days', 'time': '', 'urgent': False, 'timely': True, 'quadrant': 3, 'timestamp': now.isoformat()},
        {'id': 8, 'type': 'note', 'text': 'Check curriculum update', 'time': 'Yesterday', 'urgent': False, 'timely': False, 'quadrant': 4, 'timestamp': (now - timedelta(days=1)).isoformat()},
        {'id': 9, 'type': 'payment', 'text': 'Nu Nu overdue 20 days – 50,000 MMK', 'time': 'Due 15 Jun', 'urgent': False, 'timely': False, 'quadrant': 4, 'timestamp': now.isoformat()},
    ]
    return items

def create_note(session: dict, body: str):
    import json
    data = json.loads(body or '{}')
    # TODO: store in DB
    return {'success': True, 'id': 100}

def update_inbox_item(item_id: int, body: str):
    # TODO: update in DB
    return {'success': True}