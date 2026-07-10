import os
from ...crypto_engine import get_master_key
from .models import PackageTemplate

# The database will live here
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'data', 'pricing', 'pricing.db'
)

def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def open_pricing_db():
    """Open the encrypted pricing database using the master key."""
    from ...students.crypto import open_encrypted_db
    key = get_master_key()
    if not key:
        raise RuntimeError("Master key not unlocked")
    _ensure_dir()
    # If the database file doesn't exist yet, create it encrypted
    if not os.path.exists(DB_PATH):
        from ...students.crypto import create_encrypted_db
        conn = create_encrypted_db(DB_PATH, key)
        init_pricing_db(conn)
        conn.commit()
        return conn
    return open_encrypted_db(DB_PATH, key)

def init_pricing_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS package_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('private','group')),
            lesson_count INTEGER NOT NULL DEFAULT 4,
            default_rate INTEGER NOT NULL,
            subject TEXT DEFAULT '',
            billing_cycle TEXT NOT NULL DEFAULT 'monthly',
            schedule_json TEXT DEFAULT '[]',  -- list of {day, time} objects
            active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS base_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT,
            subject TEXT,
            rate INTEGER NOT NULL,
            effective_from TEXT NOT NULL
        );
    """)
    conn.commit()

# ---- CRUD for templates (will be used by back-office later) ----
def add_template(data: dict) -> int:
    conn = open_pricing_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO package_templates (teacher_id, name, type, lesson_count, default_rate, subject, billing_cycle, schedule_json)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        data['teacher_id'],
        data['name'],
        data['type'],
        data.get('lesson_count', 4),
        data.get('default_rate', 0),
        data.get('subject', ''),
        data.get('billing_cycle', 'monthly'),
        data.get('schedule_json', '[]')
    ))
    conn.commit()
    tid = c.lastrowid
    conn.close()
    return tid

def get_templates_for_teacher(teacher_id: str) -> list[PackageTemplate]:
    conn = open_pricing_db()
    c = conn.cursor()
    c.execute("SELECT * FROM package_templates WHERE teacher_id=? AND active=1", (teacher_id,))
    rows = c.fetchall()
    conn.close()
    return [_row_to_template(row) for row in rows]

def get_template(template_id: int) -> PackageTemplate | None:
    conn = open_pricing_db()
    c = conn.cursor()
    c.execute("SELECT * FROM package_templates WHERE id=?", (template_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return _row_to_template(row)
    return None

def _row_to_template(row) -> PackageTemplate:
    return PackageTemplate(
        id=row[0],
        teacher_id=row[1],
        name=row[2],
        type=row[3],
        lesson_count=row[4],
        default_rate=row[5],
        subject=row[6],
        billing_cycle=row[7],
        schedule_json=row[8]
    )
def update_template(template_id: int, data: dict):
    allowed = ['teacher_id', 'name', 'type', 'lesson_count', 'default_rate', 'subject', 'billing_cycle', 'schedule_json', 'active']
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return
    conn = open_pricing_db()
    set_clause = ', '.join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [template_id]
    conn.execute(f"UPDATE package_templates SET {set_clause} WHERE id=?", values)
    conn.commit()
    conn.close()

def delete_template(template_id: int):
    conn = open_pricing_db()
    conn.execute("DELETE FROM package_templates WHERE id=?", (template_id,))
    conn.commit()
    conn.close()

def get_all_templates() -> list[PackageTemplate]:
    conn = open_pricing_db()
    c = conn.cursor()
    c.execute("SELECT * FROM package_templates WHERE active=1 ORDER BY teacher_id, name")
    rows = c.fetchall()
    conn.close()
    return [_row_to_template(row) for row in rows]