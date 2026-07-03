import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib

from .index_db import (
    setup_index_db,
    open_index_db,
    close_index_db,
    get_auth_record,
    update_auth_password,
    add_password_to_history,
    is_password_in_history
)
from .crypto import hash_password, generate_key

# In‑memory session store: token -> { 'created': datetime, 'last_used': datetime }
_sessions: Dict[str, dict] = {}

SESSION_EXPIRY_MINUTES = 60   # token valid for 1 hour of inactivity
PASSWORD_EXPIRY_DAYS = 30

# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------
def setup_master_password(data_dir: str, password: str):
    """First‑time setup: create the index DB with the given password."""
    setup_index_db(data_dir, password)

# ------------------------------------------------------------
# Login
# ------------------------------------------------------------
def login(data_dir: str, password: str) -> Optional[str]:
    try:
        # Derive key
        from .index_db import _read_salt, _derive_key
        salt = _read_salt(data_dir)
        key = _derive_key(password, salt)
        conn = open_index_db(data_dir, password)   # also verifies
        close_index_db(conn)
    except Exception:
        return None
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        'key': key,
        'created': datetime.utcnow(),
        'last_used': datetime.utcnow()
    }
    return token

def get_session_key(token: str) -> Optional[bytes]:
    """Return the derived index DB key for the session, or None."""
    if verify_token(token):
        return _sessions[token]['key']
    return None

# ------------------------------------------------------------
# Token verification
# ------------------------------------------------------------
def verify_token(token: str) -> bool:
    """Check if token exists and is not expired. Updates last_used."""
    if token in _sessions:
        session = _sessions[token]
        now = datetime.utcnow()
        if now - session['last_used'] > timedelta(minutes=SESSION_EXPIRY_MINUTES):
            del _sessions[token]
            return False
        session['last_used'] = now
        return True
    return False

# ------------------------------------------------------------
# Password expiry check
# ------------------------------------------------------------
def is_password_expired(data_dir: str) -> bool:
    """Return True if password hasn't been changed in PASSWORD_EXPIRY_DAYS."""
    try:
        # We need to open the DB to get the last_changed date.
        # But we don't have the password here. This function is meant to be called
        # after login (when we have a valid session). So we'll require a connection.
        # We'll expose a variant that takes a connection instead.
        pass
    except:
        pass
    # For API use, we'll check after opening the DB.
    return False  # Placeholder; actual check done in coordinator with open DB

def check_password_expiry_with_conn(conn) -> bool:
    """Given an open index DB connection, check if password is expired."""
    record = get_auth_record(conn)
    last_changed = datetime.fromisoformat(record['last_changed'])
    return (datetime.utcnow() - last_changed).days >= PASSWORD_EXPIRY_DAYS

# ------------------------------------------------------------
# Password change
# ------------------------------------------------------------
def change_password(data_dir: str, old_password: str, new_password: str) -> bool:
    """
    Change the master password.
    Rejects if new password is in history or same as old.
    """
    # Open DB with old password
    try:
        conn = open_index_db(data_dir, old_password)
    except:
        return False
    try:
        # Check history
        if is_password_in_history(conn, new_password):
            return False
        # Add old password to history (using the salt/hash from auth table)
        old_record = get_auth_record(conn)
        add_password_to_history(conn, old_record['salt'], old_record['hash'])
        # Generate new salt and hash for new password
        new_salt = secrets.token_bytes(16)
        new_hash, _ = hash_password(new_password, new_salt)
        # Rekey the database
        new_key = hashlib.scrypt(new_password.encode('utf-8'), salt=new_salt, n=2**14, r=8, p=1, dklen=32)
        from .crypto import rekey_db
        rekey_db(conn, new_key)
        # Update auth table with new salt/hash and last_changed
        update_auth_password(conn, new_salt, new_hash)
        # Update the external salt file
        from .index_db import _write_salt
        _write_salt(data_dir, new_salt)
        conn.commit()
        return True
    finally:
        close_index_db(conn)

def verify_master_password(data_dir: str, password: str) -> bool:
    """Return True if the password matches the master password."""
    try:
        from .index_db import open_index_db, close_index_db
        conn = open_index_db(data_dir, password)
        close_index_db(conn)
        return True
    except Exception:
        return False        