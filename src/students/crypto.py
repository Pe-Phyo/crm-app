import os
import hashlib
import base64
from typing import Tuple, Optional

# SQLCipher
from pysqlcipher3 import dbapi2 as sqlcipher

# ------------------------------------------------------------
# Key generation
# ------------------------------------------------------------
def generate_key() -> bytes:
    """Generate a cryptographically random 256‑bit key."""
    return os.urandom(32)

# ------------------------------------------------------------
# Password hashing (using hashlib.scrypt)
# ------------------------------------------------------------
def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Hash a password with scrypt. Returns (hash, salt).
    If salt is None, a new random salt is generated.
    """
    if salt is None:
        salt = os.urandom(16)
    # scrypt parameters: N=2^14, r=8, p=1, dklen=32
    hash_bytes = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32
    )
    return hash_bytes, salt

def verify_password(password: str, salt: bytes, stored_hash: bytes) -> bool:
    """Verify a password against a stored scrypt hash."""
    new_hash, _ = hash_password(password, salt)
    return new_hash == stored_hash

# ------------------------------------------------------------
# Encrypted database helpers (SQLCipher)
# ------------------------------------------------------------
def open_encrypted_db(path: str, key: bytes):
    """
    Open a SQLCipher‑encrypted database with the given key.
    Returns a connection object.
    """
    # pysqlcipher3 uses a URI with ?key=... or PRAGMA key
    # The safest way: open without key, then execute PRAGMA key
    conn = sqlcipher.connect(path)
    # Convert key to hex string for PRAGMA (SQLCipher expects raw key as x'...')
    hex_key = key.hex()
    conn.execute(f"PRAGMA key = \"x'{hex_key}'\"")
    # Verify the key (optional but catches wrong keys early)
    try:
        conn.execute("SELECT count(*) FROM sqlite_master")
    except sqlcipher.DatabaseError:
        raise ValueError("Wrong database key or file corrupted")
    return conn

def create_encrypted_db(path: str, key: bytes):
    """Create a new encrypted database file."""
    conn = sqlcipher.connect(path)
    hex_key = key.hex()
    conn.execute(f"PRAGMA key = \"x'{hex_key}'\"")
    # Enable WAL mode and foreign keys for safety
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def rekey_db(conn, new_key: bytes):
    """Change the encryption key of an already‑open database."""
    hex_key = new_key.hex()
    conn.execute(f"PRAGMA rekey = \"x'{hex_key}'\"")