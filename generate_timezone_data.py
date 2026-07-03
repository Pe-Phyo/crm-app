import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

locations = []
for tz_name in sorted(available_timezones()):
    try:
        now = datetime.now(ZoneInfo(tz_name))
        offset_seconds = now.utcoffset().total_seconds()
        hours = int(offset_seconds // 3600)
        minutes = abs(int(offset_seconds % 3600 // 60))
        sign = '+' if hours >= 0 else '-'
        if minutes:
            offset_str = f"GMT{sign}{abs(hours)}:{minutes:02d}"
        else:
            offset_str = f"GMT{sign}{abs(hours)}"
        label = f"{tz_name} ({offset_str})"
        locations.append({"label": label, "value": offset_str})
    except Exception:
        continue

output = {"locations": locations}
os.makedirs('data/utils', exist_ok=True)
with open('data/utils/timezone_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Generated {len(locations)} timezone entries.")