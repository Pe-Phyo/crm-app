#!/usr/bin/env python3
import sys, os, getpass, json, shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))
sys.path.insert(0, os.path.dirname(__file__))

from src.crypto_engine import unlock, get_master_key, verify_mep
from src.staff.index_db import create_staff_index
from src.staff.management import handle_create_staff, handle_approve_staff

ROOT_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def main():
    # Unlock MEP
    unlock(ROOT_DATA_DIR)

    # Wipe old staff files
    staff_dir = os.path.join(ROOT_DATA_DIR, 'staff')
    if os.path.exists(staff_dir):
        shutil.rmtree(staff_dir)
        print("Old staff data deleted.")

    # Recreate fresh staff index
    create_staff_index(ROOT_DATA_DIR)

    # Create admin with known password
    username = "admin"
    password = "admin123"
    full_name = "Administrator"
    body = json.dumps({
        "username": username,
        "password": password,
        "role": "admin",
        "full_name": full_name
    })
    result, status = handle_create_staff(ROOT_DATA_DIR, body)
    if status != 201:
        print("Creation failed:", result)
        sys.exit(1)

    uuid = result['uuid']
    # Approve with MEP
    mep = getpass.getpass("Enter MEP one more time to approve admin: ")
    if not verify_mep(ROOT_DATA_DIR, mep):
        print("Wrong MEP.")
        sys.exit(1)
    app_body = json.dumps({"mep_password": mep})
    app_result, app_status = handle_approve_staff(ROOT_DATA_DIR, uuid, app_body)
    if app_status == 200:
        print(f"✅ Admin created and approved.")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Login at: https://localhost:8080/launch/index.html")
    else:
        print("Approval failed:", app_result)

if __name__ == "__main__":
    main()