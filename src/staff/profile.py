import secrets
from datetime import datetime
from .staff_db import get_profile, save_profile, get_availability, set_availability, get_holidays, set_holidays
from .index_db import open_staff_index, close_staff_index, get_staff_summary
from ..students.crypto import verify_password, hash_password
import os

def handle_own_profile(root_data_dir, session):
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, session['user_uuid'])
    finally:
        close_staff_index(index_conn)
    if not staff:
        return {'error': 'Staff not found'}, 404
    db_conn = open_staff_db_util(db_dir, session['user_uuid'], staff['db_key'])
    try:
        profile = get_profile(db_conn)
        for k in ('password_hash', 'password_salt'):
            profile.pop(k, None)
        return profile, 200
    finally:
        db_conn.close()

def handle_update_own_profile(root_data_dir, session, body):
    data = _parse_body(body)
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, session['user_uuid'])
    finally:
        close_staff_index(index_conn)
    if not staff:
        return {'error': 'Staff not found'}, 404
    db_conn = open_staff_db_util(db_dir, session['user_uuid'], staff['db_key'])
    try:
        profile = get_profile(db_conn)
        for key in ['full_name', 'display_name', 'email', 'phone', 'timezone',
                    'default_hourly_rate', 'default_meeting_link_pattern', 'bio',
                    'payout_taxes_json', 'payment_methods_json']:
            if key in data:
                profile[key] = data[key]
        profile['updated_at'] = datetime.utcnow().isoformat()
        save_profile(db_conn, profile)
        return {'success': True}, 200
    finally:
        db_conn.close()

def handle_own_availability(root_data_dir, session, method, body=None):
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, session['user_uuid'])
    finally:
        close_staff_index(index_conn)
    if not staff:
        return {'error': 'Staff not found'}, 404
    db_conn = open_staff_db_util(db_dir, session['user_uuid'], staff['db_key'])
    try:
        if method == 'GET':
            return get_availability(db_conn), 200
        data = _parse_body(body)
        slots = data.get('slots', [])
        if session['role'] != 'admin':
            for s in slots:
                s['status'] = 'pending'
        set_availability(db_conn, slots)
        return {'success': True}, 200
    finally:
        db_conn.close()

def handle_own_holidays(root_data_dir, session, method, body=None):
    db_dir = os.path.join(root_data_dir, 'staff', 'databases')
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_summary(index_conn, session['user_uuid'])
    finally:
        close_staff_index(index_conn)
    if not staff:
        return {'error': 'Staff not found'}, 404
    db_conn = open_staff_db_util(db_dir, session['user_uuid'], staff['db_key'])
    try:
        if method == 'GET':
            return get_holidays(db_conn), 200
        data = _parse_body(body)
        holidays = data.get('holidays', [])
        if session['role'] != 'admin':
            for h in holidays:
                h['status'] = 'pending'
        set_holidays(db_conn, holidays)
        return {'success': True}, 200
    finally:
        db_conn.close()

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
    db_conn = open_staff_db_util(db_dir, session['user_uuid'], staff['db_key'])
    try:
        profile = get_profile(db_conn)
        if not verify_password(old_pw, profile['password_salt'], profile['password_hash']):
            return {'error': 'Incorrect old password'}, 403
        new_salt = secrets.token_bytes(16)
        new_hash, _ = hash_password(new_pw, new_salt)
        profile['password_salt'] = new_salt
        profile['password_hash'] = new_hash
        profile['password_last_changed'] = datetime.utcnow().isoformat()
        profile['must_change_password'] = False
        save_profile(db_conn, profile)
        return {'success': True}, 200
    finally:
        db_conn.close()

# ---- helpers (can be shared via a small utils file later) ----
def _parse_body(body):
    import json
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}

def open_staff_db_util(db_dir, uuid_str, key):
    from .staff_db import open_staff_db
    return open_staff_db(db_dir, uuid_str, key)