import sys, os
sys.path.insert(0, 'libs')
from src.students.auth import login
from src.students.coordinator import StudentCoordinator

DATA_DIR = os.path.join(os.getcwd(), 'data', 'students')
coordinator = StudentCoordinator(DATA_DIR)

# Ask for master password
password = input("Master password: ")
token = login(DATA_DIR, password)
if not token:
    print("Wrong password")
    sys.exit(1)

# Get student list
headers = {'Authorization': f'Bearer {token}'}
data, status = coordinator.handle('GET', '/students', headers=headers)
if status != 200:
    print("Error fetching students:", data)
    sys.exit(1)

students = data
if not students:
    print("No students found. Add a student first.")
    sys.exit(1)

# Show the first student in detail
student = students[0]
print(f"\nStudent: {student['name']} (UUID: {student['uuid']})")
print(f"Meeting times summary: {student['meeting_times_summary']}")

# Fetch full profile to see meeting_times array
full, status = coordinator.handle('GET', f"/students/{student['uuid']}", headers=headers)
if status == 200 and 'meeting_times' in full:
    print("\nMeeting times details:")
    for mt in full['meeting_times']:
        print(f"  - Name: '{mt.get('name', 'MISSING')}', Day: {mt.get('day')}, Time: {mt.get('time')}, Type: {mt.get('type')}")
        if 'name' not in mt:
            print("    ^^^ 'name' field is MISSING from this meeting!")
else:
    print("Failed to get full profile:", full)