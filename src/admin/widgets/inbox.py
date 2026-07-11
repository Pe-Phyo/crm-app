from datetime import datetime, timedelta

def get_items():
    """Admin inbox items with Eisenhower quadrant data (placeholder)."""
    now = datetime.utcnow()
    return [
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

def get_config():
    """Heuristics config for admin inbox."""
    return {
        'rules': [
            {'type': 'meeting', 'urgent_threshold_min': 30, 'timely_window_hours': 24},
            {'type': 'payment', 'urgent_days': 30, 'urgent_amount': 100000, 'timely_days': 14}
        ]
    }

def create_note(session, body):
    """Stub: create a new note."""
    import json
    data = json.loads(body or '{}')
    # TODO: store in DB
    return {'success': True, 'id': 100}

def update_item(item_id, body):
    """Stub: update an inbox item."""
    return {'success': True}