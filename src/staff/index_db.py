import os
import json
from typing import List, Optional, Dict
from datetime import datetime
from ..crypto_engine import get_master_key
from ..students.crypto import create_encrypted_db, open_encrypted_db, generate_key, rekey_db

# We will store the staff index inside data/staff/
STAFF_INDEX_DB = "index.db"

def _staff_data_dir(root_data_dir: str) -> str:
    return os.path.join(root_data_dir, "staff")

def _db_path(data_dir: str) -> str:
    return os.path.join(data_dir, STAFF_INDEX_DB)

def create_staff_index(root_data_dir: str):
    """Create the staff index database encrypted with the master key."""
    data_dir = _staff_data_dir(root_data_dir)
    os.makedirs(data_dir, exist_ok=True)
    db_path = _db_path(data_dir)
    master_key = get_master_key()
    conn = create_encrypted_db(db_path, master_key)
    _create_tables(conn)
    conn.commit()
    conn.close()

def open_staff_index(root_data_dir: str):
    """Open the staff index database (already unlocked)."""
    data_dir = _staff_data_dir(root_data_dir)
    db_path = _db_path(data_dir)
    master_key = get_master_key()
    conn = open_encrypted_db(db_path, master_key)
    return conn

def close_staff_index(conn):
    conn.close()

def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS staff (
            uuid TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            db_key BLOB NOT NULL
        );
    """)

def add_staff_summary(conn, uuid: str, username: str, role: str, db_key: bytes, is_active: bool = False):
    conn.execute(
        "INSERT INTO staff (uuid, username, role, is_active, db_key) VALUES (?,?,?,?,?)",
        (uuid, username, role, 1 if is_active else 0, db_key)
    )
    conn.commit()

def get_staff_summary(conn, uuid: str) -> Optional[Dict]:
    cursor = conn.execute("SELECT uuid, username, role, is_active, db_key FROM staff WHERE uuid=?", (uuid,))
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        'uuid': row[0],
        'username': row[1],
        'role': row[2],
        'is_active': bool(row[3]),
        'db_key': row[4]
    }

def get_staff_by_username(conn, username: str) -> Optional[Dict]:
    cursor = conn.execute("SELECT uuid, username, role, is_active, db_key FROM staff WHERE username=?", (username,))
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        'uuid': row[0],
        'username': row[1],
        'role': row[2],
        'is_active': bool(row[3]),
        'db_key': row[4]
    }

def get_all_staff(conn) -> List[Dict]:
    cursor = conn.execute("SELECT uuid, username, role, is_active FROM staff ORDER BY username")
    rows = cursor.fetchall()
    return [{'uuid': r[0], 'username': r[1], 'role': r[2], 'is_active': bool(r[3])} for r in rows]

def update_staff_active(conn, uuid: str, is_active: bool):
    conn.execute("UPDATE staff SET is_active=? WHERE uuid=?", (1 if is_active else 0, uuid))
    conn.commit()

def delete_staff_summary(conn, uuid: str):
    conn.execute("DELETE FROM staff WHERE uuid=?", (uuid,))
    conn.commit()