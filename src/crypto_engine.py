import os
import sys
import hashlib
import secrets
import getpass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Paths (will be set during unlock)
_salt_path = None
_encrypted_key_path = None

# In‑memory master key (bytes)
_master_key = None


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------
def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive 256‑bit key from password + salt using scrypt."""
    return hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32
    )


def _encrypt_key(master_key: bytes, password: str, salt: bytes) -> tuple[bytes, bytes, bytes]:
    """Encrypt master_key with a key derived from password + salt.
    Returns (ciphertext, nonce, salt)."""
    key = _derive_key(password, salt)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, master_key, None)
    return ciphertext, nonce, salt


def _decrypt_key(ciphertext: bytes, nonce: bytes, salt: bytes, password: str) -> bytes:
    """Decrypt master_key. Raises if wrong password."""
    key = _derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------
def setup_mep(data_dir: str, password: str):
    """First‑time setup: generate a master key, encrypt it with the MEP."""
    global _master_key

    os.makedirs(data_dir, exist_ok=True)
    _salt_path = os.path.join(data_dir, 'master_key.salt')
    _encrypted_key_path = os.path.join(data_dir, 'master_key.enc')

    salt = os.urandom(16)
    master_key = os.urandom(32)  # 256‑bit
    ciphertext, nonce, salt = _encrypt_key(master_key, password, salt)

    with open(_salt_path, 'wb') as f:
        f.write(salt)
    with open(_encrypted_key_path, 'wb') as f:
        f.write(nonce + ciphertext)

    _master_key = master_key


def unlock(data_dir: str):
    """Prompt for MEP, load and decrypt the master key. Exits on failure."""
    global _master_key, _salt_path, _encrypted_key_path

    _salt_path = os.path.join(data_dir, 'master_key.salt')
    _encrypted_key_path = os.path.join(data_dir, 'master_key.enc')

    if not os.path.exists(_salt_path) or not os.path.exists(_encrypted_key_path):
        print("\n🔐 First-time setup: Create a Master Encryption Password (MEP)")
        print("   This password encrypts all student and staff data.")
        while True:
            pw = getpass.getpass("Enter new MEP (min 6 chars): ")
            if len(pw) < 6:
                print("Too short, minimum 6 characters.")
                continue
            pw2 = getpass.getpass("Confirm MEP: ")
            if pw != pw2:
                print("Passwords don't match.")
                continue
            setup_mep(data_dir, pw)
            print("✅ MEP created and master key stored.")
            return

    # Normal unlock
    with open(_salt_path, 'rb') as f:
        salt = f.read()
    with open(_encrypted_key_path, 'rb') as f:
        data = f.read()
    nonce, ciphertext = data[:12], data[12:]

    print("\n🔓 Enter Master Encryption Password to unlock data:")
    for attempt in range(3):
        pw = getpass.getpass("MEP: ")
        try:
            _master_key = _decrypt_key(ciphertext, nonce, salt, pw)
            print("✅ Data unlocked.\n")
            return
        except Exception:
            print("Wrong password.")
    print("Too many attempts. Exiting.")
    sys.exit(1)


def verify_mep(data_dir: str, password: str) -> bool:
    """Check if a given password is the correct MEP (without storing the key)."""
    salt_path = os.path.join(data_dir, 'master_key.salt')
    enc_path = os.path.join(data_dir, 'master_key.enc')
    try:
        with open(salt_path, 'rb') as f:
            salt = f.read()
        with open(enc_path, 'rb') as f:
            data = f.read()
        nonce, ciphertext = data[:12], data[12:]
        _decrypt_key(ciphertext, nonce, salt, password)
        return True
    except Exception:
        return False


def get_master_key() -> bytes:
    """Return the in‑memory master key (must already be unlocked)."""
    if _master_key is None:
        raise RuntimeError("Master key not unlocked. Call unlock() first.")
    return _master_key
