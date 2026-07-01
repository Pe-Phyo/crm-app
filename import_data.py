#!/usr/bin/env python3
import json
import sqlite3
import os
import sys

# Path to your meetings database
MEETINGS_DB = './data/meetings/meetings.db'

# Your JSON data from localStorage (paste it below)
DATA_JSON = '''
{
  "meetings": [
    {
      "id": "m1",
      "day": "Monday",
      "time": "09:00",
      "nickname": "Math Group A",
      "type": "group",
      "students": ["John Doe", "Alice Smith", "Bob Johnson"],
      "link": "https://meet.jit.si/math_a",
      "count": 8,
      "rate": 25000,
      "homework": "Complete chapter 3",
      "comments": "Focus on word problems",
      "attendance": ["John Doe", "Alice Smith"]
    }
  ]
}
'''

def main():
    # Ensure the meetings directory exists
    os.makedirs(os.path.dirname(MEETINGS_DB), exist_ok=True)

    # Load the data
    data = json.loads(DATA_JSON)

    # Connect to the database
    conn = sqlite3.connect(MEETINGS_DB)
    c = conn.cursor()

    # Create the table
    c.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            nickname TEXT NOT NULL,
            type TEXT NOT NULL,
            student_ids TEXT NOT NULL,
            student_names TEXT NOT NULL,
            link TEXT NOT NULL,
            count INTEGER DEFAULT 8,
            rate INTEGER DEFAULT 0,
            homework TEXT DEFAULT '',
            comments TEXT DEFAULT '',
            attendance TEXT DEFAULT '',
            created TEXT DEFAULT CURRENT_TIMESTAMP,
            updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert each meeting
    for meeting in data.get('meetings', []):
        # Generate student IDs (filename references)
        student_ids = []
        student_names = meeting.get('students', [])
        for _ in student_names:
            student_ids.append('stu_' + str(int(time.time())) + '_' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6)))
            time.sleep(0.001)  # Ensure unique timestamps

        c.execute('''
            INSERT OR REPLACE INTO meetings (
                id, day, time, nickname, type, student_ids, student_names,
                link, count, rate, homework, comments, attendance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            meeting.get('id', 'm_' + str(int(time.time()))),
            meeting.get('day', 'Monday'),
            meeting.get('time', '09:00'),
            meeting.get('nickname', 'Class'),
            meeting.get('type', 'group'),
            ','.join(student_ids),
            ','.join(student_names),
            meeting.get('link', 'https://meet.jit.si/room'),
            meeting.get('count', 8),
            meeting.get('rate', 0),
            meeting.get('homework', ''),
            meeting.get('comments', ''),
            ','.join(meeting.get('attendance', []))
        ))

    conn.commit()
    conn.close()
    print(f"Imported {len(data.get('meetings', []))} meetings to {MEETINGS_DB}")

if __name__ == '__main__':
    import time
    import random
    main()