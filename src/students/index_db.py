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
    """Derive 32‑byte key from password + salt using scrypt."""
    return hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=32)

def _read_salt(data_dir: str) -> bytes:
    with open(os.path.join(data_dir, SALT_FILE), 'rb') as f:
        return f.read()

def _write_salt(data_dir: str, salt: bytes):
    with open(os.path.join(data_dir, SALT_FILE), 'wb') as f:
        f.write(salt)

# ------------------------------------------------------------
# Setup / open
# ------------------------------------------------------------
def setup_index_db(data_dir: str, password: str):
    """Create the index database and all its tables."""
    os.makedirs(data_dir, exist_ok=True)
    salt = os.urandom(16)
    _write_salt(data_dir, salt)
    key = _derive_key(password, salt)
    db_path = os.path.join(data_dir, DB_FILE)
    conn = create_encrypted_db(db_path, key)
    _create_tables(conn)
    # Store auth record
    pw_hash, _ = hash_password(password, salt)   # we reuse the same salt for simplicity
    conn.execute(
        "INSERT INTO auth (salt, hash, last_changed) VALUES (?, ?, ?)",
        (salt, pw_hash, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def open_index_db_with_key(data_dir: str, key: bytes):
    db_path = os.path.join(data_dir, DB_FILE)
    conn = open_encrypted_db(db_path, key)
    # No password verification needed because we already authenticated.
    return conn

def open_index_db(data_dir: str, password: str) -> Any:
    """Open the index DB with the given password. Returns a connection."""
    salt = _read_salt(data_dir)
    key = _derive_key(password, salt)
    db_path = os.path.join(data_dir, DB_FILE)
    conn = open_encrypted_db(db_path, key)
    # Verify that the password matches the stored hash (belt and suspenders)
    cursor = conn.execute("SELECT salt, hash FROM auth LIMIT 1")
    row = cursor.fetchone()
    if row is None:
        raise ValueError("Auth record missing")
    stored_salt, stored_hash = row
    if not verify_password(password, stored_salt, stored_hash):
        raise ValueError("Incorrect password")
    return conn

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
            db_key BLOB NOT NULL
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

# ------------------------------------------------------------
# Student summaries
# ------------------------------------------------------------
def add_student_summary(conn, uuid: str, name: str, location: str, rate: int,
                        last_payment_date: str, attendance_percentage: float,
                        meeting_times_summary: str, status: str, db_key: bytes):
    conn.execute(
        "INSERT INTO students (uuid, name, location, rate, last_payment_date, attendance_percentage, meeting_times_summary, status, db_key) VALUES (?,?,?,?,?,?,?,?,?)",
        (uuid, name, location, rate, last_payment_date, attendance_percentage, meeting_times_summary, status, db_key)
    )
    conn.commit()

def update_student_summary(conn, uuid: str, **kwargs):
    allowed = {'name', 'location', 'rate', 'last_payment_date', 'attendance_percentage', 'meeting_times_summary', 'status'}
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
    cursor = conn.execute("SELECT uuid, name, location, rate, last_payment_date, attendance_percentage, meeting_times_summary, status FROM students ORDER BY last_payment_date DESC")
    rows = cursor.fetchall()
    students = []
    for row in rows:
        students.append({
            'uuid': row[0],
            'name': row[1],
            'location': row[2],
            'rate': row[3],
            'last_payment_date': row[4],
            'attendance_percentage': row[5],
            'meeting_times_summary': row[6],
            'status': row[7]
        })
    return students

def get_student_summary(conn, uuid: str) -> Optional[Dict]:
    cursor = conn.execute("SELECT uuid, name, location, rate, last_payment_date, attendance_percentage, meeting_times_summary, status FROM students WHERE uuid=?", (uuid,))
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
        'status': row[7]
    }

def get_student_db_key(conn, uuid: str) -> Optional[bytes]:
    cursor = conn.execute("SELECT db_key FROM students WHERE uuid=?", (uuid,))
    row = cursor.fetchone()
    if row:
        return row[0]
    return None

# ------------------------------------------------------------
# Auth helpers (used by auth.py)
# ------------------------------------------------------------
def get_auth_record(conn) -> Dict:
    """Return the single auth row."""
    cursor = conn.execute("SELECT salt, hash, last_changed FROM auth LIMIT 1")
    row = cursor.fetchone()
    return {'salt': row[0], 'hash': row[1], 'last_changed': row[2]}

def update_auth_password(conn, new_salt: bytes, new_hash: bytes):
    """Update auth record after password change."""
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
    """Check if the given password matches any stored history."""
    cursor = conn.execute("SELECT salt, hash FROM password_history")
    for salt, stored_hash in cursor.fetchall():
        if verify_password(password, salt, stored_hash):
            return True
    return False

# ------------------------------------------------------------
# Action items
# ------------------------------------------------------------
def get_action_items(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, text, done, created FROM action_items ORDER BY id DESC")
    items = []
    for row in cursor.fetchall():
        items.append({'id': row[0], 'text': row[1], 'done': bool(row[2]), 'created': row[3]})
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