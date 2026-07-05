import os
from typing import Dict, List, Optional
from datetime import datetime
from ..students.crypto import create_encrypted_db, open_encrypted_db, generate_key

def create_staff_db(data_dir: str, uuid: str) -> bytes:
    """Create a new per‑staff encrypted database and return its key."""
    os.makedirs(data_dir, exist_ok=True)
    key = generate_key()
    db_path = os.path.join(data_dir, f"{uuid}.sqlite")
    conn = create_encrypted_db(db_path, key)
    _create_tables(conn)
    conn.commit()
    conn.close()
    return key

def open_staff_db(data_dir: str, uuid: str, key: bytes):
    db_path = os.path.join(data_dir, f"{uuid}.sqlite")
    return open_encrypted_db(db_path, key)

def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS profile (
            uuid TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            full_name TEXT,
            display_name TEXT,
            email TEXT,
            phone TEXT,
            timezone TEXT,
            default_hourly_rate INTEGER,
            default_meeting_link_pattern TEXT,
            bio TEXT,
            role TEXT,
            is_active INTEGER DEFAULT 0,
            password_hash BLOB,
            password_salt BLOB,
            password_last_changed TEXT,
            must_change_password INTEGER DEFAULT 0,
            payout_taxes_json TEXT DEFAULT '',
            payment_methods_json TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS availability_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER,
            start_time TEXT,
            end_time TEXT,
            status TEXT DEFAULT 'pending'
        );

        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT,
            end_date TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending'
        );
    """)

# --- Profile CRUD ---
def get_profile(conn) -> Dict:
    cursor = conn.execute("SELECT * FROM profile LIMIT 1")
    row = cursor.fetchone()
    if row is None:
        return {}
    return {
        'uuid': row[0],
        'username': row[1],
        'full_name': row[2],
        'display_name': row[3],
        'email': row[4],
        'phone': row[5],
        'timezone': row[6],
        'default_hourly_rate': row[7],
        'default_meeting_link_pattern': row[8],
        'bio': row[9],
        'role': row[10],
        'is_active': bool(row[11]),
        'password_hash': row[12],
        'password_salt': row[13],
        'password_last_changed': row[14],
        'must_change_password': bool(row[15]),
        'payout_taxes_json': row[16],
        'payment_methods_json': row[17],
        'created_at': row[18],
        'updated_at': row[19]
    }

def save_profile(conn, profile: Dict):
    conn.execute("""
        INSERT OR REPLACE INTO profile (
            uuid, username, full_name, display_name, email, phone, timezone,
            default_hourly_rate, default_meeting_link_pattern, bio, role,
            is_active, password_hash, password_salt, password_last_changed,
            must_change_password, payout_taxes_json, payment_methods_json,
            created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        profile['uuid'],
        profile['username'],
        profile.get('full_name', ''),
        profile.get('display_name', ''),
        profile.get('email', ''),
        profile.get('phone', ''),
        profile.get('timezone', ''),
        profile.get('default_hourly_rate', 0),
        profile.get('default_meeting_link_pattern', ''),
        profile.get('bio', ''),
        profile['role'],
        1 if profile.get('is_active') else 0,
        profile.get('password_hash', b''),
        profile.get('password_salt', b''),
        profile.get('password_last_changed', ''),
        1 if profile.get('must_change_password') else 0,
        profile.get('payout_taxes_json', ''),
        profile.get('payment_methods_json', ''),
        profile.get('created_at', datetime.utcnow().isoformat()),
        profile.get('updated_at', datetime.utcnow().isoformat())
    ))
    conn.commit()

# --- Availability ---
def get_availability(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, day_of_week, start_time, end_time, status FROM availability_slots ORDER BY day_of_week, start_time")
    return [{'id': r[0], 'day_of_week': r[1], 'start_time': r[2], 'end_time': r[3], 'status': r[4]} for r in cursor.fetchall()]

def set_availability(conn, slots: List[Dict]):
    conn.execute("DELETE FROM availability_slots")
    for slot in slots:
        conn.execute(
            "INSERT INTO availability_slots (day_of_week, start_time, end_time, status) VALUES (?,?,?,?)",
            (slot['day_of_week'], slot['start_time'], slot['end_time'], slot.get('status', 'pending'))
        )
    conn.commit()

# --- Holidays ---
def get_holidays(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, start_date, end_date, description, status FROM holidays ORDER BY start_date")
    return [{'id': r[0], 'start_date': r[1], 'end_date': r[2], 'description': r[3], 'status': r[4]} for r in cursor.fetchall()]

def set_holidays(conn, holidays: List[Dict]):
    conn.execute("DELETE FROM holidays")
    for h in holidays:
        conn.execute(
            "INSERT INTO holidays (start_date, end_date, description, status) VALUES (?,?,?,?)",
            (h['start_date'], h['end_date'], h.get('description', ''), h.get('status', 'pending'))
        )
    conn.commit()