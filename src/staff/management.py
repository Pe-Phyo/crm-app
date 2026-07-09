import uuid
import os
from datetime import datetime
from .index_db import (
    open_staff_index, close_staff_index, get_all_staff, get_staff_summary,
    add_staff_summary, update_staff_active, delete_staff_summary
)
from .staff_db import create_staff_db, open_staff_db, get_profile, save_profile
from ..crypto_engine import verify_mep

def handle_list_staff(root_data_dir):
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_all_staff(index_conn)
        return staff, 200
    finally:
        close_staff_index(index_conn)

def handle_list_staff_detailed(root_data_dir):
    index_conn = open_staff_index(root_data_dir)
    try:
        all_staff = get_all_staff(index_conn)
        detailed = []
        db_dir = os.path.join(root_data_dir, 'staff', 'databases')
        for s in all_staff:
            staff_db = open_staff_db(db_dir, s['uuid'], s['db_key'])
            try:
                profile = get_profile(staff_db)
                for k in ('password_hash', 'password_salt'):
                    profile.pop(k, None)
                detailed.append(profile)
            finally:
                staff_db.close()
        return detailed, 200
    finally:
        close_staff_index(index_conn)

def handle_get_staff_detail(root_data_dir, uuid_str):
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, uuid_str)
        if not staff:
            return {'error': 'Not found'}, 404
        db_dir = os.path.join(root_data_dir, 'staff', 'databases')
        db_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
        try:
            profile = get_profile(db_conn)
            for k in ('password_hash', 'password_salt'):
                profile.pop(k, None)
            return profile, 200
        finally:
            db_conn.close()
    finally:
        close_staff_index(index_conn)

def handle_update_staff_profile(root_data_dir, uuid_str, body):
    data = _parse_body(body)
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, uuid_str)
    finally:
        close_staff_index(index_conn)
    if not staff:
        return {'error': 'Staff not found'}, 404
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    db_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
    try:
        profile = get_profile(db_conn)
                # Sensitive fields require MEP
        if 'is_active' in data or 'role' in data:
            mep = data.get('mep_password', '')
            if not mep or not verify_mep(root_data_dir, mep):
                return {'error': 'MEP required for role/status changes'}, 403
        for key in ['full_name', 'display_name', 'email', 'phone', 'timezone',
                    'default_hourly_rate', 'default_meeting_link_pattern', 'bio',
                    'role', 'is_active', 'payout_taxes_json', 'payment_methods_json']:
            if key in data:
                profile[key] = data[key]
        profile['updated_at'] = datetime.utcnow().isoformat()
        save_profile(db_conn, profile)
        return {'success': True}, 200
    finally:
        db_conn.close()

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
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    db_key = create_staff_db(db_dir, new_uuid)
    db_conn = open_staff_db(db_dir, new_uuid, db_key)
    try:
        from ..students.crypto import hash_password
        import secrets
        salt = secrets.token_bytes(16)
        pw_hash, _ = hash_password(password, salt)
        profile = {
            'uuid': new_uuid,
            'username': username,
            'full_name': full_name,
            'display_name': full_name,
            'email': '',
            'phone': '',
            'timezone': 'Asia/Yangon',
            'default_hourly_rate': 0,
            'default_meeting_link_pattern': '',
            'bio': '',
            'role': role,
            'is_active': False,
            'password_hash': pw_hash,
            'password_salt': salt,
            'password_last_changed': datetime.utcnow().isoformat(),
            'must_change_password': False,
            'payout_taxes_json': '{}',
            'payment_methods_json': '{}',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        save_profile(db_conn, profile)
    finally:
        db_conn.close()
    index_conn = open_staff_index(root_data_dir)
    try:
        add_staff_summary(index_conn, new_uuid, username, role, db_key, is_active=False)
    finally:
        close_staff_index(index_conn)
    return {'uuid': new_uuid}, 201

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
        db_dir = os.path.join(root_data_dir, 'staff', 'databases')
        db_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
        try:
            profile = get_profile(db_conn)
            profile['is_active'] = True
            save_profile(db_conn, profile)
        finally:
            db_conn.close()
        return {'success': True}, 200
    finally:
        close_staff_index(index_conn)

def handle_delete_staff(root_data_dir, uuid_str, body):
    data = _parse_body(body)
    mep_password = data.get('mep_password', '')
    if not verify_mep(root_data_dir, mep_password):
        return {'error': 'Invalid master encryption password'}, 403
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    db_path = os.path.join(db_dir, f"{uuid_str}.sqlite")
    if os.path.exists(db_path):
        os.remove(db_path)
    index_conn = open_staff_index(root_data_dir)
    try:
        delete_staff_summary(index_conn, uuid_str)
    finally:
        close_staff_index(index_conn)
    return {'success': True}, 200

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
    db_conn = open_staff_db(db_dir, uuid_str, staff['db_key'])
    try:
        from ..students.crypto import hash_password
        import secrets
        profile = get_profile(db_conn)
        salt = secrets.token_bytes(16)
        pw_hash, _ = hash_password(new_password, salt)
        profile['password_salt'] = salt
        profile['password_hash'] = pw_hash
        profile['password_last_changed'] = datetime.utcnow().isoformat()
        profile['must_change_password'] = True   # force change on next login
        save_profile(db_conn, profile)
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