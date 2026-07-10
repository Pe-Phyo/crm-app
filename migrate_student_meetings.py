import os
import sys

# Add libs to path (same as main.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

from src import crypto_engine
from src.students import index_db, student_db, crypto

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Unlock master key
crypto_engine.unlock(DATA_DIR)

index_conn = index_db.open_index_db_with_key(DATA_DIR, crypto_engine.get_master_key())
students = index_db.get_all_students(index_conn)

for s in students:
    uuid = s['uuid']
    key = index_db.get_student_db_key(index_conn, uuid)
    if not key:
        print(f"Skipping {uuid} – no db key")
        continue
    student_dir = os.path.join(DATA_DIR, 'students', 'students')
    try:
        conn = student_db.open_student_db(student_dir, uuid, key)
        # Add missing columns (safe to run even if they already exist)
        for col_def in [
            "ALTER TABLE meeting_times ADD COLUMN teacher_id TEXT DEFAULT ''",
            "ALTER TABLE meeting_times ADD COLUMN teacher_name TEXT DEFAULT ''",
            "ALTER TABLE meeting_times ADD COLUMN rate INTEGER DEFAULT 0",
            "ALTER TABLE meeting_times ADD COLUMN package_id INTEGER DEFAULT NULL"
        ]:
            try:
                conn.execute(col_def)
                conn.commit()
            except:
                pass  # column already exists
        conn.close()
        print(f"Migrated {uuid} ({s['name']})")
    except Exception as e:
        print(f"Failed for {uuid}: {e}")

index_db.close_index_db(index_conn)
print("Migration complete.")