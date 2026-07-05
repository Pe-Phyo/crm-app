```markdown
# CRM App – Meeting Launcher & Student Manager

A lightweight, privacy-focused CRM for teachers with limited internet connectivity.  
Runs entirely from a USB thumb drive, stores data in encrypted SQLite databases, and works offline.

---

## Project Overview

This modular CRM handles:

- Meeting Launcher: one-click Jitsi join with low-bandwidth settings
- Student Management: secure, encrypted client profiles with attendance, payments, and notes
- Staff & Role Management: multi-user system with role-based dashboards (active development)
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
  - Full name, age group, timezone (selected from worldwide list)
  - Multi-value phone numbers and email addresses (dynamic add/remove)
  - Telegram handle
  - Conditional minor section: parent/guardian details, school, grade
  - Multi-day meeting times with meeting name, day, time, type, in‑person flag, meeting link
  - Link to other students (family/siblings) with relationship type and invoice grouping toggle
  - Rate per lesson (MMK)
  - Educational goals and general comments
- Student detail view showing all stored information, including attendance log, payment records, linked students
- Global action items / to-do list (add, toggle, delete)
- Password-protected student deletion (requires MEP re-entry)
- All student data encrypted at rest

### Staff & Multi-User System (active)
- Master Encryption Password (MEP) splits encryption from user login; entered once at console
- Staff accounts stored in encrypted per-staff databases with individual login passwords
- Roles: `admin`, `teacher`, `front_office`, `back_office`, `bot`, `dev`
- Staff login via browser (username + password) with session tokens (60-minute expiry)
- Admin panel: create, approve (with MEP), and delete staff accounts
- Own-profile editing (name, contact, rate, bio); availability and holidays UI in progress
- Student module now uses staff token for access (no separate student password)

### Recent Architectural Decisions
- **MEP split**: `crypto_engine` holds master key in memory after console unlock; user passwords unrelated to encryption.
- **Meeting–student linking deferred**: Future meeting refactor for multi-day packages, teacher assignment.
- **Timezone data**: Generated once via `generate_timezone_data.py` → `data/utils/timezone_data.json`.
- **Frontend modularisation**: Student JS split into `auth/`, `students/`, `actions/`, `utils/`. Staff JS follows similar pattern.
- **Database normalisation**: Phones, emails, parent contacts, relationships stored in dedicated encrypted tables. No JSON blobs in plain sight.

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
│   │   ├── db.py               # Meetings DB init & CRUD
│   │   └── coordinator.py      # Meetings API router
│   ├── students/
│   │   ├── coordinator.py      # Student API router
│   │   ├── crypto.py           # Encryption & key derivation
│   │   ├── index_db.py         # Encrypted central index
│   │   ├── student_db.py       # Per-student encrypted DB
│   │   ├── auth.py             # (Legacy) password, session, expiry
│   │   └── models.py           # Data structures
│   └── staff/
│       ├── coordinator.py      # Staff API router
│       ├── auth.py             # Staff session management
│       ├── index_db.py         # Encrypted staff index
│       ├── staff_db.py         # Per-staff encrypted DB
│       └── models.py           # Staff data structures
├── launch/
│   ├── index.html              # Login page (username + password)
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
│   │       │   ├── addForm.js
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
```

---

## How It Works

### Launch the App
1. Open a terminal in the `crm-app` folder.
2. Run: `PYTHONPATH=./libs python3 main.py`
3. Enter the Master Encryption Password (MEP) when prompted (first run sets it).
4. The server starts with HTTPS on `https://localhost:8080` and opens the login page.

### Authentication Flow (current)
- **First run**: `create_admin.py` creates an admin staff account (inactive), then approves it with MEP.
- **Subsequent starts**: MEP unlocks data; users log in with their staff username and password at `/launch/index.html`.
- **Session**: Token stored in browser, expires after 60 min of inactivity.
- **Student access**: Student page now reads staff token; no separate student password needed.
- **Irreversible actions** (e.g., delete student) still require MEP re-entry.

### Meetings
- Click "Meetings" from dashboard to view weekly calendar.
- Add meetings with name, day, time, type, Jitsi link, students, rate, homework, comments.
- Click a meeting name or the countdown number to join via Jitsi with low-bandwidth settings.
- Edit or delete meetings using per-entry buttons.
- Currently, meetings are stored independently from student profiles. Linking will be part of a future meeting system refactor.

### Students
- Access from dashboard; requires valid staff login.
- Student list with search and filters (status, rate range, payment status).
- Add/Edit student form with all fields as described above.
- Click student card for detail view (attendance, payments, linked students).
- Delete student: click "Delete", enter MEP to confirm.

### Staff Management (admin only)
- Staff page accessible from admin dashboard.
- Create new staff accounts (inactive by default).
- Approve staff accounts (requires MEP).
- Edit own profile, availability, holidays (UI in progress).

---

## Installation & Setup

### Prerequisites
- Ubuntu-based Linux (tested on Linux Mint 22.3)
- Python 3.12+
- Brave or Firefox browser
- System library: `libsqlcipher-dev`

### One-time setup
1. Copy the `crm-app` folder to your USB drive.
2. Install system dependency: `sudo apt install libsqlcipher-dev`
3. Navigate to the folder: `cd /path/to/crm-app`
4. Create the portable library folder and install packages:
   ```bash
   mkdir -p libs
   pip install --target=./libs pysqlcipher3 cryptography
   ```
5. Run the app once to generate SSL certificates and set up MEP:
   ```bash
   PYTHONPATH=./libs python3 main.py
   ```
   (Follow prompts to create the Master Encryption Password.)
6. Install the generated local CA certificate into your system trust store:
   ```bash
   sudo cp data/certs/ca.crt /usr/local/share/ca-certificates/crm-ca.crt
   sudo update-ca-certificates
   ```
   Restart your browser afterwards.
7. Create the initial admin staff account:
   ```bash
   PYTHONPATH=./libs python3 create_admin.py
   ```
   (Use admin/admin123 or set your own credentials.)
8. (Optional) Generate the full timezone data file:
   ```bash
   PYTHONPATH=./libs python3 generate_timezone_data.py
   ```

### Running normally
```bash
cd /path/to/crm-app
PYTHONPATH=./libs python3 main.py
```
Open `https://localhost:8080/launch/index.html` (the launcher opens it automatically).

---

## Security Model
- **Transport security**: All traffic uses HTTPS with per-session server certificates signed by a local CA.
- **Authentication**: Staff passwords hashed with scrypt. Session tokens expire after 60 min. MEP required for irreversible actions and staff approval.
- **Encryption at rest**: Student index and per-student DBs encrypted with unique keys, sealed by a master key. Staff index and per-staff DBs encrypted with the same master key. Master key stored in `master_key.enc`, encrypted with MEP (scrypt + AES‑GCM).
- **No internet connection required**: Everything runs locally; no data leaves the USB drive.

---

## Roadmap

### Phase 1: Meeting Launcher (Complete)
- [x] Vertical weekly calendar
- [x] One-click Jitsi join with low bandwidth
- [x] Private & group classes
- [x] Countdown tracker, rate, homework, comments
- [x] SQLite storage
- [x] Edit & delete meetings
- [x] Dark theme
- [x] Current/upcoming highlighting

### Phase 2: Student & Staff Management (Active)
- [x] Encrypted per-student databases
- [x] Master password + SSL authentication
- [x] Student list view with search and filters
- [x] Full student profile (contacts, meetings, goals, comments)
- [x] Attendance logging
- [x] Payment records (manual entry)
- [x] Global action items
- [x] Student linking (family/siblings)
- [x] Multi-value contact fields
- [x] Modular frontend architecture
- [x] Timezone dropdown with worldwide coverage
- [x] Password-protected student deletion
- [x] MEP split: separate encryption from user login
- [x] Staff accounts & role-based access
- [x] Admin staff creation/approval workflow
- [ ] **Dashboard shell refactoring** (next major milestone)
  - Unified shell with role-based sidebar (or tabs) shared by all dashboards.
  - **Admin/CEO Dashboard**: business health (active students, revenue, outstanding payments), system health (MEP status, USB free space, bot statuses), inbox with Eisenhower matrix, analytics (Chart.js), build status from git log.
  - **Teacher Dashboard**: own student list, upcoming meetings, availability & holidays editor, personal action items.
  - **Front Office Dashboard**: leads, today’s schedule, payments summary, messaging placeholders.
  - **Back Office Dashboard**: financial overview, payroll & expenses, pending approvals.
  - **Bot Management Dashboard**: bot status list, live activity log, templates, errors.
  - **System & Dev Dashboard**: build status, system health, logs viewer, API console (stub).
  - "View as…" feature for admin to preview any role’s dashboard.
  - Inbox heuristics per role, starting with the Eisenhower quadrant for admin.
- [ ] Meeting–student integration (deferred to dedicated meeting refactor)

### Phase 3: Telegram Bot
- Deploy bot to Render (free tier)
- Burmese language support
- FAQ automation
- Scheduling assistance

### Phase 4: Analytics
- Attendance reports
- Revenue summaries
- Export to CSV/PDF

### Phase 5: Scripts & Automation
- FAQ database
- Funnels and templates
- Automated reminders

---

## Cost Breakdown
| Component         | Cost |
|-------------------|------|
| Meeting Launcher  | $0   |
| Student Manager   | $0   |
| SQLite/SQLCipher  | $0   |
| Brave Browser     | $0   |
| Python & libraries| $0   |
| Git & GitHub      | $0   |
| Render (future)   | $0   |
| **Total**         | $0   |

---

## Git Workflow
```bash
# See status
git status

# Stage all changes (libs/ is ignored)
git add -A

# Commit
git commit -m "Description"

# Push to GitHub
git push origin main
```
Private project – built for teachers in Myanmar with limited internet connectivity.
```
