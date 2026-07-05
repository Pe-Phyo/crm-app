import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
from .index_db import get_staff_by_username, open_staff_index, close_staff_index
from .staff_db import open_staff_db, get_profile
from ..crypto_engine import get_master_key
from ..students.crypto import hash_password, verify_password

# In‑memory session store: token -> {user_uuid, role, last_used}
_sessions: Dict[str, dict] = {}
SESSION_EXPIRY_MINUTES = 60
PASSWORD_EXPIRY_DAYS = 30

def login(root_data_dir: str, username: str, password: str) -> Optional[Dict]:
    """Returns {token, role} or None."""
    print(f"[LOGIN] Attempting login for user: {username}")
    index_conn = open_staff_index(root_data_dir)
    try:
        staff = get_staff_by_username(index_conn, username)
        if not staff:
            print("[LOGIN] User not found in index")
            return None
        print(f"[LOGIN] Found staff: {staff['uuid']}, active: {staff['is_active']}")
        if not staff['is_active']:
            print("[LOGIN] Staff is inactive")
            return None
        db_key = staff['db_key']
        staff_db_dir = os.path.join(root_data_dir, 'staff', 'databases')
        os.makedirs(staff_db_dir, exist_ok=True)
        print(f"[LOGIN] Opening staff DB at {staff_db_dir}/{staff['uuid']}.sqlite")
        db_conn = open_staff_db(staff_db_dir, staff['uuid'], db_key)
        try:
            profile = get_profile(db_conn)
            print(f"[LOGIN] Profile loaded, username: {profile.get('username')}")
            if not verify_password(password, profile['password_salt'], profile['password_hash']):
                print("[LOGIN] Password mismatch")
                return None
            # Check password expiry
            last_changed = datetime.fromisoformat(profile['password_last_changed'])
            if (datetime.utcnow() - last_changed).days >= PASSWORD_EXPIRY_DAYS:
                print("[LOGIN] Password expired, but allowing login for now")
                # (we'll handle in the response later)
            token = secrets.token_urlsafe(32)
            _sessions[token] = {
                'user_uuid': staff['uuid'],
                'role': staff['role'],
                'last_used': datetime.utcnow()
            }
            print(f"[LOGIN] Success, token: {token[:10]}...")
            return {'token': token, 'role': staff['role'], 'uuid': staff['uuid']}
        except Exception as e:
            print(f"[LOGIN] Error reading staff DB: {e}")
            return None
        finally:
            db_conn.close()
    except Exception as e:
        print(f"[LOGIN] Index error: {e}")
        return None
    finally:
        close_staff_index(index_conn)

def verify_session(token: str) -> Optional[Dict]:
    """Return session dict if valid, else None."""
    if token in _sessions:
        sess = _sessions[token]
        now = datetime.utcnow()
        if now - sess['last_used'] > timedelta(minutes=SESSION_EXPIRY_MINUTES):
            del _sessions[token]
            return None
        sess['last_used'] = now
        return sess
    return None

def logout(token: str):
    if token in _sessions:
        del _sessions[token]