import os
import json
from typing import List, Optional, Dict
from datetime import datetime

from .crypto import create_encrypted_db, open_encrypted_db, generate_key

# ------------------------------------------------------------
# Create / Open
# ------------------------------------------------------------
def create_student_db(data_dir: str, uuid: str) -> (bytes):
    """
    Create a new encrypted student DB. Returns the random key (so it can be stored in index).
    """
    os.makedirs(data_dir, exist_ok=True)
    key = generate_key()
    db_path = os.path.join(data_dir, f"{uuid}.sqlite")
    conn = create_encrypted_db(db_path, key)
    _create_tables(conn)
    conn.commit()
    conn.close()
    return key

def open_student_db(data_dir: str, uuid: str, key: bytes):
    """Open an existing student DB with the given key."""
    db_path = os.path.join(data_dir, f"{uuid}.sqlite")
    conn = open_encrypted_db(db_path, key)
    return conn

# ------------------------------------------------------------
# Table creation
# ------------------------------------------------------------
def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS profile (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT DEFAULT '',
            timezone TEXT DEFAULT '',
            age_group TEXT DEFAULT '',
            academic_year TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            telegram TEXT DEFAULT '',
            email TEXT DEFAULT '',
            is_minor INTEGER DEFAULT 0,
            parent_name TEXT DEFAULT '',
            parent_phone TEXT DEFAULT '',
            educational_goals TEXT DEFAULT '',
            behavioral_comments TEXT DEFAULT '',
            general_comments TEXT DEFAULT '',
            rate INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS meeting_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            type TEXT NOT NULL,
            is_in_person INTEGER DEFAULT 0,
            meeting_id TEXT
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT,
            date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'absent'
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount INTEGER NOT NULL,
            receipt_image BLOB
        );
        CREATE TABLE IF NOT EXISTS homework_reading (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_type TEXT NOT NULL,  -- 'homework' or 'reading'
            content TEXT NOT NULL,
            date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            salt BLOB,
            hash BLOB,
            date TEXT NOT NULL
        );
    """)

# ------------------------------------------------------------
# Profile CRUD
# ------------------------------------------------------------
def get_profile(conn) -> Dict:
    cursor = conn.execute("SELECT * FROM profile LIMIT 1")
    row = cursor.fetchone()
    if row is None:
        return {}
    return {
        'uuid': row[0],
        'name': row[1],
        'location': row[2],
        'timezone': row[3],
        'age_group': row[4],
        'academic_year': row[5],
        'phone': row[6],
        'telegram': row[7],
        'email': row[8],
        'is_minor': bool(row[9]),
        'parent_name': row[10],
        'parent_phone': row[11],
        'educational_goals': row[12],
        'behavioral_comments': row[13],
        'general_comments': row[14],
        'rate': row[15]
    }

def save_profile(conn, profile: Dict):
    # Insert or replace
    conn.execute("""
        INSERT OR REPLACE INTO profile (
            uuid, name, location, timezone, age_group, academic_year,
            phone, telegram, email, is_minor, parent_name, parent_phone,
            educational_goals, behavioral_comments, general_comments, rate
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        profile['uuid'],
        profile.get('name', ''),
        profile.get('location', ''),
        profile.get('timezone', ''),
        profile.get('age_group', ''),
        profile.get('academic_year', ''),
        profile.get('phone', ''),
        profile.get('telegram', ''),
        profile.get('email', ''),
        1 if profile.get('is_minor') else 0,
        profile.get('parent_name', ''),
        profile.get('parent_phone', ''),
        profile.get('educational_goals', ''),
        profile.get('behavioral_comments', ''),
        profile.get('general_comments', ''),
        profile.get('rate', 0)
    ))
    conn.commit()

# ------------------------------------------------------------
# Meeting times (custom slots)
# ------------------------------------------------------------
def get_meeting_times(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, day, time, type, is_in_person, meeting_id FROM meeting_times ORDER BY id")
    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'day': row[1],
            'time': row[2],
            'type': row[3],
            'is_in_person': bool(row[4]),
            'meeting_id': row[5]
        })
    return items

def add_meeting_time(conn, day: str, time: str, mtype: str, is_in_person: bool, meeting_id: str = None) -> int:
    cursor = conn.execute(
        "INSERT INTO meeting_times (day, time, type, is_in_person, meeting_id) VALUES (?,?,?,?,?)",
        (day, time, mtype, 1 if is_in_person else 0, meeting_id)
    )
    conn.commit()
    return cursor.lastrowid

def delete_meeting_time(conn, slot_id: int):
    conn.execute("DELETE FROM meeting_times WHERE id=?", (slot_id,))
    conn.commit()

def get_meeting_times_summary(conn) -> str:
    """Returns a human‑readable summary like 'Mon 9am (Group), Wed 3pm (Private)'."""
    items = get_meeting_times(conn)
    summaries = []
    for item in items:
        summaries.append(f"{item['day'][:3]} {item['time']} ({'Group' if item['type']=='group' else 'Private'})")
    return ', '.join(summaries)

# ------------------------------------------------------------
# Attendance
# ------------------------------------------------------------
def get_attendance(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, meeting_id, date, status FROM attendance ORDER BY date DESC")
    rows = cursor.fetchall()
    log = []
    for row in rows:
        log.append({'id': row[0], 'meeting_id': row[1], 'date': row[2], 'status': row[3]})
    return log

def add_attendance(conn, meeting_id: str, date: str, status: str = 'absent') -> int:
    cursor = conn.execute(
        "INSERT INTO attendance (meeting_id, date, status) VALUES (?,?,?)",
        (meeting_id, date, status)
    )
    conn.commit()
    return cursor.lastrowid

def update_attendance(conn, log_id: int, status: str):
    conn.execute("UPDATE attendance SET status=? WHERE id=?", (status, log_id))
    conn.commit()

def delete_attendance(conn, log_id: int):
    conn.execute("DELETE FROM attendance WHERE id=?", (log_id,))
    conn.commit()

def get_attendance_percentage(conn) -> float:
    """Calculate present/(total) percentage from attendance log."""
    cursor = conn.execute("SELECT COUNT(*), SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) FROM attendance")
    total, present = cursor.fetchone()
    if total == 0:
        return 0.0
    return (present / total) * 100.0

# ------------------------------------------------------------
# Payments
# ------------------------------------------------------------
def get_payments(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, date, amount, receipt_image FROM payments ORDER BY date DESC")
    rows = cursor.fetchall()
    payments = []
    for row in rows:
        payments.append({
            'id': row[0],
            'date': row[1],
            'amount': row[2],
            'receipt_image': row[3]  # bytes, or None
        })
    return payments

def add_payment(conn, date: str, amount: int, receipt_image: bytes = None) -> int:
    cursor = conn.execute(
        "INSERT INTO payments (date, amount, receipt_image) VALUES (?,?,?)",
        (date, amount, receipt_image)
    )
    conn.commit()
    return cursor.lastrowid

def delete_payment(conn, payment_id: int):
    conn.execute("DELETE FROM payments WHERE id=?", (payment_id,))
    conn.commit()

# ------------------------------------------------------------
# Homework / Reading
# ------------------------------------------------------------
def get_homework_reading(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, entry_type, content, date FROM homework_reading ORDER BY date DESC")
    items = []
    for row in cursor.fetchall():
        items.append({'id': row[0], 'type': row[1], 'content': row[2], 'date': row[3]})
    return items

def add_homework_reading(conn, entry_type: str, content: str, date: str) -> int:
    cursor = conn.execute(
        "INSERT INTO homework_reading (entry_type, content, date) VALUES (?,?,?)",
        (entry_type, content, date)
    )
    conn.commit()
    return cursor.lastrowid

def delete_homework_reading(conn, entry_id: int):
    conn.execute("DELETE FROM homework_reading WHERE id=?", (entry_id,))
    conn.commit()