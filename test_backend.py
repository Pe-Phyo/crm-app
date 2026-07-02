import sys
import os
import shutil
import json

# Point to portable libraries
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

from src.students.coordinator import StudentCoordinator

# Use a temporary data directory for testing
TEST_DATA_DIR = "/tmp/student_test_data"

# Clean up any previous test run
if os.path.exists(TEST_DATA_DIR):
    shutil.rmtree(TEST_DATA_DIR)
os.makedirs(TEST_DATA_DIR)

coordinator = StudentCoordinator(TEST_DATA_DIR)

def call(method, path, body=None, token=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    # Simulate HTTP body as JSON string
    body_str = json.dumps(body) if body else None
    data, status = coordinator.handle(method, path, body_str, headers)
    return data, status

print("1. Setup master password...")
data, status = call('POST', '/auth/setup', {'password': 'testpassword123'})
assert status == 200, f"Setup failed: {data}"
print("   OK")

print("2. Login...")
data, status = call('POST', '/auth/login', {'password': 'testpassword123'})
assert status == 200, f"Login failed: {data}"
token = data['token']
print("   OK, got token")

print("3. Create a student...")
student_data = {
    'name': 'Mg Mg',
    'location': 'Yangon',
    'rate': 15000,
    'phone': '09123456789',
    'telegram': '@mgmg',
    'email': 'mgmg@example.com',
    'is_minor': False,
    'age_group': 'young adult',
    'timezone': 'Asia/Yangon',
    'meeting_times': [
        {'day': 'Monday', 'time': '09:00', 'type': 'private', 'is_in_person': False},
        {'day': 'Wednesday', 'time': '15:00', 'type': 'group', 'is_in_person': False}
    ]
}
data, status = call('POST', '/students', student_data, token)
assert status == 201, f"Create failed: {data}"
student_uuid = data['uuid']
print(f"   OK, created UUID {student_uuid}")

print("4. List students...")
data, status = call('GET', '/students', token=token)
assert status == 200, f"List failed: {data}"
assert len(data) == 1
print(f"   OK, found {len(data)} student(s)")

print("5. Get student profile...")
data, status = call('GET', f'/students/{student_uuid}', token=token)
assert status == 200, f"Get failed: {data}"
assert data['name'] == 'Mg Mg'
print("   OK, name matches")

print("6. Update student...")
update = {'name': 'Mg Mg (updated)', 'rate': 16000}
data, status = call('PUT', f'/students/{student_uuid}', update, token)
assert status == 200, f"Update failed: {data}"
data, status = call('GET', f'/students/{student_uuid}', token=token)
assert data['name'] == 'Mg Mg (updated)'
print("   OK")

print("7. Add attendance...")
att = {'date': '2026-07-01', 'status': 'present'}
data, status = call('POST', f'/students/{student_uuid}/attendance', att, token)
assert status == 201, f"Add attendance failed: {data}"
att_id = data['id']
# check attendance percentage
data, status = call('GET', f'/students/{student_uuid}', token=token)
assert data['attendance_percentage'] == 100.0
print(f"   OK, attendance 100%")

print("8. Update attendance...")
data, status = call('PUT', f'/students/{student_uuid}/attendance/{att_id}', {'status': 'absent'}, token)
assert status == 200
data, status = call('GET', f'/students/{student_uuid}', token=token)
assert data['attendance_percentage'] == 0.0
print("   OK, attendance changed to 0%")

print("9. Add payment...")
payment = {'date': '2026-06-25', 'amount': 50000}
data, status = call('POST', f'/students/{student_uuid}/payments', payment, token)
assert status == 201
# check list payments
data, status = call('GET', f'/students/{student_uuid}/payments', token=token)
assert len(data) == 1 and data[0]['amount'] == 50000
print("   OK")

print("10. Action items...")
data, status = call('POST', '/actions', {'text': 'Follow up payment'}, token)
assert status == 201
action_id = data['id']
data, status = call('GET', '/actions', token=token)
assert len(data) == 1
print("   OK, action created")

data, status = call('PUT', f'/actions/{action_id}', {'done': True}, token)
assert status == 200
data, status = call('GET', '/actions', token=token)
assert data[0]['done'] == True
print("   OK, action marked done")

print("11. Delete student...")
data, status = call('DELETE', f'/students/{student_uuid}', token=token)
assert status == 200
data, status = call('GET', '/students', token=token)
assert len(data) == 0
print("   OK, student deleted")

# Clean up test directory
shutil.rmtree(TEST_DATA_DIR)
print("\n✅ All backend tests passed!")