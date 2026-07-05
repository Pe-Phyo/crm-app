#!/usr/bin/env python3
import sys
import os
import getpass

# Ensure we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))
sys.path.insert(0, os.path.dirname(__file__))

from src.crypto_engine import unlock, get_master_key, verify_mep
from src.staff.coordinator import StaffCoordinator

def main():
    root_data_dir = os.path.join(os.path.dirname(__file__), 'data')
    # Unlock the master encryption key (MEP)
    unlock(root_data_dir)

    coordinator = StaffCoordinator(root_data_dir)

    # Collect new admin details
    print("\nCreate initial admin user")
    username = input("Username (default: admin): ").strip() or "admin"
    password = getpass.getpass("Password: ")
    if len(password) < 6:
        print("Password too short (min 6).")
        sys.exit(1)
    full_name = input("Full name: ").strip()

    # Create (role=admin) - this bypasses authentication because it's local
    # We'll call the internal method directly
    import json
    body = json.dumps({
        "username": username,
        "password": password,
        "role": "admin",
        "full_name": full_name
    })
    result, status = coordinator._create_staff(body)
    print(f"Creation status {status}: {result}")
    if status != 201:
        print("Failed.")
        sys.exit(1)

    uuid = result.get('uuid')
    if not uuid:
        print("No UUID returned.")
        sys.exit(1)

    # Approve the admin (requires MEP again)
    # We'll verify MEP from the already unlocked key? Actually approval requires MEP re-entry.
    # We'll prompt again.
    mep = getpass.getpass("Enter MEP again to approve: ")
    if not verify_mep(root_data_dir, mep):
        print("Wrong MEP.")
        sys.exit(1)

    approve_body = json.dumps({"mep_password": mep})
    app_result, app_status = coordinator._approve_staff(uuid, approve_body)
    print(f"Approval status {app_status}: {app_result}")

    print(f"\n✅ Admin user '{username}' created and approved.")
    print(f"   You can now log in at https://localhost:8080/launch/index.html")

if __name__ == "__main__":
    main()
