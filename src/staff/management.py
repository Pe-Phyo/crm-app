import uuid
import os
from datetime import datetime
from .index_db import (
    open_staff_index, close_staff_index, get_all_staff, get_staff_summary,
    add_staff_summary, update_staff_active, delete_staff_summary,
    update_staff_profile_key
)
from .staff_db import create_staff_db, open_staff_db, get_profile, save_profile
from ..crypto_engine import verify_mep
from ..profiles.db import (
    create_profile_db, open_profile_db,
    get_profile_details, save_profile_details,
    get_phones, set_phones,
    get_emails, set_emails,
)
from ..students.crypto import hash_password
import secrets

def _parse_body(body):
    import json
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}

def _open_profile_db_for_staff(root_data_dir, uuid_str):
    """Utility to open the profile DB for a staff member."""
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, uuid_str)
    finally:
        close_staff_index(index_conn)
    if not staff or not staff.get('profile_db_key'):
        return None
    profile_data_dir = os.path.join(root_data_dir, 'data', 'profiles')
    return open_profile_db(profile_data_dir, uuid_str, staff['profile_db_key'])

# -------------------------------------------------------------------
# List staff (basic) – unchanged, index only
# -------------------------------------------------------------------
def handle_list_staff(root_data_dir):
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_all_staff(index_conn)
        return staff, 200
    finally:
        close_staff_index(index_conn)

# -------------------------------------------------------------------
# List staff detailed – now uses profile DB for identity
# -------------------------------------------------------------------
def handle_list_staff_detailed(root_data_dir):
    index_conn = open_staff_index(root_data_dir)
    try:
        all_staff = get_all_staff(index_conn)
        detailed = []
        for s in all_staff:
            # Open staff DB for auth (role, is_active)
            db_dir = os.path.join(root_data_dir, 'staff', 'databases')
            staff_conn = open_staff_db(db_dir, s['uuid'], s['db_key'])
            try:
                auth = get_profile(staff_conn)
            finally:
                staff_conn.close()

            # Open profile DB for identity
            profile_conn = _open_profile_db_for_staff(root_data_dir, s['uuid'])
            identity = {}
            if profile_conn:
                try:
                    identity = get_profile_details(profile_conn)
                    identity['phones'] = get_phones(profile_conn)
                    identity['emails'] = get_emails(profile_conn)
                finally:
                    profile_conn.close()

            detailed.append({
                'uuid': s['uuid'],
                'username': auth['username'],
                'role': auth['role'],
                'is_active': auth['is_active'],
                'full_name': identity.get('full_name', ''),
                'display_name': identity.get('display_name', ''),
                'email': identity.get('email', ''),
                'phone': identity.get('phone', ''),
                'timezone': identity.get('timezone', ''),
                'default_hourly_rate': identity.get('default_hourly_rate', 0),
                'bio': identity.get('bio', ''),
                'phones': identity.get('phones', []),
                'emails': identity.get('emails', []),
            })
        return detailed, 200
    finally:
        close_staff_index(index_conn)

# -------------------------------------------------------------------
# Get single staff detail – uses profile DB for identity
# -------------------------------------------------------------------
def handle_get_staff_detail(root_data_dir, uuid_str):
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, uuid_str)
    finally:
        close_staff_index(index_conn)
    if not staff:
        return {'error': 'Not found'}, 404

    # Auth from staff DB
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    staff_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
    try:
        auth = get_profile(staff_conn)
    finally:
        staff_conn.close()

    # Identity from profile DB
    profile_conn = _open_profile_db_for_staff(root_data_dir, uuid_str)
    identity = {}
    if profile_conn:
        try:
            identity = get_profile_details(profile_conn)
            identity['phones'] = get_phones(profile_conn)
            identity['emails'] = get_emails(profile_conn)
        finally:
            profile_conn.close()

    return {
        'uuid': uuid_str,
        'username': auth['username'],
        'role': auth['role'],
        'is_active': auth['is_active'],
        'full_name': identity.get('full_name', ''),
        'display_name': identity.get('display_name', ''),
        'email': identity.get('email', ''),
        'phone': identity.get('phone', ''),
        'timezone': identity.get('timezone', ''),
        'default_hourly_rate': identity.get('default_hourly_rate', 0),
        'bio': identity.get('bio', ''),
        'phones': identity.get('phones', []),
        'emails': identity.get('emails', []),
    }, 200

# -------------------------------------------------------------------
# Update staff profile (admin/back‑office) – split identity/auth
# -------------------------------------------------------------------
def handle_update_staff_profile(root_data_dir, uuid_str, body):
    data = _parse_body(body)
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, uuid_str)
    finally:
        close_staff_index(index_conn)
    if not staff:
        return {'error': 'Staff not found'}, 404

    # Sensitive fields require MEP
    if 'is_active' in data or 'role' in data:
        mep = data.get('mep_password', '')
        if not mep or not verify_mep(root_data_dir, mep):
            return {'error': 'MEP required for role/status changes'}, 403

    # Update auth fields in staff DB
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    staff_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
    try:
        auth = get_profile(staff_conn)
        if 'role' in data:
            auth['role'] = data['role']
        if 'is_active' in data:
            auth['is_active'] = data['is_active']
        auth['updated_at'] = datetime.utcnow().isoformat()
        save_profile(staff_conn, auth)
    finally:
        staff_conn.close()

    # Sync the staff index so login / teacher list reflect changes
    index_conn2 = open_staff_index(root_data_dir)
    try:
        if 'is_active' in data:
            update_staff_active(index_conn2, uuid_str, data['is_active'])
        if 'role' in data:
            # Role changes also need to be reflected in the index
            index_conn2.execute("UPDATE staff SET role = ? WHERE uuid = ?", (data['role'], uuid_str))
            index_conn2.commit()
    finally:
        close_staff_index(index_conn2)

    # Update identity fields in profile DB
    profile_conn = _open_profile_db_for_staff(root_data_dir, uuid_str)
    if profile_conn:
        try:
            details = get_profile_details(profile_conn)
            identity_fields = [
                'full_name', 'display_name', 'email', 'phone', 'timezone',
                'default_hourly_rate', 'default_meeting_link_pattern', 'bio',
                'languages'
            ]
            for key in identity_fields:
                if key in data:
                    details[key] = data[key]
            details['updated_at'] = datetime.utcnow().isoformat()
            save_profile_details(profile_conn, details)

            if 'phones' in data:
                set_phones(profile_conn, data['phones'])
            if 'emails' in data:
                set_emails(profile_conn, data['emails'])
        finally:
            profile_conn.close()

    return {'success': True}, 200

# -------------------------------------------------------------------
# Create staff – staff DB (auth) + profile DB (identity)
# -------------------------------------------------------------------
def handle_create_staff(root_data_dir, body):
    data = _parse_body(body)
    username = data.get('username', '')
    role = data.get('role', 'teacher')
    full_name = data.get('full_name', '')
    password = data.get('password', '')
    if not username or not password:
        return {'error': 'username and password required'}, 400
    if role not in ['admin', 'teacher', 'front_office', 'back_office', 'bot']:
        return {'error': 'Invalid role'}, 400

    new_uuid = uuid.uuid4().hex

    # 1. Create staff DB (auth only)
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    staff_db_key = create_staff_db(db_dir, new_uuid)
    staff_conn = open_staff_db(db_dir, new_uuid, staff_db_key)
    try:
        salt = secrets.token_bytes(16)
        pw_hash, _ = hash_password(password, salt)
        auth_record = {
            'uuid': new_uuid,
            'username': username,
            'role': role,
            'is_active': False,
            'password_hash': pw_hash,
            'password_salt': salt,
            'password_last_changed': datetime.utcnow().isoformat(),
            'must_change_password': False,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        save_profile(staff_conn, auth_record)
    finally:
        staff_conn.close()

    # 2. Create profile DB (identity)
    profile_data_dir = os.path.join(root_data_dir, 'data', 'profiles')
    profile_db_key = create_profile_db(profile_data_dir, new_uuid)
    profile_conn = open_profile_db(profile_data_dir, new_uuid, profile_db_key)
    try:
        details = {
            'uuid': new_uuid,
            'full_name': full_name,
            'display_name': full_name,
            'email': '',
            'phone': '',
            'timezone': 'Asia/Yangon',
            'default_hourly_rate': 0,
            'default_meeting_link_pattern': '',
            'bio': '',
            'languages': '[]',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        save_profile_details(profile_conn, details)
    finally:
        profile_conn.close()

    # 3. Add to staff index (with both keys)
    index_conn = open_staff_index(root_data_dir)
    try:
        add_staff_summary(index_conn, new_uuid, username, role, staff_db_key, is_active=False)
        update_staff_profile_key(index_conn, new_uuid, profile_db_key)
    finally:
        close_staff_index(index_conn)

    return {'uuid': new_uuid}, 201

# -------------------------------------------------------------------
# Approve staff – set is_active in auth, profile DB already exists
# -------------------------------------------------------------------
def handle_approve_staff(root_data_dir, uuid_str, body):
    data = _parse_body(body)
    mep_password = data.get('mep_password', '')
    if not verify_mep(root_data_dir, mep_password):
        return {'error': 'Invalid master encryption password'}, 403

    index_conn = open_staff_index(root_data_dir)
    try:
        update_staff_active(index_conn, uuid_str, True)
        staff = get_staff_summary(index_conn, uuid_str)
        if not staff:
            return {'error': 'Staff not found'}, 404

        # Activate in staff DB
        db_dir = os.path.join(root_data_dir, 'staff', 'databases')
        staff_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
        try:
            auth = get_profile(staff_conn)
            auth['is_active'] = True
            auth['updated_at'] = datetime.utcnow().isoformat()
            save_profile(staff_conn, auth)
        finally:
            staff_conn.close()

        return {'success': True}, 200
    finally:
        close_staff_index(index_conn)

# -------------------------------------------------------------------
# Delete staff – remove both DB files and index entry
# -------------------------------------------------------------------
def handle_delete_staff(root_data_dir, uuid_str, body):
    data = _parse_body(body)
    mep_password = data.get('mep_password', '')
    if not verify_mep(root_data_dir, mep_password):
        return {'error': 'Invalid master encryption password'}, 403

    # Delete staff DB file
    staff_db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    staff_db_path = os.path.join(staff_db_dir, f"{uuid_str}.sqlite")
    if os.path.exists(staff_db_path):
        os.remove(staff_db_path)

    # Delete profile DB file
    profile_db_dir = os.path.join(root_data_dir, 'data', 'profiles')
    profile_db_path = os.path.join(profile_db_dir, f"{uuid_str}.sqlite")
    if os.path.exists(profile_db_path):
        os.remove(profile_db_path)

    # Remove from index
    index_conn = open_staff_index(root_data_dir)
    try:
        delete_staff_summary(index_conn, uuid_str)
    finally:
        close_staff_index(index_conn)

    return {'success': True}, 200

# -------------------------------------------------------------------
# List teachers – unchanged (index only)
# -------------------------------------------------------------------
def handle_list_teachers(root_data_dir):
    index_conn = open_staff_index(root_data_dir)
    try:
        all_staff = get_all_staff(index_conn)
        teachers = [{
            'uuid': s['uuid'],
            'display_name': s.get('display_name', s['username'])
        } for s in all_staff if s.get('role') == 'teacher' and s.get('is_active')]
        return teachers, 200
    finally:
        close_staff_index(index_conn)

# -------------------------------------------------------------------
# Reset staff password – auth only, stays in staff DB
# -------------------------------------------------------------------
def handle_reset_staff_password(root_data_dir, uuid_str, body):
    data = _parse_body(body)
    new_password = data.get('new_password', '')
    mep_password = data.get('mep_password', '')
    if not mep_password:
        return {'error': 'Master encryption password required'}, 400
    if not verify_mep(root_data_dir, mep_password):
        return {'error': 'Invalid master encryption password'}, 403
    if len(new_password) < 6:
        return {'error': 'New password too short'}, 400

    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, uuid_str)
    finally:
        close_staff_index(index_conn)
    if not staff:
        return {'error': 'Staff not found'}, 404

    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    staff_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
    try:
        auth = get_profile(staff_conn)
        salt = secrets.token_bytes(16)
        pw_hash, _ = hash_password(new_password, salt)
        auth['password_salt'] = salt
        auth['password_hash'] = pw_hash
        auth['password_last_changed'] = datetime.utcnow().isoformat()
        auth['must_change_password'] = True
        auth['updated_at'] = datetime.utcnow().isoformat()
        save_profile(staff_conn, auth)
        return {'success': True}, 200
    finally:
        staff_conn.close()