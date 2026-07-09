# CRM App – Meeting Launcher & Student Manager

A lightweight, privacy-focused CRM for teachers with limited internet connectivity.  
Runs entirely from a USB thumb drive, stores data in encrypted SQLite databases, and works offline.

---

## Project Overview

This modular CRM handles:

- Meeting Launcher: one-click Jitsi join with low-bandwidth settings
- Student Management: secure, encrypted client profiles with attendance, payments, and notes
- Staff & Role Management: multi-user system with role-based dashboards
- Dashboard System: unified shell with six role-specific dashboards, lazy‑loaded widgets, and “View” menu
- Database Storage: SQLite / SQLCipher on thumb drive
- Future: Telegram bot, OCR receipt scanning, teacher profile, analytics, automation

---

## Current Features

### Meeting Launcher
- One-click Jitsi joining (Brave browser, no extra clicks)
- Low bandwidth by default (video off, mic off, skip pre-join)
- Vertical weekly calendar, current day on top
- Current meeting highlighted in green, upcoming in yellow
- Private and group classes (group maximum 9 students)
- Per-meeting countdown tracker (lessons remaining), rate (MMK), homework, comments
- Add/remove students per meeting (free-text student names)
- SQLite database storage
- Works offline

### Student Manager (Phase 2 – active development)
- Master Encryption Password (MEP) entered once at server start to unlock all data
- Encrypted central index database (SQLCipher)
- Individual per-student encrypted databases (one `.sqlite` file per student)
- Student list panel with search and filters (status, rate range, payment status)
- Add/Edit student form with:
  - Full name, **birthdate**, age group, timezone (selected from worldwide list)
  - **Teacher assignment** – dropdown of active teachers
  - Multi-value phone numbers and email addresses (dynamic add/remove)
  - Telegram handle
  - Conditional minor section: parent/guardian details, school, grade
  - Multi-day meeting times with meeting name, day, time, type, in‑person flag, meeting link
  - **Group meeting selector** – when type is “Group”, choose from existing groups or create new
  - Link to other students (family/siblings) with relationship type and invoice grouping toggle
  - Rate per lesson (MMK)
  - Educational goals and general comments
- **Meetings automatically created** when a student is added – they appear immediately in the teacher’s dashboard and attendance widget
- Student detail view showing all stored information, including attendance log, payment records, linked students
- Global action items / to-do list (add, toggle, delete)
- Password-protected student deletion (requires MEP re-entry)
- All student data encrypted at rest

### Dashboard System (new – Phase 2 milestone)
- **Unified shell** (`dashboard.html`) that loads a role‑specific configuration
- Six dashboards: **Admin**, **Teacher**, **Front Office**, **Back Office**, **Bot**, and **System & Dev**
- Each dashboard defines which widgets appear in the left column (35%), right column (65%), and bottom tab area
- **Widgets are loaded lazily and securely** – no widget code is sent to the browser until the user is authenticated, and only the widgets needed for the current role are loaded
- **“View” menu** (eye icon) in the top bar:
  - Admin can switch to any other role’s dashboard and back
  - Other roles have placeholder menu items for future actions (e.g., Student View, Meetings View)
- Built‑in widgets include:
  - **Upcoming Dates** – holidays, exams, and eventually birthdays (timeline rules: school holidays 1 month, public holidays 1 month, exams 2 months out)
  - **Student Highlights** – active count, top loyalty (static for now)
  - **Meetings** (teacher right column) – day picker, today’s meetings with homework/comments, no edit/delete in dashboard
  - **Attendance** (teacher left column) – list of students with meetings today, checkbox to mark present/absent
  - **Inbox** (bottom tab for all roles) – shared action items (Eisenhower matrix tinting planned)
  - **Build Status** (admin/dev) – placeholder for system health
  - **Payments Summary**, **Bot Health**, **Agent Health**, **Messages**, **Financial Overview**, etc. – stubs for future work
- Front‑office “Student View” menu item links directly to the student creation page
- No duplicated CSS – the dashboard reuses the meeting page’s styles where appropriate, with a plan to unify into a single global theme

### Staff & Multi-User System (active)
- Master Encryption Password (MEP) splits encryption from user login; entered once at console
- Staff accounts stored in encrypted per-staff databases with individual login passwords
- Roles: `admin`, `teacher`, `front_office`, `back_office`, `bot`, `dev`
- Staff login via browser (username + password) with session tokens (60-minute expiry)
- Admin panel: create, approve (with MEP), and delete staff accounts
- **Teacher listing endpoint** (`GET /api/staff/teachers`) – available to any authenticated user, used by student creation form
- Own-profile editing (name, contact, rate, bio); availability and holidays UI in progress
- Student module now uses staff token for access (no separate student password)

### Recent Architectural Decisions
- **MEP split**: `crypto_engine` holds master key in memory after console unlock; user passwords unrelated to encryption.
- **Meeting–student linking**: Student creation automatically adds meeting rows to the shared meetings database; meeting times linked to student profiles.
- **Timezone data**: Generated once via `generate_timezone_data.py` → `data/utils/timezone_data.json`.
- **Frontend modularisation**: Dashboard widgets organised by screen location (`column1/`, `column2/`, `bottom/`). Student JS remains under `students/`.
- **Database normalisation**: Phones, emails, parent contacts, relationships stored in dedicated encrypted tables. No JSON blobs in plain sight.
- **Security**: Dashboard widget files are only imported dynamically after authentication – no frontend code leaks before login.

---

## Tech Stack

### Current Components
| Component      | Technology                        | Notes                                 |
|----------------|-----------------------------------|---------------------------------------|
| Backend Server | Python 3.12                       | Lightweight, runs on thumb drive      |
| Database       | SQLite / SQLCipher                | File-based, encrypted per-student     |
| Frontend       | HTML, CSS, JavaScript (ES modules)| No external dependencies              |
| Browser        | Brave (Chromium-based)            | Privacy-focused                       |
| Version Control| Git                               | Local + GitHub                        |
| Cryptography   | cryptography, pysqlcipher3        | Portable in `libs/` folder            |
| SSL/TLS        | Self-signed per-session certs     | Local CA installed once               |
| Timezone Data  | Python `zoneinfo` (stdlib)        | One-off generation to static JSON     |

### Future Components
| Component      | Technology                        | Notes                                 |
|----------------|-----------------------------------|---------------------------------------|
| OCR Receipt Scanning | Tesseract or similar         | Extract payment details from images   |
| Teacher Profile| Built-in module                   | Availability, default settings        |
| Telegram Bot   | python-telegram-bot               |                                       |
| LLM Integration| Hugging Face or Ollama            | Burmese language support              |
| Cloud Sync     | Render (free tier)                | Optional backup                       |
| Analytics      | Chart.js (local bundle)           | Role-specific dashboards              |

---

## Project Structure

crm-app/
├── main.py                     # Ultra-thin launcher
├── src/
│   ├── server.py               # HTTPS server, SSL, routing
│   ├── crypto_engine.py        # MEP unlock, master key management
│   ├── meetings/
│   │   ├── db.py               # Meetings DB init & CRUD (+ group names)
│   │   └── coordinator.py      # Meetings API router (+ /api/meetings/groups)
│   ├── students/
│   │   ├── coordinator.py      # Student API router (creates meetings on student add)
│   │   ├── crypto.py           # Encryption & key derivation
│   │   ├── index_db.py         # Encrypted central index (student summaries)
│   │   ├── student_db.py       # Per-student encrypted DB (profile + birthdate + teacher_id)
│   │   ├── auth.py             # (Legacy) password, session, expiry
│   │   └── models.py           # Data structures
│   └── staff/
│       ├── coordinator.py      # Staff API router (+ /api/staff/teachers)
│       ├── auth.py             # Staff session management
│       ├── index_db.py         # Encrypted staff index
│       ├── staff_db.py         # Per-staff encrypted DB
│       └── models.py           # Staff data structures
├── launch/
│   ├── index.html              # Login page (username + password)
│   ├── dashboard/              # Role-based dashboard system
│   │   ├── dashboard.html      # Unified shell
│   │   ├── css/styles.css      # Dashboard theme (Catppuccin Dark)
│   │   └── js/
│   │       ├── coordinator.js  # Core dashboard logic, lazy widget loading
│   │       ├── api.js          # Shared API helper (staff token)
│   │       ├── widgets.js      # Widget renderer and registry
│   │       ├── dashboards/     # Role config files (admin.js, teacher.js, ...)
│   │       └── widgets/
│   │           ├── column1/    # Left-column widgets (35%)
│   │           │   ├── upcomingDates.js
│   │           │   ├── studentHighlights.js
│   │           │   ├── attendance.js
│   │           │   ├── paymentsSummary.js
│   │           │   ├── botHealth.js
│   │           │   └── agentHealth.js
│   │           ├── column2/    # Right-column widgets (65%)
│   │           │   ├── meetings.js
│   │           │   ├── messages.js
│   │           │   └── analytics/   # Chart stubs
│   │           └── bottom/     # Bottom-area widgets (tabbed or full-width)
│   │               ├── inbox.js
│   │               ├── buildStatus.js
│   │               ├── allLogs.js
│   │               ├── errors.js
│   │               ├── templates.js
│   │               ├── addFinances.js
│   │               ├── activityLog.js
│   │               └── apiConsole.js
│   ├── meetings/               # Meetings frontend
│   │   ├── meetings.html
│   │   ├── css/styles.css
│   │   └── js/
│   │       ├── api.js
│   │       ├── app.js
│   │       ├── config.js
│   │       └── render.js
│   ├── students/               # Student frontend (uses staff token)
│   │   ├── students.html
│   │   ├── css/styles.css
│   │   └── js/
│   │       ├── api.js
│   │       ├── app.js
│   │       ├── config.js
│   │       ├── students/
│   │       │   ├── addForm.js          # Updated with teacher, birthdate, group selector
│   │       │   ├── detailView.js
│   │       │   └── list.js
│   │       ├── actions/
│   │       │   └── actions.js
│   │       └── utils/
│   │           └── helpers.js
│   └── staff/                  # Staff management & profiles
│       ├── staff.html
│       ├── css/
│       │   └── styles.css
│       └── js/
│           ├── api.js
│           ├── app.js
│           ├── config.js
│           ├── admin/          # (future admin widgets)
│           ├── profile/        # (future profile widgets)
│           └── auth/           # (future auth helpers)
├── data/
│   ├── meetings/
│   │   └── meetings.db         # Meetings (unencrypted)
│   ├── students/
│   │   ├── index.db            # Central index (encrypted)
│   │   └── {uuid}.sqlite       # Per-student encrypted DB
│   ├── staff/
│   │   ├── index.db            # Staff index (encrypted)
│   │   └── databases/
│   │       └── {uuid}.sqlite   # Per-staff encrypted DB
│   ├── utils/
│   │   └── timezone_data.json  # Generated timezone list
│   ├── master_key.salt         # MEP salt
│   ├── master_key.enc          # Encrypted master key
│   └── certs/                  # SSL certificates (auto-generated)
├── libs/                       # Portable Python packages (git-ignored)
├── generate_timezone_data.py
├── check_student.py            # Debug script
├── create_admin.py             # Admin account creation & approval script
├── README.md
└── .gitignore
How It Works
Launch the App
Open a terminal in the crm-app folder.

Run: PYTHONPATH=./libs python3 main.py

Enter the Master Encryption Password (MEP) when prompted (first run sets it).

The server starts with HTTPS on https://localhost:8080 and opens the login page.

Authentication Flow (current)
First run: create_admin.py creates an admin staff account (inactive), then approves it with MEP.

Subsequent starts: MEP unlocks data; users log in with their staff username and password at /launch/index.html.

Session: Token stored in browser, expires after 60 min of inactivity.

Student access: Student page now reads staff token; no separate student password needed.

Irreversible actions (e.g., delete student) still require MEP re-entry.

Meetings
Click "Meetings" from dashboard to view weekly calendar.

Add meetings with name, day, time, type, Jitsi link, students, rate, homework, comments.

Click a meeting name or the countdown number to join via Jitsi with low-bandwidth settings.

Edit or delete meetings using per-entry buttons.

Currently, meetings are stored independently from student profiles. Linking will be part of a future meeting system refactor.

Students
Access from dashboard; requires valid staff login.

Student list with search and filters (status, rate range, payment status).

Add/Edit student form with all fields as described above.

Click student card for detail view (attendance, payments, linked students).

Delete student: click "Delete", enter MEP to confirm.

Staff Management (admin only)
Staff page accessible from admin dashboard.

Create new staff accounts (inactive by default).

Approve staff accounts (requires MEP).

Edit own profile, availability, holidays (UI in progress).

Dashboards (new)
After login, the dashboard shell loads the role‑appropriate layout.

Admin can use the “View” menu to switch to any other role’s dashboard (teacher, front‑office, back‑office, bot, dev).

The teacher dashboard shows meetings for any day (via day picker) and a “Today’s Attendance” checklist.

Front‑office dashboard can jump to student creation or meetings view via the “View” menu.

Other dashboards contain placeholder widgets for future features.

Installation & Setup
Prerequisites
Ubuntu-based Linux (tested on Linux Mint 22.3)

Python 3.12+

Brave or Firefox browser

System library: libsqlcipher-dev

One-time setup
Copy the crm-app folder to your USB drive.

Install system dependency: sudo apt install libsqlcipher-dev

Navigate to the folder: cd /path/to/crm-app

Create the portable library folder and install packages:

bash
mkdir -p libs
pip install --target=./libs pysqlcipher3 cryptography
Run the app once to generate SSL certificates and set up MEP:

bash
PYTHONPATH=./libs python3 main.py
(Follow prompts to create the Master Encryption Password.)

Install the generated local CA certificate into your system trust store:

bash
sudo cp data/certs/ca.crt /usr/local/share/ca-certificates/crm-ca.crt
sudo update-ca-certificates
Restart your browser afterwards.

Create the initial admin staff account:

bash
PYTHONPATH=./libs python3 create_admin.py
(Use admin/admin123 or set your own credentials.)

(Optional) Generate the full timezone data file:

bash
PYTHONPATH=./libs python3 generate_timezone_data.py
Running normally
bash
cd /path/to/crm-app
PYTHONPATH=./libs python3 main.py
Open https://localhost:8080/launch/index.html (the launcher opens it automatically).

Security Model
Transport security: All traffic uses HTTPS with per-session server certificates signed by a local CA.

Authentication: Staff passwords hashed with scrypt. Session tokens expire after 60 min. MEP required for irreversible actions and staff approval.

Encryption at rest: Student index and per-student DBs encrypted with unique keys, sealed by a master key. Staff index and per-staff DBs encrypted with the same master key. Master key stored in master_key.enc, encrypted with MEP (scrypt + AES‑GCM).

No internet connection required: Everything runs locally; no data leaves the USB drive.

Roadmap
Phase 1: Meeting Launcher (Complete)
Vertical weekly calendar

One-click Jitsi join with low bandwidth

Private & group classes

Countdown tracker, rate, homework, comments

SQLite storage

Edit & delete meetings

Dark theme

Current/upcoming highlighting

Phase 2: Student & Staff Management (Active)
Encrypted per-student databases

Master password + SSL authentication

Student list view with search and filters

Full student profile (contacts, meetings, goals, comments)

Attendance logging

Payment records (manual entry)

Global action items

Student linking (family/siblings)

Multi-value contact fields

Modular frontend architecture

Timezone dropdown with worldwide coverage

Password-protected student deletion

MEP split: separate encryption from user login

Staff accounts & role-based access

Admin staff creation/approval workflow

Dashboard shell with role-based views (complete)

Teacher dropdown, birthdate, group meeting selector in student form (complete)

Meeting auto-creation on student add (complete)

Unified inbox stub (future: Eisenhower matrix)

Attendance widget (teacher dashboard) – ready for backend wiring

Meeting–student integration (completed via auto-creation; future refactor for multi-day packages)

Phase 3: Telegram Bot
Deploy bot to Render (free tier)

Burmese language support

FAQ automation

Scheduling assistance

Phase 4: Analytics
Attendance reports

Revenue summaries

Export to CSV/PDF

Phase 5: Scripts & Automation
FAQ database

Funnels and templates

Automated reminders

Cost Breakdown
Component	Cost
Meeting Launcher	$0
Student Manager	$0
SQLite/SQLCipher	$0
Brave Browser	$0
Python & libraries	$0
Git & GitHub	$0
Render (future)	$0
Total	$0
Git Workflow
bash
# See status
git status

# Stage all changes (libs/ is ignored)
git add -A

# Commit
git commit -m "Description"

# Push to GitHub
git push origin main
Private project – built for teachers in Myanmar with limited internet connectivity.
