def get_inbox_config(role: str):
    return {
        'rules': [
            {'type': 'meeting', 'urgent_threshold_min': 30, 'timely_window_hours': 24},
            {'type': 'payment', 'urgent_days': 30, 'urgent_amount': 100000, 'timely_days': 14}
        ]
    }