import sys
import os
import uuid

# Make sure we can import project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.meetings.db import get_meetings, update_meeting, get_db
from src.students.index_db import (
    open_index_db_with_key, close_index_db,
    add_student_summary, get_all_students
)
from src.students.student_db import (
    create_student_db, open_student_db,
    add_meeting_time, save_profile
)
from src import crypto_engine

# ============================================================
# CONFIGURATION – change these if needed
# ============================================================
TEACHER_UUID = "a4a3b0666e034c209acb23ea22ffb2e0"   # Teacher Lucky
DRY_RUN = False   # Set to True to preview changes without saving

def main():
    # Unlock master key (prompts for MEP)
    crypto_engine.unlock('data')

    # Fetch all meetings
    meetings = get_meetings()
    print(f"Found {len(meetings)} meetings.")

    # Group meetings by student name
    student_meetings = {}   # name -> list of meeting dicts
    for m in meetings:
        for name in m['student_names']:
            name = name.strip()
            if name:
                student_meetings.setdefault(name, []).append(m)

    print(f"Unique student names: {list(student_meetings.keys())}")

    # Connect to student index
    data_dir = os.path.join(os.path.dirname(__file__), 'data', 'students')
    key = crypto_engine.get_master_key()
    index_conn = open_index_db_with_key(data_dir, key)
    try:
        existing_students = get_all_students(index_conn)
        existing_names = {s['name'] for s in existing_students}
    finally:
        close_index_db(index_conn)

    name_to_uuid = {}
    student_db_dir = os.path.join(data_dir, 'students')

    # Create a student for each unique name that doesn't already exist
    for name, meets in student_meetings.items():
        if name in existing_names:
            print(f"'{name}' already exists, skipping creation.")
            # Find existing UUID
            for s in existing_students:
                if s['name'] == name:
                    name_to_uuid[name] = s['uuid']
                    break
            continue

        new_uuid = uuid.uuid4().hex
        name_to_uuid[name] = new_uuid

        if DRY_RUN:
            print(f"Would create student: {name} (uuid={new_uuid})")
            continue

        # Create per‑student encrypted DB
        student_key = create_student_db(student_db_dir, new_uuid)

        profile = {
            'uuid': new_uuid,
            'name': name,
            'timezone': '',
            'age_group': 'Adult',
            'academic_year': '',
            'telegram': '',
            'is_minor': False,
            'parent_name': '',
            'school_name': '',
            'educational_goals': '',
            'behavioral_comments': '',
            'general_comments': '',
            'rate': 0,
            'birthdate': '',
            'teacher_id': TEACHER_UUID       # <-- assign teacher Lucky
        }

        # Add to index
        index_conn = open_index_db_with_key(data_dir, key)
        try:
            add_student_summary(
                index_conn,
                uuid=new_uuid,
                name=name,
                location='',
                rate=0,
                last_payment_date='',
                attendance_percentage=0.0,
                meeting_times_summary='',
                status='active',
                db_key=student_key
            )
        finally:
            close_index_db(index_conn)

        # Add meeting times to per‑student DB
        sconn = open_student_db(student_db_dir, new_uuid, student_key)
        try:
            save_profile(sconn, profile)
            for m in meets:
                add_meeting_time(
                    sconn,
                    name=m['nickname'],
                    day=m['day'],
                    time=m['time'],
                    mtype=m['type'],
                    is_in_person=False,
                    meeting_id=m['id']
                )
            sconn.commit()
        finally:
            sconn.close()

        print(f"Created student: {name} (uuid={new_uuid})")

    # ------------------------------------------------------------
    # Update all meetings:
    #   - set teacher_id = TEACHER_UUID
    #   - replace student_names with student UUIDs (keep names too)
    #   - assign package_id for private bundles
    # ------------------------------------------------------------
    print("\nUpdating meetings...")

    # Collect private meeting IDs per student
    private_by_student = {}
    for name, meets in student_meetings.items():
        private_ids = [m['id'] for m in meets if m['type'] == 'private' and len(m['student_names']) == 1]
        if len(private_ids) > 1:
            private_by_student[name] = private_ids

    for m in meetings:
        # Build new student_ids from the name‑to‑uuid map
        new_ids = []
        for raw_name in m['student_names']:
            name = raw_name.strip()
            if name and name in name_to_uuid:
                new_ids.append(name_to_uuid[name])

        if not new_ids:
            continue

        update_data = {
            'student_ids': new_ids,
            'teacher_id': TEACHER_UUID    # <-- assign teacher Lucky
        }

        if DRY_RUN:
            print(f"Would update meeting {m['id']} with student_ids={new_ids}")
        else:
            update_meeting(m['id'], update_data)

    # Assign package IDs to private bundles
    if not DRY_RUN:
        for name, ids in private_by_student.items():
            package_id = uuid.uuid4().hex
            for mid in ids:
                update_meeting(mid, {'package_id': package_id})

    print("Done.")

if __name__ == "__main__":
    main()