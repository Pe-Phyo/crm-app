import os
from typing import List, Dict, Optional
from .crypto import create_encrypted_db, open_encrypted_db, generate_key

# ------------------------------------------------------------
# Create / Open
# ------------------------------------------------------------
def create_student_db(data_dir: str, uuid: str) -> bytes:
    os.makedirs(data_dir, exist_ok=True)
    key = generate_key()
    db_path = os.path.join(data_dir, f"{uuid}.sqlite")
    conn = create_encrypted_db(db_path, key)
    _create_tables(conn)
    conn.commit()
    conn.close()
    return key

def open_student_db(data_dir: str, uuid: str, key: bytes):
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
            telegram TEXT DEFAULT '',
            is_minor INTEGER DEFAULT 0,
            parent_name TEXT DEFAULT '',
            school_name TEXT DEFAULT '',
            educational_goals TEXT DEFAULT '',
            behavioral_comments TEXT DEFAULT '',
            general_comments TEXT DEFAULT '',
            rate INTEGER DEFAULT 0,
            birthdate TEXT DEFAULT '',
            teacher_id TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS parent_phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS parent_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            other_uuid TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            invoice_group INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS meeting_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
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
            entry_type TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL
        );
    """)

# ------------------------------------------------------------
# Profile
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
        'telegram': row[6],
        'is_minor': bool(row[7]),
        'parent_name': row[8],
        'school_name': row[9],
        'educational_goals': row[10],
        'behavioral_comments': row[11],
        'general_comments': row[12],
        'rate': row[13],
        'birthdate': row[14] if len(row) > 14 else '',
        'teacher_id': row[15] if len(row) > 15 else ''
    }

def save_profile(conn, profile: Dict):
    conn.execute("""
        INSERT OR REPLACE INTO profile (
            uuid, name, location, timezone, age_group, academic_year,
            telegram, is_minor, parent_name, school_name,
            educational_goals, behavioral_comments, general_comments, rate,
            birthdate, teacher_id
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        profile['uuid'],
        profile.get('name', ''),
        profile.get('location', ''),
        profile.get('timezone', ''),
        profile.get('age_group', ''),
        profile.get('academic_year', ''),
        profile.get('telegram', ''),
        1 if profile.get('is_minor') else 0,
        profile.get('parent_name', ''),
        profile.get('school_name', ''),
        profile.get('educational_goals', ''),
        profile.get('behavioral_comments', ''),
        profile.get('general_comments', ''),
        profile.get('rate', 0),
        profile.get('birthdate', ''),
        profile.get('teacher_id', '')
    ))
    conn.commit()

# ------------------------------------------------------------
# Phones
# ------------------------------------------------------------
def get_phones(conn) -> List[str]:
    cursor = conn.execute("SELECT value FROM phones ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def set_phones(conn, phones: List[str]):
    conn.execute("DELETE FROM phones")
    for phone in phones:
        conn.execute("INSERT INTO phones (value) VALUES (?)", (phone,))
    conn.commit()

# ------------------------------------------------------------
# Emails
# ------------------------------------------------------------
def get_emails(conn) -> List[str]:
    cursor = conn.execute("SELECT value FROM emails ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def set_emails(conn, emails: List[str]):
    conn.execute("DELETE FROM emails")
    for email in emails:
        conn.execute("INSERT INTO emails (value) VALUES (?)", (email,))
    conn.commit()

# ------------------------------------------------------------
# Parent Phones
# ------------------------------------------------------------
def get_parent_phones(conn) -> List[str]:
    cursor = conn.execute("SELECT value FROM parent_phones ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def set_parent_phones(conn, phones: List[str]):
    conn.execute("DELETE FROM parent_phones")
    for phone in phones:
        conn.execute("INSERT INTO parent_phones (value) VALUES (?)", (phone,))
    conn.commit()

# ------------------------------------------------------------
# Parent Emails
# ------------------------------------------------------------
def get_parent_emails(conn) -> List[str]:
    cursor = conn.execute("SELECT value FROM parent_emails ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def set_parent_emails(conn, emails: List[str]):
    conn.execute("DELETE FROM parent_emails")
    for email in emails:
        conn.execute("INSERT INTO parent_emails (value) VALUES (?)", (email,))
    conn.commit()

# ------------------------------------------------------------
# Relationships (linked students)
# ------------------------------------------------------------
def get_relationships(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, other_uuid, relationship_type, invoice_group FROM relationships ORDER BY id")
    rels = []
    for row in cursor.fetchall():
        rels.append({
            'id': row[0],
            'other_uuid': row[1],
            'relationship_type': row[2],
            'invoice_group': bool(row[3])
        })
    return rels

def set_relationships(conn, relationships: List[Dict]):
    conn.execute("DELETE FROM relationships")
    for rel in relationships:
        conn.execute(
            "INSERT INTO relationships (other_uuid, relationship_type, invoice_group) VALUES (?,?,?)",
            (rel['uuid'], rel['relationship'], 1 if rel.get('invoice_group') else 0)
        )
    conn.commit()

# ------------------------------------------------------------
# Meeting times
# ------------------------------------------------------------
def get_meeting_times(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, name, day, time, type, is_in_person, meeting_id FROM meeting_times ORDER BY id")
    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'name': row[1],
            'day': row[2],
            'time': row[3],
            'type': row[4],
            'is_in_person': bool(row[5]),
            'meeting_id': row[6]
        })
    return items

def add_meeting_time(conn, name: str, day: str, time: str, mtype: str, is_in_person: bool, meeting_id: str = None) -> int:
    cursor = conn.execute(
        "INSERT INTO meeting_times (name, day, time, type, is_in_person, meeting_id) VALUES (?,?,?,?,?,?)",
        (name, day, time, mtype, 1 if is_in_person else 0, meeting_id)
    )
    conn.commit()
    return cursor.lastrowid

def delete_meeting_time(conn, slot_id: int):
    conn.execute("DELETE FROM meeting_times WHERE id=?", (slot_id,))
    conn.commit()

def get_meeting_times_summary(conn) -> str:
    items = get_meeting_times(conn)
    summaries = []
    for item in items:
        summaries.append(f"{item['name']} {item['day'][:3]} {item['time']} ({'Group' if item['type']=='group' else 'Private'})")
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
            'receipt_image': row[3]
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