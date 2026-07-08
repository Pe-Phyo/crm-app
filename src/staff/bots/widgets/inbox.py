def get_items():
    """Bot activity log (placeholder)."""
    return [
        {'id': 1, 'type': 'error', 'text': 'Failed to send to Soe: no phone number', 'time': 'Just now', 'urgent': True, 'timely': True, 'quadrant': 1},
        {'id': 2, 'type': 'info', 'text': 'Reminder sent to Thiri (lesson at 10:30)', 'time': '10:05', 'urgent': False, 'timely': False, 'quadrant': 4},
    ]

def get_config():
    return {'rules': []}

def create_note(session, body):
    return {'success': True, 'id': 500}

def update_item(item_id, body):
    return {'success': True}