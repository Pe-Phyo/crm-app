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
            birthdate TEXT DEFAULT ''
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

        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            teacher_name TEXT NOT NULL DEFAULT '',
            subject TEXT DEFAULT '',
            package_name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'private',
            lesson_count INTEGER NOT NULL DEFAULT 4,
            rate INTEGER NOT NULL,
            discount_amount INTEGER DEFAULT 0,
            billing_cycle TEXT NOT NULL DEFAULT 'monthly',
            start_date TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS meeting_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            type TEXT NOT NULL,
            is_in_person INTEGER DEFAULT 0,
            meeting_id TEXT,
            teacher_id TEXT DEFAULT '',
            teacher_name TEXT DEFAULT '',
            rate INTEGER DEFAULT 0,
            package_id INTEGER DEFAULT NULL
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
    # Migrations for existing databases
    try:
        conn.execute("ALTER TABLE meeting_times ADD COLUMN teacher_id TEXT DEFAULT ''")
    except:
        pass
    try:
        conn.execute("ALTER TABLE meeting_times ADD COLUMN teacher_name TEXT DEFAULT ''")
    except:
        pass
    try:
        conn.execute("ALTER TABLE meeting_times ADD COLUMN rate INTEGER DEFAULT 0")
    except:
        pass
    try:
        conn.execute("ALTER TABLE meeting_times ADD COLUMN package_id INTEGER DEFAULT NULL")
    except:
        pass

# ------------------------------------------------------------
# Profile (unchanged from previous update)
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
        'birthdate': row[13] if len(row) > 13 else ''
    }

def save_profile(conn, profile: Dict):
    conn.execute("""
        INSERT OR REPLACE INTO profile (
            uuid, name, location, timezone, age_group, academic_year,
            telegram, is_minor, parent_name, school_name,
            educational_goals, behavioral_comments, general_comments, birthdate
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
        profile.get('birthdate', '')
    ))
    conn.commit()

# ------------------------------------------------------------
# Phones, Emails, Parent Phones, Parent Emails (unchanged)
# ------------------------------------------------------------
def get_phones(conn) -> List[str]:
    cursor = conn.execute("SELECT value FROM phones ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def set_phones(conn, phones: List[str]):
    conn.execute("DELETE FROM phones")
    for phone in phones:
        conn.execute("INSERT INTO phones (value) VALUES (?)", (phone,))
    conn.commit()

def get_emails(conn) -> List[str]:
    cursor = conn.execute("SELECT value FROM emails ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def set_emails(conn, emails: List[str]):
    conn.execute("DELETE FROM emails")
    for email in emails:
        conn.execute("INSERT INTO emails (value) VALUES (?)", (email,))
    conn.commit()

def get_parent_phones(conn) -> List[str]:
    cursor = conn.execute("SELECT value FROM parent_phones ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def set_parent_phones(conn, phones: List[str]):
    conn.execute("DELETE FROM parent_phones")
    for phone in phones:
        conn.execute("INSERT INTO parent_phones (value) VALUES (?)", (phone,))
    conn.commit()

def get_parent_emails(conn) -> List[str]:
    cursor = conn.execute("SELECT value FROM parent_emails ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def set_parent_emails(conn, emails: List[str]):
    conn.execute("DELETE FROM parent_emails")
    for email in emails:
        conn.execute("INSERT INTO parent_emails (value) VALUES (?)", (email,))
    conn.commit()

# ------------------------------------------------------------
# Relationships (unchanged)
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
# Packages (NEW)
# ------------------------------------------------------------
def add_package(conn, package: Dict) -> int:
    """Insert a new package row and return its id."""
    cursor = conn.execute("""
        INSERT INTO packages (teacher_id, teacher_name, subject, package_name, type, lesson_count,
                              rate, discount_amount, billing_cycle, start_date, end_date, status, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        package['teacher_id'],
        package.get('teacher_name', ''),
        package.get('subject', ''),
        package['package_name'],
        package.get('type', 'private'),
        package.get('lesson_count', 4),
        package['rate'],
        package.get('discount_amount', 0),
        package.get('billing_cycle', 'monthly'),
        package.get('start_date', ''),
        package.get('end_date', ''),
        package.get('status', 'active'),
        package.get('notes', '')
    ))
    conn.commit()
    return cursor.lastrowid

def get_packages(conn) -> List[Dict]:
    """Return all packages for this student."""
    cursor = conn.execute("SELECT * FROM packages ORDER BY id")
    rows = cursor.fetchall()
    packages = []
    for row in rows:
        packages.append({
            'id': row[0],
            'teacher_id': row[1],
            'teacher_name': row[2],
            'subject': row[3],
            'package_name': row[4],
            'type': row[5],
            'lesson_count': row[6],
            'rate': row[7],
            'discount_amount': row[8],
            'billing_cycle': row[9],
            'start_date': row[10],
            'end_date': row[11],
            'status': row[12],
            'notes': row[13]
        })
    return packages

def update_package(conn, package_id: int, data: Dict):
    """Update fields of an existing package."""
    allowed = ['teacher_id', 'teacher_name', 'subject', 'package_name', 'type', 'lesson_count',
               'rate', 'discount_amount', 'billing_cycle', 'start_date', 'end_date', 'status', 'notes']
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return
    set_clause = ', '.join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [package_id]
    conn.execute(f"UPDATE packages SET {set_clause} WHERE id=?", values)
    conn.commit()

def delete_package(conn, package_id: int):
    """Delete a package and optionally its associated meeting times."""
    conn.execute("DELETE FROM packages WHERE id=?", (package_id,))
    # Optionally remove meeting_times that belong to this package (if you want cascade)
    conn.execute("DELETE FROM meeting_times WHERE package_id=?", (package_id,))
    conn.commit()

# ------------------------------------------------------------
# Meeting times (updated to include package_id)
# ------------------------------------------------------------
def add_meeting_time(conn, name: str, day: str, time: str, mtype: str,
                     is_in_person: bool, meeting_id: str = None,
                     teacher_id: str = '', teacher_name: str = '', rate: int = 0,
                     package_id: int = None) -> int:
    cursor = conn.execute(
        "INSERT INTO meeting_times (name, day, time, type, is_in_person, meeting_id, teacher_id, teacher_name, rate, package_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (name, day, time, mtype, 1 if is_in_person else 0, meeting_id, teacher_id, teacher_name, rate, package_id)
    )
    conn.commit()
    return cursor.lastrowid

def get_meeting_times(conn) -> List[Dict]:
    cursor = conn.execute("SELECT id, name, day, time, type, is_in_person, meeting_id, teacher_id, teacher_name, rate, package_id FROM meeting_times ORDER BY id")
    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'name': row[1],
            'day': row[2],
            'time': row[3],
            'type': row[4],
            'is_in_person': bool(row[5]),
            'meeting_id': row[6],
            'teacher_id': row[7],
            'teacher_name': row[8],
            'rate': row[9],
            'package_id': row[10]
        })
    return items

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
# Attendance, Payments, Homework (unchanged)
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