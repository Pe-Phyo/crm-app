import os
from datetime import datetime
from typing import Dict, List, Optional
from ..students.crypto import create_encrypted_db, open_encrypted_db, generate_key

def create_profile_db(data_dir: str, uuid: str) -> bytes:
    """Create a new encrypted profile DB and return its key."""
    os.makedirs(data_dir, exist_ok=True)
    key = generate_key()
    db_path = os.path.join(data_dir, f"{uuid}.sqlite")
    conn = create_encrypted_db(db_path, key)
    _create_tables(conn)
    conn.commit()
    conn.close()
    return key

def open_profile_db(data_dir: str, uuid: str, key: bytes):
    db_path = os.path.join(data_dir, f"{uuid}.sqlite")
    return open_encrypted_db(db_path, key)

def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS profile_details (
            uuid TEXT PRIMARY KEY,
            full_name TEXT DEFAULT '',
            display_name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            timezone TEXT DEFAULT '',
            default_hourly_rate INTEGER DEFAULT 0,
            default_meeting_link_pattern TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            languages TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL
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

        CREATE TABLE IF NOT EXISTS teaching_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            level TEXT DEFAULT '',
            curriculum_id TEXT DEFAULT '',
            years_exp INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS teaching_modes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS teaching_styles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            style TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS student_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS curriculum_expertise (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curriculum_id TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            issuer TEXT DEFAULT '',
            year INTEGER DEFAULT 0
        );
    """)

# --- Profile Details CRUD ---
def get_profile_details(conn) -> Dict:
    cursor = conn.execute("SELECT * FROM profile_details LIMIT 1")
    row = cursor.fetchone()
    if row is None:
        return {}
    return {
        'uuid': row[0],
        'full_name': row[1],
        'display_name': row[2],
        'email': row[3],
        'phone': row[4],
        'timezone': row[5],
        'default_hourly_rate': row[6],
        'default_meeting_link_pattern': row[7],
        'bio': row[8],
        'languages': row[9],
        'created_at': row[10],
        'updated_at': row[11]
    }

def save_profile_details(conn, details: Dict):
    conn.execute("""
        INSERT OR REPLACE INTO profile_details (
            uuid, full_name, display_name, email, phone, timezone,
            default_hourly_rate, default_meeting_link_pattern, bio, languages,
            created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        details['uuid'],
        details.get('full_name', ''),
        details.get('display_name', ''),
        details.get('email', ''),
        details.get('phone', ''),
        details.get('timezone', ''),
        details.get('default_hourly_rate', 0),
        details.get('default_meeting_link_pattern', ''),
        details.get('bio', ''),
        details.get('languages', '[]'),
        details.get('created_at', datetime.utcnow().isoformat()),
        details.get('updated_at', datetime.utcnow().isoformat())
    ))
    conn.commit()

# --- Phones & Emails (multi-value) ---
def get_phones(conn) -> List[str]:
    return [r[1] for r in conn.execute("SELECT id, value FROM phones").fetchall()]

def set_phones(conn, phones: List[str]):
    conn.execute("DELETE FROM phones")
    for p in phones:
        conn.execute("INSERT INTO phones (value) VALUES (?)", (p,))
    conn.commit()

def get_emails(conn) -> List[str]:
    return [r[1] for r in conn.execute("SELECT id, value FROM emails").fetchall()]

def set_emails(conn, emails: List[str]):
    conn.execute("DELETE FROM emails")
    for e in emails:
        conn.execute("INSERT INTO emails (value) VALUES (?)", (e,))
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

# --- Capabilities ---
def get_teaching_subjects(conn) -> List[Dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM teaching_subjects").fetchall()]

def set_teaching_subjects(conn, subjects: List[Dict]):
    conn.execute("DELETE FROM teaching_subjects")
    for s in subjects:
        conn.execute(
            "INSERT INTO teaching_subjects (subject_id, subject_name, level, curriculum_id, years_exp) VALUES (?,?,?,?,?)",
            (s.get('subject_id',''), s.get('subject_name',''), s.get('level',''), s.get('curriculum_id',''), s.get('years_exp',0))
        )
    conn.commit()

def get_teaching_modes(conn) -> List[str]:
    return [r[1] for r in conn.execute("SELECT id, mode FROM teaching_modes").fetchall()]

def set_teaching_modes(conn, modes: List[str]):
    conn.execute("DELETE FROM teaching_modes")
    for m in modes:
        conn.execute("INSERT INTO teaching_modes (mode) VALUES (?)", (m,))
    conn.commit()

def get_teaching_styles(conn) -> List[str]:
    return [r[1] for r in conn.execute("SELECT id, style FROM teaching_styles").fetchall()]

def set_teaching_styles(conn, styles: List[str]):
    conn.execute("DELETE FROM teaching_styles")
    for s in styles:
        conn.execute("INSERT INTO teaching_styles (style) VALUES (?)", (s,))
    conn.commit()

def get_student_types(conn) -> List[str]:
    return [r[1] for r in conn.execute("SELECT id, type FROM student_types").fetchall()]

def set_student_types(conn, types: List[str]):
    conn.execute("DELETE FROM student_types")
    for t in types:
        conn.execute("INSERT INTO student_types (type) VALUES (?)", (t,))
    conn.commit()

def get_curriculum_expertise(conn) -> List[str]:
    return [r[1] for r in conn.execute("SELECT id, curriculum_id FROM curriculum_expertise").fetchall()]

def set_curriculum_expertise(conn, curricula: List[str]):
    conn.execute("DELETE FROM curriculum_expertise")
    for c in curricula:
        conn.execute("INSERT INTO curriculum_expertise (curriculum_id) VALUES (?)", (c,))
    conn.commit()

def get_certifications(conn) -> List[Dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM certifications").fetchall()]

def set_certifications(conn, certs: List[Dict]):
    conn.execute("DELETE FROM certifications")
    for c in certs:
        conn.execute(
            "INSERT INTO certifications (name, issuer, year) VALUES (?,?,?)",
            (c.get('name',''), c.get('issuer',''), c.get('year',0))
        )
    conn.commit()