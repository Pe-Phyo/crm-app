#  CRM App - Meeting Launcher

A lightweight, privacy-focused meeting management system for teachers with limited internet connectivity.

## Project Overview

This is a modular CRM application that handles:
- **Meeting Launcher** (Local): One-click Jitsi join with low-bandwidth settings
- **Calendar Integration** (Local): Sync with your existing calendar application
- **Telegram Bot** (Future): Automated FAQs, scheduling assistance, student communication
- **Cloud Deployment** (Future): Free 24/7 hosting on Render

## Features

### Current Phase: Meeting Launcher
- One-click meeting joining via Brave browser
- Low bandwidth by default (video off, mic off, skip pre-join)
- Works entirely offline (no internet needed for the dashboard)
- Data stored locally - full privacy
- No credit card required - completely free

### Future Phases
- **Telegram Bot**: Burmese-language support, FAQ automation, scheduling assistance
- **Cloud Sync**: Optional backup to Render free tier (no credit card)
- **Calendar Integration**: Direct sync with GNOME Calendar or other CalDAV applications
- **Client Management**: Track student names, phone numbers, enrollment types

## Tech Stack

### Local Components
| Component | Technology | Why |
|-----------|------------|-----|
| Interface | HTML + CSS + JavaScript | No dependencies, works in any browser |
| Data | Local calendar (GNOME Calendar / CalDAV) | Existing, privacy-preserving, no new format |
| Browser | Brave | Privacy-focused, Chromium-based for Jitsi |
| Version Control | Git | Local repository on thumb drive |

### Future Components
| Component | Technology | Why |
|-----------|------------|-----|
| Telegram Bot | Python + python-telegram-bot | Open source, well-documented |
| LLM Integration | Hugging Face (Padauk) or Ollama | Burmese language support |
| Hosting | Render (free tier) | No credit card required, 24/7 uptime |

## Project Structure
crm-app/
├── index.html # Main dashboard
├── styles.css # Dark theme styling
├── app.js # Meeting logic and UI handling
├── README.md # This file
└── .gitignore # Git exclusions

text

## How It Works

1. Open `index.html` in Brave browser
2. The dashboard reads your calendar events
3. Each meeting shows as a card with name, time, and a "Join" button
4. Click "Join" → Opens Jitsi with low-bandwidth settings

## Data Storage

### Option 1: GNOME Calendar (Recommended for Linux Mint)
- Stores meetings in local CalDAV database
- Accessible via SQLite directly
- Your existing calendar app handles all updates

### Option 2: CalDAV (Future)
- Sync with any CalDAV server
- Cross-platform compatibility
- No proprietary formats

### Option 3: Local ICS File (Fallback)
- Simple iCalendar format
- Export from any calendar app
- Easy to edit in text editor

## Installation & Setup

### Prerequisites
- Linux Mint 22.3 (or any Ubuntu-based)
- Brave browser (recommended) or Firefox
- VS Code (optional but recommended)

### Setup
1. Clone or copy this folder to your thumb drive
2. Open `index.html` in Brave
3. Edit your calendar settings (see configuration below)

## Configuration

### Calendar Data Fields
| Field | Description |
|-------|-------------|
| Date | Meeting date |
| Time | Meeting start time |
| Customer Name | Student/client name |
| Phone Number | Contact number |
| Meeting Link | Jitsi URL or other meeting link |
| Enrollment Type | Class type or package (e.g., "Monthly", "Trial") |

### Jitsi Low-Bandwidth Settings
Each meeting link automatically includes:
#config.prejoinPageEnabled=false
&config.startWithVideoMuted=true
&config.startWithAudioMuted=true

text

## Roadmap

### Phase 1: Meeting Launcher (Current)
- [x] Basic dashboard interface
- [ ] Read data from local calendar
- [ ] One-click join with low bandwidth
- [ ] Display meeting cards with all fields

### Phase 2: Calendar Integration
- [ ] Connect to GNOME Calendar
- [ ] Auto-sync events
- [ ] Add/edit meetings from dashboard

### Phase 3: Telegram Bot
- [ ] Deploy bot to Render (free tier)
- [ ] Burmese language support
- [ ] FAQ automation
- [ ] Scheduling assistance

### Phase 4: CRM Features
- [ ] Student database
- [ ] Payment tracking
- [ ] Session notes
- [ ] Analytics

## Privacy & Security

- **Data never leaves your computer** (Phase 1-2)
- **No credit card required** for any service
- **No tracking or analytics** built into the app
- **Open source** - you can inspect everything
- **Brave browser** for enhanced privacy

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Local dashboard | $0 |
| GNOME Calendar | $0 (pre-installed on Linux Mint) |
| Brave browser | $0 |
| Git & GitHub | $0 |
| Render hosting (future) | $0 (free tier) |
| Hugging Face API (future) | $0 (free tier) |
| **Total** | **$0** |

## License

Open Source - Use freely, modify as needed.

## Contributing

This is a personal project but open to feedback. Submit issues or suggestions via GitHub.

---

*Built for teachers with limited internet connectivity in Myanmar*