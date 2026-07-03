Here is the updated `README.md` with the current project state, no emojis, ready to cut and paste.

---

```markdown
# CRM App - Meeting Launcher & Student Manager

A lightweight, privacy-focused CRM for teachers with limited internet connectivity.  
Runs entirely from a USB thumb drive, stores data in encrypted SQLite databases, and works offline.

---

## Project Overview

This modular CRM handles:

- Meeting Launcher: one-click Jitsi join with low-bandwidth settings
- Student Management: secure, encrypted client profiles with attendance, payments, and notes
- Database Storage: SQLite / SQLCipher on thumb drive
- Future: Telegram bot, analytics, automation scripts

---

## Current Features

### Meeting Launcher
- One-click Jitsi joining (Brave browser, no extra clicks)
- Low bandwidth by default (video off, mic off, skip pre-join)
- Vertical weekly calendar, current day on top
- Current meeting highlighted, upcoming meeting highlighted
- Private and group classes (max 9 students)
- Per-meeting countdown tracker, rate (MMK), homework, comments
- Add/remove students per meeting
- SQLite database storage
- Works offline

### Student Manager (Phase 2 - in progress)
- Master password protection with per-session SSL encryption
- Encrypted central index database (SQLCipher)
- Individual per-student encrypted databases
- Student list with search and filters (status, rate, payment)
- Full student profiles: contact info, age group, academic year, meetings, goals, comments
- Attendance logging per student
- Payment tracking (manual entry, receipt image storage ready)
- Global action items / to-do list
- All student data encrypted at rest

---

## Tech Stack

### Current Components
| Component      | Technology                        | Notes                           |
|----------------|-----------------------------------|---------------------------------|
| Backend Server | Python 3.12                       | Lightweight, runs on thumb drive|
| Database       | SQLite / SQLCipher                | File-based, encrypted per-student|
| Frontend       | HTML, CSS, JavaScript (ES modules)| No external dependencies        |
| Browser        | Brave (Chromium-based)            | Privacy-focused                 |
| Version Control| Git                               | Local + GitHub                  |
| Cryptography   | cryptography, pysqlcipher3        | Portable in `libs/` folder      |
| SSL/TLS        | Self-signed per-session certs     | Local CA installed once         |

### Future Components
| Component      | Technology                        | Notes                           |
|----------------|-----------------------------------|---------------------------------|
| Telegram Bot   | python-telegram-bot               |                                 |
| LLM Integration| Hugging Face or Ollama            | Burmese language support        |
| Cloud Sync     | Render (free tier)                | Optional backup                 |

---

## Project Structure

```
crm-app/
├── main.py                      # Ultra-thin launcher
├── src/
│   ├── server.py                # HTTPS server, SSL, routing
│   ├── meetings/
│   │   ├── db.py                # Meetings DB init & CRUD
│   │   └── coordinator.py       # Meetings API router
│   └── students/
│       ├── coordinator.py       # Student API router
│       ├── crypto.py            # Encryption & key derivation
│       ├── index_db.py          # Encrypted central index
│       ├── student_db.py        # Per-student encrypted DB
│       ├── auth.py              # Password, session, expiry
│       ├── actions.py           # Action items logic
│       └── models.py            # Data structures
├── launch/
│   ├── index.html               # Main dashboard
│   ├── meetings/                # Meetings frontend
│   │   ├── meetings.html
│   │   ├── css/styles.css
│   │   └── js/
│   │       ├── api.js
│   │       ├── app.js
│   │       ├── config.js
│   │       └── render.js
│   └── students/                # Student frontend
│       ├── students.html
│       ├── css/styles.css
│       └── js/
│           ├── api.js
│           ├── app.js
│           ├── config.js
│           └── render.js
├── data/
│   ├── meetings/
│   │   └── meetings.db          # Meetings (unencrypted)
│   ├── students/                # Student encrypted DBs
│   │   ├── index.db             # Central index (encrypted)
│   │   ├── index.salt           # Salt file for key derivation
│   │   └── {uuid}.sqlite        # Per-student DBs
│   └── certs/                   # SSL certificates (auto-generated)
├── libs/                        # Portable Python packages
├── README.md
└── .gitignore
```

---

## How It Works

### Launch the App
1. Open a terminal in the `crm-app` folder.
2. Run: `PYTHONPATH=./libs python3 main.py`
3. The server starts with HTTPS on `https://localhost:8080` and opens the dashboard.

### Meetings
- Click "Launch Meetings" to manage weekly meetings.
- Add meetings with name, day, time, type, Jitsi link, students, rate, homework, comments.
- Click a meeting name or countdown to join via Jitsi with low-bandwidth settings.
- Edit or delete meetings using the buttons on each entry.

### Students (requires master password)
- First visit: set a strong master password.
- Subsequent visits: log in with the master password (session token + SSL).
- Dashboard shows student list (searchable, filterable) and side panel with action items.
- Add Student form includes:
  - Name, location, timezone, age group, academic year
  - Contact: phone, Telegram, email
  - Minor checkbox (shows parent fields)
  - Rate (MMK)
  - Multiple custom meeting times (day, time, type, in-person flag)
  - Educational goals, behavioral comments, general comments
- Click a student card to view details: attendance log, payments, meetings summary.
- Action items side panel: add, toggle, delete global to-dos.

All student data is encrypted with SQLCipher. The central index database is encrypted with a key derived from the master password. Each student's database has its own random key, stored inside the index.

---

## Installation & Setup

### Prerequisites
- Ubuntu-based Linux (tested on Linux Mint 22.3)
- Python 3.6+
- Brave or Firefox browser
- System library: `libsqlcipher-dev`

### One-time setup
1. Copy the `crm-app` folder to your USB drive.
2. Install system dependency: `sudo apt install libsqlcipher-dev`
3. Navigate to the folder: `cd /path/to/crm-app`
4. Create portable library folder and install packages:
   ```bash
   mkdir -p libs
   pip install --target=./libs pysqlcipher3 cryptography
   ```
5. Run the app once to generate SSL certificates:
   ```bash
   PYTHONPATH=./libs python3 main.py
   ```
6. Install the generated local CA certificate into your system trust store:
   ```bash
   sudo cp data/certs/ca.crt /usr/local/share/ca-certificates/crm-ca.crt
   sudo update-ca-certificates
   ```
   Restart your browser afterwards.

### Running normally
```bash
cd /path/to/crm-app
PYTHONPATH=./libs python3 main.py
```
Open `https://localhost:8080/launch/index.html` (or let the launcher open it).

---

## Security Model

- **Transport security**: all student traffic is HTTPS with per-session server certificates signed by a local CA. No plain HTTP for student endpoints.
- **Authentication**: master password hashed with scrypt, session token required for all student API calls. Password expires every 30 days, history prevents reuse.
- **Encryption at rest**: student index database encrypted with key derived from master password. Each student database encrypted with a unique random key, stored inside the encrypted index.
- **Meetings database** remains unencrypted (no sensitive personal data).
- **No internet connection required**: everything runs locally; no data leaves the USB drive.

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

### Phase 2: Client Management (In Progress)
- [x] Encrypted per-student databases
- [x] Master password + SSL authentication
- [x] Student list view with search and filters
- [x] Full student profile (contact, meetings, goals, comments)
- [x] Attendance logging
- [x] Payment records (manual, receipt BLOB ready)
- [x] Global action items
- [ ] Link students to existing meetings
- [ ] Attendance marking from meeting view
- [ ] Payment receipt OCR
- [ ] Teacher availability / booking

### Phase 3: Telegram Bot
- [ ] Deploy bot to Render (free tier)
- [ ] Burmese language support
- [ ] FAQ automation
- [ ] Scheduling assistance

### Phase 4: Analytics
- [ ] Attendance reports
- [ ] Revenue summaries
- [ ] Export to CSV/PDF

### Phase 5: Scripts & Automation
- [ ] FAQ database
- [ ] Funnels and templates
- [ ] Automated reminders

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

# Stage all changes
git add -A

# Commit
git commit -m "Description"

# Push to GitHub
git push origin main
```

---

## License

*Built for teachers in Myanmar with limited internet connectivity.*
```
