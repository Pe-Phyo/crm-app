import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib

from .crypto import (
    hash_password,
    verify_password,
    open_encrypted_db,
    create_encrypted_db,
    generate_key,
    rekey_db
)

SALT_FILE = "index.salt"
DB_FILE = "index.db"

# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------
def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=32)

def _read_salt(data_dir: str) -> bytes:
    with open(os.path.join(data_dir, SALT_FILE), 'rb') as f:
        return f.read()

def _write_salt(data_dir: str, salt: bytes):
    with open(os.path.join(data_dir, SALT_FILE), 'wb') as f:
        f.write(salt)

# ------------------------------------------------------------
# Flag helpers
# ------------------------------------------------------------
def country_flag(code: str) -> str:
    if len(code) != 2:
        return ''
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))

def _load_tz_flag_map(data_dir: str) -> Dict[str, str]:
    """Return a dict mapping timezone value (e.g., 'GMT+6.5') to flag emoji."""
    tz_file = os.path.join(data_dir, 'utils', 'timezone_data.json')
    if not os.path.exists(tz_file):
        return {}
    with open(tz_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    flag_map = {}
    for loc in data.get('locations', []):
        tz_value = loc.get('value', '')
        cc = loc.get('country_code', '')
        if cc:
            flag_map[tz_value] = country_flag(cc)
    return flag_map

def get_flag_for_timezone(data_dir: str, timezone_value: str) -> str:
    """Return the flag emoji for a given timezone value (e.g., 'GMT+6.5')."""
    flag_map = _load_tz_flag_map(data_dir)
    return flag_map.get(timezone_value, '')

def get_flag_for_timezone_label(data_dir: str, tz_label: str) -> str:
    """Return the flag emoji for a given timezone label (e.g., 'Singapore')."""
    tz_file = os.path.join(data_dir, 'utils', 'timezone_data.json')
    if not os.path.exists(tz_file) or not tz_label:
        return ''
    with open(tz_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for loc in data.get('locations', []):
        if loc.get('label') == tz_label:
            cc = loc.get('country_code', '')
            if cc:
                return country_flag(cc)
    return ''

# ------------------------------------------------------------
# Setup / open
# ------------------------------------------------------------
def setup_index_db(data_dir: str, password: str):
    os.makedirs(data_dir, exist_ok=True)
    salt = os.urandom(16)
    _write_salt(data_dir, salt)
    key = _derive_key(password, salt)
    db_path = os.path.join(data_dir, DB_FILE)
    conn = create_encrypted_db(db_path, key)
    _create_tables(conn)
    conn.execute(
        "INSERT INTO auth (salt, hash, last_changed) VALUES (?, ?, ?)",
        (salt, hashlib.sha256(password.encode()).digest(), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def open_index_db_with_key(data_dir: str, key: bytes):
    db_path = os.path.join(data_dir, DB_FILE)
    conn = open_encrypted_db(db_path, key)
    _create_tables(conn)         # ensure tables including flag column
    conn.commit()
    return conn

def open_index_db(data_dir: str, password: str):
    from .. import crypto_engine
    key = crypto_engine.get_master_key()
    return open_index_db_with_key(data_dir, key)

def close_index_db(conn):
    conn.close()

# ------------------------------------------------------------
# Table creation
# ------------------------------------------------------------
def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT DEFAULT '',
            rate INTEGER DEFAULT 0,
            last_payment_date TEXT DEFAULT '',
            attendance_percentage REAL DEFAULT 0.0,
            meeting_times_summary TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            db_key BLOB NOT NULL,
            flag TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS auth (
            id INTEGER PRIMARY KEY,
            salt BLOB NOT NULL,
            hash BLOB NOT NULL,
            last_changed TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            salt BLOB NOT NULL,
            hash BLOB NOT NULL,
            date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            created TEXT NOT NULL
        );
    """)
    # Add flag column if missing (for existing databases)
    try:
        conn.execute("ALTER TABLE students ADD COLUMN flag TEXT DEFAULT ''")
    except:
        pass
    try:
        conn.execute("ALTER TABLE students ADD COLUMN timezone TEXT DEFAULT ''")
    except:
        pass
    try:
        conn.execute("ALTER TABLE students ADD COLUMN teacher_id TEXT DEFAULT ''")
    except:
        pass

# ------------------------------------------------------------
# Student summaries
# ------------------------------------------------------------
def add_student_summary(conn, uuid: str, name: str, location: str, timezone: str, rate: int,
                        last_payment_date: str, attendance_percentage: float,
                        meeting_times_summary: str, status: str, db_key: bytes,
                        flag: str = '', teacher_name: str = ''):
    conn.execute(
        "INSERT INTO students (uuid, name, location, timezone, rate, last_payment_date, attendance_percentage, meeting_times_summary, status, db_key, flag, flag) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (uuid, name, location, timezone, rate, last_payment_date, attendance_percentage, meeting_times_summary, status, db_key, flag)
    )
    conn.commit()

def update_student_summary(conn, uuid: str, **kwargs):
    allowed = {'name', 'location', 'timezone', 'rate', 'last_payment_date', 'attendance_percentage', 'meeting_times_summary', 'status', 'flag'}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    set_clause = ', '.join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [uuid]
    conn.execute(f"UPDATE students SET {set_clause} WHERE uuid=?", values)
    conn.commit()

def delete_student_summary(conn, uuid: str):
    conn.execute("DELETE FROM students WHERE uuid=?", (uuid,))
    conn.commit()

def get_all_students(conn) -> List[Dict]:
    cursor = conn.execute("SELECT uuid, name, location, timezone, rate, last_payment_date, attendance_percentage, meeting_times_summary, status, flag FROM students ORDER BY last_payment_date DESC")
    rows = cursor.fetchall()
    students = []
    for row in rows:
        students.append({
            'uuid': row[0],
            'name': row[1],
            'location': row[2],
            'timezone': row[3],
            'rate': row[4],
            'last_payment_date': row[5],
            'attendance_percentage': row[6],
            'meeting_times_summary': row[7],
            'status': row[8],
            'flag': row[9] if len(row) > 9 else ''
        })
    return students

def get_student_summary(conn, uuid: str) -> Optional[Dict]:
    cursor = conn.execute("SELECT uuid, name, location, rate, last_payment_date, attendance_percentage, meeting_times_summary, status, flag FROM students WHERE uuid=?", (uuid,))
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        'uuid': row[0],
        'name': row[1],
        'location': row[2],
        'rate': row[3],
        'last_payment_date': row[4],
        'attendance_percentage': row[5],
        'meeting_times_summary': row[6],
        'status': row[7],
        'flag': row[8] if len(row) > 8 else ''
    }

def get_student_db_key(conn, uuid: str) -> Optional[bytes]:
    cursor = conn.execute("SELECT db_key FROM students WHERE uuid=?", (uuid,))
    row = cursor.fetchone()
    if row:
        return row[0]
    return None

# ------------------------------------------------------------
# Auth helpers (unchanged)
# ------------------------------------------------------------
def get_auth_record(conn) -> Dict:
    cursor = conn.execute("SELECT salt, hash, last_changed FROM auth LIMIT 1")
    row = cursor.fetchone()
    return {'salt': row[0], 'hash': row[1], 'last_changed': row[2]}

def update_auth_password(conn, new_salt: bytes, new_hash: bytes):
    conn.execute(
        "UPDATE auth SET salt=?, hash=?, last_changed=? WHERE id=1",
        (new_salt, new_hash, datetime.utcnow().isoformat())
    )
    conn.commit()

def add_password_to_history(conn, salt: bytes, pw_hash: bytes):
    conn.execute(
        "INSERT INTO password_history (salt, hash, date) VALUES (?,?,?)",
        (salt, pw_hash, datetime.utcnow().isoformat())
    )
    conn.commit()

def is_password_in_history(conn, password: str) -> bool:
    cursor = conn.execute("SELECT salt, hash FROM password_history")
    for salt, stored_hash in cursor.fetchall():
        if verify_password(password, salt, stored_hash):
            return True
    return False

# ------------------------------------------------------------
# Action items (unchanged)
# ------------------------------------------------------------
def get_action_items(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            created TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()
    cursor = conn.execute(
        "SELECT id, text, done, created FROM action_items ORDER BY id DESC"
    )
    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'text': row[1],
            'done': bool(row[2]),
            'created': row[3]
        })
    return items

def add_action_item(conn, text: str) -> int:
    now = datetime.utcnow().isoformat()
    cursor = conn.execute("INSERT INTO action_items (text, done, created) VALUES (?,0,?)", (text, now))
    conn.commit()
    return cursor.lastrowid

def update_action_item(conn, item_id: int, text: str = None, done: bool = None):
    fields = []
    values = []
    if text is not None:
        fields.append("text=?")
        values.append(text)
    if done is not None:
        fields.append("done=?")
        values.append(1 if done else 0)
    if not fields:
        return
    values.append(item_id)
    conn.execute(f"UPDATE action_items SET {', '.join(fields)} WHERE id=?", values)
    conn.commit()

def delete_action_item(conn, item_id: int):
    conn.execute("DELETE FROM action_items WHERE id=?", (item_id,))
    conn.commit()

def setup_index_db_with_master_key(data_dir: str, master_key: bytes):
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, DB_FILE)
    conn = create_encrypted_db(db_path, master_key)
    _create_tables(conn)
    conn.execute(
        "INSERT INTO auth (salt, hash, last_changed) VALUES (?,?,?)",
        (b'', b'', datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()