def get_items():
    """Dev inbox: errors from frontend/backend/AI."""
    return [
        {'id': 1, 'type': 'error', 'text': 'Backend: Failed to decrypt student DB', 'time': 'Just now', 'urgent': True, 'timely': True, 'quadrant': 1},
        {'id': 2, 'type': 'error', 'text': 'Frontend: Unhandled promise rejection', 'time': '2 min ago', 'urgent': True, 'timely': True, 'quadrant': 1},
        {'id': 3, 'type': 'info', 'text': 'AI Agent: Notification sent to Thiri', 'time': '10:06', 'urgent': False, 'timely': False, 'quadrant': 4},
    ]

def get_config():
    return {'rules': []}

def create_note(session, body):
    return {'success': True, 'id': 600}

def update_item(item_id, body):
    return {'success': True}