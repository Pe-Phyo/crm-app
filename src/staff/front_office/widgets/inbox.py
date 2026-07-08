def get_items():
    """Reception list for today."""
    return [
        {'id': 1, 'type': 'meeting', 'text': '10:00 – Thiri', 'time': 'Arrived ✓', 'quadrant': 3},
        {'id': 2, 'type': 'meeting', 'text': '2:00 – Alex', 'time': 'Not arrived', 'quadrant': 3},
        {'id': 3, 'type': 'meeting', 'text': '4:30 – Maria', 'time': 'Arrived ✓', 'quadrant': 3},
    ]

def get_config():
    return {'rules': []}

def create_note(session, body):
    return {'success': True, 'id': 300}

def update_item(item_id, body):
    return {'success': True}