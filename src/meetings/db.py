import os
import sqlite3
from typing import List, Dict, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'meetings', 'meetings.db')

def init_db():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
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
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DATABASE_PATH)

def rows_to_meetings(rows):
    meetings = []
    for row in rows:
        meetings.append({
            'id': row[0],
            'day': row[1],
            'time': row[2],
            'nickname': row[3],
            'type': row[4],
            'student_ids': row[5].split(',') if row[5] else [],
            'student_names': row[6].split(',') if row[6] else [],
            'link': row[7],
            'count': row[8],
            'rate': row[9],
            'homework': row[10] or '',
            'comments': row[11] or '',
            'attendance': row[12].split(',') if row[12] else [],
            'created': row[13],
            'updated': row[14]
        })
    return meetings

def get_meetings():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM meetings ORDER BY day, time')
    rows = c.fetchall()
    conn.close()
    return rows_to_meetings(rows)

def add_meeting(data: dict):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO meetings (
            id, day, time, nickname, type, student_ids, student_names,
            link, count, rate, homework, comments, attendance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['id'],
        data['day'],
        data['time'],
        data['nickname'],
        data['type'],
        ','.join(data.get('student_ids', [])),
        ','.join(data.get('student_names', [])),
        data['link'],
        data.get('count', 8),
        data.get('rate', 0),
        data.get('homework', ''),
        data.get('comments', ''),
        ','.join(data.get('attendance', []))
    ))
    conn.commit()
    conn.close()
    return data['id']

def update_meeting(meeting_id: str, data: dict):
    conn = get_db()
    c = conn.cursor()
    fields = []
    values = []
    for key in ['day', 'time', 'nickname', 'type', 'link', 'rate', 'homework', 'comments']:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    if 'student_ids' in data:
        fields.append("student_ids = ?")
        values.append(','.join(data['student_ids']))
    if 'student_names' in data:
        fields.append("student_names = ?")
        values.append(','.join(data['student_names']))
    if 'count' in data:
        fields.append("count = ?")
        values.append(data['count'])
    if 'attendance' in data:
        fields.append("attendance = ?")
        values.append(','.join(data['attendance']))
    if not fields:
        return
    fields.append("updated = CURRENT_TIMESTAMP")
    values.append(meeting_id)
    query = f"UPDATE meetings SET {', '.join(fields)} WHERE id = ?"
    c.execute(query, values)
    conn.commit()
    conn.close()

def delete_meeting(meeting_id: str):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
    conn.commit()
    conn.close()

def get_group_names():
    """Return a list of distinct group meeting nicknames for dropdown."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT DISTINCT nickname FROM meetings WHERE type='group' ORDER BY nickname")
    names = [row[0] for row in c.fetchall()]
    conn.close()
    return names