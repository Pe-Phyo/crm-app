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
- Back‑Office Pricing & Packages: encrypted package templates, subscription logic, invoice grouping
- Future: Telegram bot, OCR receipt scanning, teacher availability integration, analytics, automation

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
- Student list panel with search and filters (status, next invoice, payment status)
- Add/Edit student form with:
  - Full name, **birthdate**, age group, timezone (selected from worldwide list)
  - Per‑meeting teacher assignment, rate, and package templates loaded from back‑office pricing
  - Multi-value phone numbers and email addresses (dynamic add/remove)
  - Telegram handle
  - Conditional minor section: parent/guardian details, school, grade
  - Multi-day meeting times with meeting name, day, time, type, in‑person flag, meeting link, teacher, rate
  - **Group meeting selector** – when type is “Group”, choose from existing groups or create new
  - Link to other students (family/siblings) with relationship type and invoice grouping toggle
  - **Next Invoice** computed from active packages; linked students show primary account reference
  - Educational goals and general comments
- Student detail view showing profile, meeting times, attendance log, payment records, next invoice, linked students
- Global action items / to-do list (add, toggle, delete)
- Password-protected student deletion (requires MEP re-entry)
- All student data encrypted at rest

### Domain‑Separated Backend (New Architecture)
- **Student module** (`src/students/`) – pure profile & contact data; no attendance/payment logic
- **Teacher module** (`src/teachers/`) – attendance recording, owned by teacher role
- **Front‑Office module** (`src/frontoffice/`) – payment recording
- **Back‑Office module** (`src/backoffice/pricing/`) – encrypted package templates, base rates, discount rules, subscription service (invoice calculation, package creation, linked‑student grouping)
- All modules use the same master encryption key; pricing & future analytics databases are encrypted with SQLCipher
- Server routes requests to the appropriate domain coordinator

### Package & Subscription System (New)
- Teachers define availability and package templates (private/group, lesson count, rate, subject, schedule)
- Back‑office creates/manages package templates in encrypted `pricing.db`
- Student form loads teacher‑specific templates; selecting a template auto‑fills meeting details
- On save, a package entry is created in the student’s encrypted DB, and `next_invoice` is calculated from active packages (minus discounts)
- Linked students with invoice grouping show combined invoice on primary account
- Subscription status (active, paused, completed) supports legacy rate handling and re‑enrollment at current rates
- Analytics foundation: future `analytics.db` will record package events for revenue reporting

### Dashboard System
- **Unified shell** (`dashboard.html`) that loads a role‑specific configuration
- Six dashboards: **Admin**, **Teacher**, **Front Office**, **Back Office**, **Bot**, and **System & Dev**
- Each dashboard defines which widgets appear in the left column (35%), right column (65%), and bottom tab area
- **Widgets are loaded lazily and securely** – no widget code is sent to the browser until the user is authenticated, and only the widgets needed for the current role are loaded
- **“View” menu** (eye icon) in the top bar:
  - Admin can switch to any other role’s dashboard and back
  - Other roles have placeholder menu items for future actions (e.g., Student View, Meetings View)
- Built‑in widgets include:
  - **Upcoming Dates** – holidays, exams, and eventually birthdays
  - **Student Highlights** – active count, top loyalty (static for now)
  - **Meetings** (teacher right column) – day picker, today’s meetings with homework/comments
  - **Attendance** (teacher left column) – list of students with meetings today, checkbox to mark present/absent (uses teacher attendance API)
  - **Inbox** (bottom tab for all roles) – shared action items
  - **Payments Summary**, **Bot Health**, **Agent Health**, **Messages**, **Financial Overview**, etc. – stubs for future work
- Front‑office “Student View” menu item links directly to the student creation page

### Staff & Multi-User System
- Master Encryption Password (MEP) splits encryption from user login; entered once at console
- Staff accounts stored in encrypted per-staff databases with individual login passwords
- Roles: `admin`, `teacher`, `front_office`, `back_office`, `bot`, `dev`
- Staff login via browser (username + password) with session tokens (60-minute expiry)
- Admin panel: create, approve (with MEP), and delete staff accounts
- **Teacher listing endpoint** (`GET /api/staff/teachers`) – available to any authenticated user
- Own-profile editing (name, contact, rate, bio); availability and holidays stored per staff, editable by teacher, approved by back‑office

### Recent Architectural Decisions
- **MEP split**: `crypto_engine` holds master key in memory after console unlock; user passwords unrelated to encryption.
- **Domain separation**: Student, Teacher, Front‑Office, Back‑Office each own their data and logic; server routes accordingly.
- **Package‑based pricing**: Per‑meeting teacher/rate removed from student profile; packages define billing, auto‑calculated next invoice.
- **Timezone data**: Generated once via `generate_timezone_data.py` → `data/utils/timezone_data.json`.
- **Frontend modularisation**: Dashboard widgets organised by screen location. Student JS remains under `students/`.
- **Database normalisation**: Phones, emails, parent contacts, relationships stored in dedicated encrypted tables. No JSON blobs in plain sight.
- **Security**: Dashboard widget files are only imported dynamically after authentication – no frontend code leaks before login.

---

## Tech Stack

| Component      | Technology                        | Notes                                 |
|----------------|-----------------------------------|---------------------------------------|
| Backend Server | Python 3.12                       | Lightweight, runs on thumb drive      |
| Database       | SQLite / SQLCipher                | File-based, encrypted per-student & staff, pricing DB encrypted |
| Frontend       | HTML, CSS, JavaScript (ES modules)| No external dependencies              |
| Browser        | Brave (Chromium-based)            | Privacy-focused                       |
| Version Control| Git                               | Local + GitHub                        |
| Cryptography   | cryptography, pysqlcipher3        | Portable in `libs/` folder            |
| SSL/TLS        | Self-signed per-session certs     | Local CA installed once               |
| Timezone Data  | Python `zoneinfo` (stdlib)        | One-off generation to static JSON     |

---

## Project Structure
crm-app/
├── main.py # Ultra-thin launcher
├── src/
│ ├── server.py # HTTPS server, SSL, routing to all coordinators
│ ├── crypto_engine.py # MEP unlock, master key management
│ ├── meetings/
│ │ ├── db.py # Meetings DB init & CRUD (+ group names)
│ │ └── coordinator.py # Meetings API router
│ ├── students/
│ │ ├── coordinator.py # Student profile API (create/read/update/delete)
│ │ ├── crypto.py # Encryption & key derivation
│ │ ├── index_db.py # Encrypted central index (next_invoice, invoice_reference)
│ │ ├── student_db.py # Per-student encrypted DB (profile, contacts, packages, meeting_times)
│ │ ├── auth.py # (Legacy) password, session, expiry
│ │ └── models.py # Data structures
│ ├── teachers/
│ │ ├── coordinator.py # Teacher API router (attendance)
│ │ └── attendance.py # Attendance service (read/write student encrypted DB)
│ ├── frontoffice/
│ │ ├── coordinator.py # Front‑Office API router (payments)
│ │ └── payments/
│ │ └── service.py # Payments service
│ ├── backoffice/
│ │ └── pricing/
│ │ ├── db.py # Encrypted pricing DB (package_templates, base_rates)
│ │ ├── models.py # PackageTemplate dataclass
│ │ ├── coordinator.py # Pricing API router (template CRUD, student form reads)
│ │ └── subscriptions.py # Business logic: packages, invoice calc, linked grouping
│ └── staff/
│ ├── coordinator.py # Staff API router (+ /api/staff/teachers)
│ ├── auth.py # Staff session management
│ ├── index_db.py # Encrypted staff index
│ ├── staff_db.py # Per-staff encrypted DB (profile, availability, holidays)
│ └── models.py # Staff data structures
├── launch/
│ ├── index.html # Login page
│ ├── dashboard/ # Role-based dashboard system
│ │ ├── dashboard.html
│ │ ├── css/styles.css
│ │ └── js/
│ │ ├── coordinator.js
│ │ ├── api.js
│ │ ├── widgets.js
│ │ ├── dashboards/
│ │ └── widgets/
│ │ ├── column1/ # Left-column widgets
│ │ │ ├── attendance.js
│ │ │ ├── upcomingDates.js
│ │ │ ├── studentHighlights.js
│ │ │ └── ...
│ │ ├── column2/ # Right-column widgets
│ │ │ ├── meetings.js
│ │ │ └── ...
│ │ └── bottom/
│ │ ├── inbox.js
│ │ └── ...
│ ├── meetings/ # Meetings frontend
│ │ ├── meetings.html
│ │ └── js/
│ ├── students/ # Student frontend
│ │ ├── students.html
│ │ └── js/
│ │ ├── api.js # API wrappers (students, attendance, payments, pricing)
│ │ ├── app.js
│ │ └── students/
│ │ ├── addForm.js # Form with teacher packages, per-meeting teacher/rate
│ │ ├── detailView.js # Detail modal with next invoice, attendance, payments
│ │ └── list.js # Student cards with local time, next invoice, filters
│ └── staff/ # Staff management & profiles
│ ├── staff.html
│ └── js/
│ ├── api.js
│ ├── profile.js # Own profile editing, availability
│ └── ...
├── data/
│ ├── meetings/
│ │ └── meetings.db # Meetings (SQLite)
│ ├── students/
│ │ ├── index.db # Central index (encrypted)
│ │ └── {uuid}.sqlite # Per-student encrypted DB
│ ├── staff/
│ │ ├── index.db # Staff index (encrypted)
│ │ └── databases/
│ │ └── {uuid}.sqlite # Per-staff encrypted DB
│ ├── pricing/
│ │ └── pricing.db # Package templates & base rates (encrypted)
│ ├── utils/
│ │ └── timezone_data.json
│ ├── master_key.salt
│ ├── master_key.enc
│ └── certs/ # SSL certificates (auto-generated)
├── libs/ # Portable Python packages (git-ignored)
├── generate_timezone_data.py
├── create_admin.py
├── README.md
└── .gitignore

text

## How It Works

### Launch the App
1. Open a terminal in the `crm-app` folder.
2. Run: `PYTHONPATH=./libs python3 main.py`
3. Enter the Master Encryption Password (MEP) when prompted (first run sets it).
4. The server starts with HTTPS on `https://localhost:8080` and opens the login page.

### Authentication Flow
- First run: `create_admin.py` creates an admin staff account (inactive), then approves it with MEP.
- Subsequent starts: MEP unlocks data; users log in with their staff username and password at `/launch/index.html`.
- Session token stored in browser, expires after 60 min of inactivity.
- Student pages use staff token; no separate student password needed.
- Irreversible actions (e.g., delete student) still require MEP re-entry.

### Meetings
- Click “Meetings” from dashboard to view weekly calendar.
- Add meetings with name, day, time, type, Jitsi link, students, rate, homework, comments.
- Click a meeting name or the countdown number to join via Jitsi with low-bandwidth settings.
- Edit or delete meetings using per-entry buttons.
- Meetings can be linked to student packages; teacher dashboard filters by teacher.

### Students
- Access from dashboard; requires valid staff login.
- Student list with search and filters (status, next invoice, payment status).
- Add/Edit student form: per-meeting teacher/rate, load back‑office package templates to auto-fill fields.
- Student card shows local time, next invoice (or primary reference for grouped accounts), meeting summary.
- Click student card for detail view (attendance, payments, linked students, next invoice).
- Attendance is now managed by the teacher coordinator (`/api/teacher/attendance`).
- Payments are managed by the front‑office coordinator (`/api/frontoffice/payments`).

### Back‑Office Pricing & Packages
- Back‑office staff manage package templates in `pricing.db` via the pricing coordinator.
- Templates include teacher, subject, type, lesson count, rate, schedule.
- When adding a student, the form fetches templates for the selected teacher and auto-fills meeting rows.
- On save, a package is created in the student's encrypted DB; `next_invoice` is calculated from active packages.
- Linked students with invoice grouping show combined invoice on the primary account.

### Staff Management (admin only)
- Staff page accessible from admin dashboard.
- Create new staff accounts (inactive by default).
- Approve staff accounts (requires MEP).
- Edit own profile, availability, holidays (teacher can submit, admin approves).

### Dashboards
- After login, the dashboard shell loads the role‑appropriate layout.
- Admin can use the “View” menu to switch to any other role’s dashboard.
- Teacher dashboard shows meetings for any day and a “Today’s Attendance” checklist (calls teacher attendance API).
- Front‑office dashboard can jump to student creation or meetings view.

## Installation & Setup

### Prerequisites
- Ubuntu-based Linux (tested on Linux Mint 22.3)
- Python 3.12+
- Brave or Firefox browser
- System library: `libsqlcipher-dev`

### One-time setup
1. Copy the `crm-app` folder to your USB drive.
2. Install system dependency:
   ```bash
   sudo apt install libsqlcipher-dev
Navigate to the folder:

bash
cd /path/to/crm-app
Create the portable library folder and install packages:

bash
mkdir -p libs
pip install --target=./libs pysqlcipher3 cryptography
Run the app once to generate SSL certificates and set up MEP:

bash
PYTHONPATH=./libs python3 main.py
(Follow prompts to create the Master Encryption Password.)

Install the generated local CA certificate:

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

Encryption at rest: Student index and per-student DBs encrypted with unique keys, sealed by a master key. Staff index, per-staff DBs, and pricing DB encrypted with the same master key. Master key stored in master_key.enc, encrypted with MEP (scrypt + AES‑GCM).

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

Attendance logging (teacher domain)

Payment records (front‑office domain)

Global action items

Student linking (family/siblings) with invoice grouping

Multi-value contact fields

Modular frontend architecture

Timezone dropdown with worldwide coverage

Password-protected student deletion

MEP split: separate encryption from user login

Staff accounts & role-based access

Admin staff creation/approval workflow

Dashboard shell with role-based views (complete)

Teacher dropdown, birthdate, group meeting selector in student form (complete)

Back‑office pricing module with package templates

Per-meeting teacher/rate, package auto‑fill

Next invoice calculation from active packages

Domain‑separated coordinators (Student, Teacher, Front‑Office, Back‑Office)

Phase 3: Telegram Bot
Deploy bot to Render (free tier)

Burmese language support

FAQ automation

Scheduling assistance

Phase 4: Analytics
Attendance reports

Revenue summaries per teacher/package

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
git status
git add -A
git commit -m "Description"
git push origin main
Private project – built for teachers in Myanmar with limited internet connectivity.
