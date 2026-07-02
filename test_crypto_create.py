import sys, os
sys.path.insert(0, 'libs')
from pysqlcipher3 import dbapi2 as sqlcipher
import tempfile

# Use a path on the thumb drive (same filesystem as your data/students/)
TEST_DB = os.path.join(os.getcwd(), 'data', 'students', '_test_create.db')

# Clean up any previous test
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

print(f"1. Target file: {TEST_DB}")
print(f"   Directory exists: {os.path.isdir(os.path.dirname(TEST_DB))}")
print(f"   Filesystem type: ", end="")
# Quick check filesystem type (optional)
try:
    import subprocess
    out = subprocess.check_output(['df', '-T', TEST_DB]).decode()
    print(out.splitlines()[-1].split()[1])
except:
    print("unknown")

key = os.urandom(32)
hex_key = key.hex()

print("\n2. Trying to connect and set key...")
conn = sqlcipher.connect(TEST_DB)
try:
    conn.execute(f"PRAGMA key = \"x'{hex_key}'\"")
    print("   PRAGMA key OK")
except Exception as e:
    print(f"   FAILED: {e}")
    conn.close()
    sys.exit(1)

print("3. Trying a minimal CREATE TABLE...")
try:
    conn.execute("CREATE TABLE IF NOT EXISTS _test (x INTEGER)")
    print("   CREATE TABLE OK")
except Exception as e:
    print(f"   FAILED: {e}")
    conn.close()
    sys.exit(1)

print("4. Trying DROP TABLE...")
try:
    conn.execute("DROP TABLE IF EXISTS _test")
    print("   DROP TABLE OK")
except Exception as e:
    print(f"   FAILED: {e}")
    conn.close()
    sys.exit(1)

print("5. Setting journal_mode=DELETE...")
try:
    conn.execute("PRAGMA journal_mode=DELETE")
    print("   PRAGMA journal_mode OK")
except Exception as e:
    print(f"   FAILED: {e}")
    conn.close()
    sys.exit(1)

conn.commit()
conn.close()
print("\n✅ All steps passed! Clean encrypted DB created.")
os.remove(TEST_DB)