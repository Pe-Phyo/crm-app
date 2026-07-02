import os
import hashlib
from typing import Tuple, Optional

from pysqlcipher3 import dbapi2 as sqlcipher


def generate_key() -> bytes:
    """Return a cryptographically random 256‑bit key."""
    return os.urandom(32)


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """Hash a password using scrypt. Returns (hash, salt)."""
    if salt is None:
        salt = os.urandom(16)
    derived = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32
    )
    return derived, salt


def verify_password(password: str, salt: bytes, stored_hash: bytes) -> bool:
    """Check a password against a stored scrypt hash."""
    new_hash, _ = hash_password(password, salt)
    return new_hash == stored_hash


def open_encrypted_db(path: str, key: bytes):
    """
    Open an existing encrypted database file with the given key.
    Raises ValueError if the key is wrong or the file is corrupt.
    """
    conn = sqlcipher.connect(path)
    _set_key(conn, key)
    # Verify the key by trying to read the schema
    try:
        conn.execute("SELECT count(*) FROM sqlite_master")
    except sqlcipher.DatabaseError:
        conn.close()
        raise ValueError("Wrong database key or file corrupted")
    return conn


def create_encrypted_db(path: str, key: bytes):
    """
    Create a new encrypted database file.
    Uses DELETE journal mode – safe on all filesystems, including vfat.
    """
    conn = sqlcipher.connect(path)
    _set_key(conn, key)
    # Force the file to be recognised as a valid SQLite database
    # (required on some filesystems like vfat before PRAGMA statements)
    conn.execute("CREATE TABLE IF NOT EXISTS _sqlcipher_init (id INTEGER PRIMARY KEY)")
    conn.execute("DROP TABLE IF EXISTS _sqlcipher_init")
    # Set journal mode to DELETE (WAL is incompatible with vfat)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def rekey_db(conn, new_key: bytes):
    """Change the encryption key of an already‑open database."""
    hex_key = new_key.hex()
    conn.execute(f"PRAGMA rekey = \"x'{hex_key}'\"")


def _set_key(conn, key: bytes):
    """Apply the encryption key to an SQLCipher connection."""
    hex_key = key.hex()
    conn.execute(f"PRAGMA key = \"x'{hex_key}'\"")