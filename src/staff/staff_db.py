import os
from datetime import datetime
from typing import Dict
from ..students.crypto import create_encrypted_db, open_encrypted_db, generate_key

def create_staff_db(data_dir: str, uuid: str) -> bytes:
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
            role TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            password_hash BLOB,
            password_salt BLOB,
            password_last_changed TEXT,
            must_change_password INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        );
    """)

def get_profile(conn) -> Dict:
    """Return auth record. Uses SELECT * for backward compatibility."""
    cursor = conn.execute("SELECT * FROM profile LIMIT 1")
    row = cursor.fetchone()
    if row is None:
        return {}
    # Map the first 10 columns (auth fields) – extra columns ignored
    return {
        'uuid': row[0],
        'username': row[1],
        'role': row[2],
        'is_active': bool(row[3]),
        'password_hash': row[4],
        'password_salt': row[5],
        'password_last_changed': row[6],
        'must_change_password': bool(row[7]),
        'created_at': row[8],
        'updated_at': row[9]
    }

def save_profile(conn, auth: Dict):
    # Only update auth columns – leaves other columns untouched
    conn.execute("""
        INSERT OR REPLACE INTO profile (
            uuid, username, role, is_active, password_hash, password_salt,
            password_last_changed, must_change_password, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        auth['uuid'],
        auth['username'],
        auth['role'],
        1 if auth.get('is_active') else 0,
        auth.get('password_hash', b''),
        auth.get('password_salt', b''),
        auth.get('password_last_changed', ''),
        1 if auth.get('must_change_password') else 0,
        auth.get('created_at', datetime.utcnow().isoformat()),
        auth.get('updated_at', datetime.utcnow().isoformat())
    ))
    conn.commit()