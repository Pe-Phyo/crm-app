import json
import os
from datetime import date, timedelta

def country_flag(code: str) -> str:
    if len(code) != 2:
        return ''
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))
    
def get_upcoming_events(days_ahead: int = 14):
    project_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
    )
    holidays_path = os.path.join(project_root, 'data', 'utils','holidays.json')
    print(f"🔍 Looking for holidays at: {holidays_path}")

    try:
        with open(holidays_path, 'r', encoding='utf-8') as f:
            all_holidays = json.load(f)
        print(f"✅ Loaded JSON with {len(all_holidays)} country entries")
    except FileNotFoundError:
        print("❌ File not found!")
        return {'events': []}

    today = date.today()
    cutoff = today + timedelta(days=days_ahead)
    print(f"📅 Today: {today}, Cutoff: {cutoff}")
    events = []

    for country_code, categories in all_holidays.items():
        if country_code == 'meta':
            continue
        for cat_name, ev_list in categories.items():
            for ev in ev_list:
                ev_date = date.fromisoformat(ev['start'])
                if today <= ev_date <= cutoff:
                    print(f"  ➕ Adding: {ev['name']} ({country_code}, {cat_name}) on {ev_date}")
                    events.append({
                        'name': ev['name'],
                        'date': ev['start'],
                        'type': cat_name,
                        'country_code': country_code,
                        'flag': country_flag(country_code),
                        'end': ev.get('end'),
                        'notes': ev.get('notes', '')
                    })

    print(f"📊 Total events in range: {len(events)}")
    return {'events': events}