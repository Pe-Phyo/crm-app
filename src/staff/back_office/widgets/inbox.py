def get_items():
    """Back office inbox: approvals, payroll reminders."""
    return [
        {'id': 1, 'type': 'approval', 'text': 'New staff: Ko Ko (pending)', 'time': 'Today', 'urgent': True, 'timely': True, 'quadrant': 1},
        {'id': 2, 'type': 'approval', 'text': 'Holiday request: Thiri (Apr 20)', 'time': 'Due soon', 'urgent': True, 'timely': False, 'quadrant': 2},
        {'id': 3, 'type': 'payment', 'text': 'Payroll due: Thiri – 500K MMK (Jul 5)', 'time': 'Jul 5', 'urgent': False, 'timely': True, 'quadrant': 3},
        {'id': 4, 'type': 'payment', 'text': 'Payroll due: Aung – 400K MMK (Jul 5)', 'time': 'Jul 5', 'urgent': False, 'timely': True, 'quadrant': 3},
        {'id': 5, 'type': 'note', 'text': 'Message from Front Office: Soe wants to reschedule', 'time': 'Today', 'urgent': False, 'timely': False, 'quadrant': 4},
    ]

def get_config():
    return {'rules': []}

def create_note(session, body):
    return {'success': True, 'id': 400}

def update_item(item_id, body):
    return {'success': True}