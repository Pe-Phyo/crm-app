import secrets
from datetime import datetime
from .staff_db import open_staff_db, get_profile, save_profile
from .index_db import open_staff_index, close_staff_index, get_staff_summary
from ..students.crypto import verify_password, hash_password
import os

def handle_change_own_password(root_data_dir, session, body):
    data = _parse_body(body)
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if len(new_pw) < 6:
        return {'error': 'New password too short'}, 400

    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, session['user_uuid'])
    finally:
        close_staff_index(index_conn)
    if not staff:
        return {'error': 'Staff not found'}, 404

    db_conn = open_staff_db(db_dir, session['user_uuid'], staff['db_key'])
    try:
        auth = get_profile(db_conn)
        if not verify_password(old_pw, auth['password_salt'], auth['password_hash']):
            return {'error': 'Incorrect old password'}, 403

        new_salt = secrets.token_bytes(16)
        new_hash, _ = hash_password(new_pw, new_salt)
        auth['password_salt'] = new_salt
        auth['password_hash'] = new_hash
        auth['password_last_changed'] = datetime.utcnow().isoformat()
        auth['must_change_password'] = False
        auth['updated_at'] = datetime.utcnow().isoformat()
        save_profile(db_conn, auth)
        return {'success': True}, 200
    finally:
        db_conn.close()

def _parse_body(body):
    import json
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}