def get_items():
    """Teacher inbox: my action items only (placeholder)."""
    return [
        {'id': 1, 'type': 'action', 'text': 'Prepare progress report Maria (high, due today)', 'time': 'Due today', 'urgent': True, 'timely': True, 'quadrant': 1},
        {'id': 2, 'type': 'action', 'text': 'Send homework Aung (due tomorrow)', 'time': 'Due tomorrow', 'urgent': False, 'timely': True, 'quadrant': 3},
        {'id': 3, 'type': 'note', 'text': 'Print lesson materials', 'time': 'Today', 'urgent': False, 'timely': False, 'quadrant': 4},
    ]

def get_config():
    return {'rules': []}  # teacher-specific heuristics later

def create_note(session, body):
    return {'success': True, 'id': 200}

def update_item(item_id, body):
    return {'success': True}