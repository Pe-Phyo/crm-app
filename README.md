Here's your updated README reflecting the current state of the project.

---

## 📄 Updated README.md

```markdown
# CRM App - Meeting Launcher

A lightweight, privacy-focused meeting management system for teachers with limited internet connectivity.

---

## Project Overview

This is a modular CRM application that handles:
- **Meeting Launcher** (Local): One-click Jitsi join with low-bandwidth settings
- **Database Storage** (SQLite): Persistent data storage on thumb drive
- **Telegram Bot** (Future): Automated FAQs, scheduling assistance, student communication
- **Client Management** (Future): Individual client profiles with custom data
- **Analytics** (Future): Track attendance, revenue, and class metrics

---

## Current Features

### Meeting Launcher
- **One-click joining** via Brave browser (no extra clicks)
- **Low bandwidth by default** (video off, mic off, skip pre-join screen)
- **Weekly calendar view** (vertical layout, current day on top)
- **Current meeting highlighted in green** (happening now)
- **Upcoming meeting highlighted in yellow** (next meeting after current time)
- **Private & Group classes** (group capacity: 9 students)
- **Countdown tracker** (tracks remaining lessons per meeting)
- **Rate tracking** (price per lesson in MMK)
- **Homework & comments fields** (per meeting)
- **Student management** (add/remove students per meeting)
- **Data persistence** (SQLite database on thumb drive)
- **No credit card required** – completely free
- **Works offline** (no internet needed for the dashboard)

### Data Storage
- **SQLite database** for all meetings
- **Individual student databases** (future: each client gets their own .db file)
- **Scripts folder** (future: FAQs, funnels, templates)
- **Analytics folder** (future: weekly/monthly reports)

---

## Tech Stack

### Current Components

| Component | Technology | Why |
|-----------|------------|-----|
| **Backend Server** | Python + SQLite | Lightweight, runs on thumb drive |
| **Frontend** | HTML + CSS + JavaScript (Modular) | No dependencies, works in any browser |
| **Browser** | Brave | Privacy-focused, Chromium-based for Jitsi |
| **Version Control** | Git | Local repository on thumb drive |
| **Database** | SQLite | File-based, secure, portable |

### Future Components

| Component | Technology | Why |
|-----------|------------|-----|
| Telegram Bot | Python + python-telegram-bot | Open source, well-documented |
| LLM Integration | Hugging Face (Padauk) or Ollama | Burmese language support |
| Cloud Sync | Render (free tier) | Optional 24/7 backup |

---

## Project Structure

```
crm-app/
├── main.py                          # Server launcher (run this)
├── launch/
│   ├── index.html                   # Main dashboard
│   └── meetings/
│       ├── meetings.html            # Meeting view
│       ├── css/
│       │   └── styles.css           # Dark theme (VS Code style)
│       └── js/
│           ├── api.js               # API calls to backend
│           ├── app.js               # App controller
│           ├── config.js            # Constants
│           └── render.js            # UI rendering
├── data/
│   └── meetings/
│       └── meetings.db              # SQLite database (auto-created)
├── README.md                        # This file
└── .gitignore                       # Git exclusions
```

---

## How It Works

### Launch the App

1. **Run `main.py`** from the terminal
2. The server starts and opens the dashboard in your browser
3. Click "Launch Meetings" to open the meeting view

### Add a Meeting

1. Click **"Add"** button
2. Fill in the meeting details:
   - Name (e.g., "Math Group A")
   - Day (Sunday–Saturday)
   - Time (e.g., 09:00)
   - Type (Private or Group)
   - Students (type each name, press Enter to add)
   - Jitsi Link (e.g., `https://meet.jit.si/room`)
   - Rate (price per lesson in MMK)
   - Homework (optional)
   - Comments (optional)
3. Click **"Add"** – the meeting appears in the calendar

### Join a Meeting

- Click the **meeting name** or the **countdown number**
- Jitsi opens in a new tab with:
  - Low bandwidth mode
  - Camera off
  - Microphone off
  - Pre-join screen skipped

### Edit a Meeting

- Click the **✎** button on any meeting
- Update the fields
- Click **"Save"**

### Delete a Meeting

- Click the **✕** button on any meeting
- Confirm deletion

### Track Progress

- Each meeting has a **countdown** (starts at 8 lessons)
- Each time you click a meeting, the count decreases by 1
- Click **"Reset"** to reset all counts to 8

---

## Data Storage

### Meetings Database
- **Location:** `data/meetings/meetings.db`
- **Format:** SQLite (secure, not plain text)
- **Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | TEXT | Unique meeting ID |
| `day` | TEXT | Sunday–Saturday |
| `time` | TEXT | HH:MM (24-hour) |
| `nickname` | TEXT | Display name |
| `type` | TEXT | 'private' or 'group' |
| `student_ids` | TEXT | Comma-separated student IDs |
| `student_names` | TEXT | Comma-separated student names |
| `link` | TEXT | Jitsi URL |
| `count` | INTEGER | Lessons remaining (default: 8) |
| `rate` | INTEGER | Price per lesson (MMK) |
| `homework` | TEXT | Homework assignment |
| `comments` | TEXT | Notes for next lesson |
| `attendance` | TEXT | Comma-separated student IDs who attended |
| `created` | TEXT | Timestamp |
| `updated` | TEXT | Timestamp |

---

## Future Data Architecture

```
data/
├── meetings/
│   └── meetings.db                # All meetings
├── students/
│   ├── stu_xxxxxx.db              # Individual student profile
│   ├── stu_yyyyyy.db              # Individual student profile
│   └── stu_zzzzzz.db              # Individual student profile
├── scripts/
│   ├── faqs/
│   │   ├── welcome.db
│   │   └── homework-reminder.db
│   ├── funnels/
│   │   └── new-student.db
│   └── templates/
│       └── class-reminder.db
└── analytics/
    ├── weekly/
    │   └── 2025-w1.db
    └── monthly/
        └── 2025-01.db
```

---

## Installation & Setup

### Prerequisites
- Linux Mint 22.3 (or any Ubuntu-based)
- Python 3.6+
- Brave browser (recommended) or Firefox
- Git (optional, for version control)

### Setup

1. **Copy the `crm-app` folder** to your thumb drive
2. **Open a terminal** in the `crm-app` folder
3. **Run the launcher:**
   ```bash
   python3 main.py
   ```
4. **Open your browser** to `http://localhost:8080/launch/index.html`
5. **Click "Launch Meetings"** to start

---

## Jitsi Low-Bandwidth Settings

Each meeting link automatically includes:

```
#config.prejoinConfig.enabled=false
&config.startWithVideoMuted=true
&config.startWithAudioMuted=true
&config.disableLobby=true
```

This ensures:
- No "Join" button to click
- Camera and microphone off
- No "Start Meeting" button (lobby bypassed)
- You go straight into the meeting

---

## Roadmap

### Phase 1: Meeting Launcher ✅ (Complete)
- [x] Vertical weekly calendar
- [x] Current day on top
- [x] One-click join with low bandwidth
- [x] Private & Group classes
- [x] Countdown tracker (8 lessons)
- [x] Rate tracking (MMK)
- [x] Homework & comments fields
- [x] SQLite database storage
- [x] Edit & delete meetings
- [x] VS Code dark theme
- [x] Current meeting (green) and upcoming (yellow) highlighting

### Phase 2: Client Management (Next)
- [ ] Individual client profiles (SQLite files)
- [ ] Client list view
- [ ] Link clients to meetings
- [ ] Client notes and history

### Phase 3: Telegram Bot
- [ ] Deploy bot to Render (free tier)
- [ ] Burmese language support
- [ ] FAQ automation
- [ ] Scheduling assistance

### Phase 4: Analytics
- [ ] Attendance tracking
- [ ] Revenue reports
- [ ] Class summaries
- [ ] Export to CSV/PDF

### Phase 5: Scripts & Automation
- [ ] FAQs database
- [ ] Funnels and templates
- [ ] Automated reminders
- [ ] Client communication

---

## Privacy & Security

- **Data stays on your thumb drive** – never leaves your control
- **SQLite databases** – secure, not plain text
- **No credit card required** – completely free
- **No tracking or analytics** – built-in privacy
- **Open source** – inspect everything
- **Brave browser** – enhanced privacy

---

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Meeting launcher | $0 |
| SQLite database | $0 |
| Brave browser | $0 |
| Git & GitHub | $0 |
| Python server | $0 |
| Render hosting (future) | $0 (free tier) |
| **Total** | **$0** |

---

## Git Workflow

```bash
# Check status
git status

# Add changes
git add .

# Commit changes
git commit -m "Description of changes"

# View history
git log --oneline
```

---

## License

Open Source – Use freely, modify as needed.

---

## Contributing

This is a personal project but open to feedback. Submit issues or suggestions via GitHub.

---

*Built for teachers with limited internet connectivity in Myanmar*
```

---

## ✅ Summary of Changes

| Section | What Was Updated |
|---------|------------------|
| **Current Features** | Now accurately reflects actual features (vertical calendar, SQLite, current/upcoming highlighting, etc.) |
| **Tech Stack** | Added Python + SQLite as current components |
| **Project Structure** | Updated to match actual folder structure |
| **How It Works** | Complete rewrite with actual workflow |
| **Data Storage** | Now reflects SQLite, future student/scripts/analytics folders |
| **Jitsi Settings** | Updated to working parameters (`prejoinConfig.enabled=false`) |
| **Roadmap** | Marked Phase 1 as complete |
| **Git Workflow** | Added basic Git commands |
| **Installation** | Updated to use `python3 main.py` |

---

**Save this as `README.md` and replace your current one.**
