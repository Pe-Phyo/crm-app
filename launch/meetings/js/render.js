// ============================================================
//  RENDER FUNCTIONS
// ============================================================

import { JITSI_PARAMS, DAYS } from './config.js';

// ============================================================
//  HELPERS
// ============================================================

function getTodayName() {
    const now = new Date();
    return DAYS[now.getDay()];
}

function getCurrentTime() {
    const now = new Date();
    return now.getHours() * 60 + now.getMinutes();
}

function isMeetingCurrent(meeting) {
    const [h, m] = meeting.time.split(':').map(Number);
    const meetingStart = h * 60 + m;
    const now = getCurrentTime();
    return now >= meetingStart && now < meetingStart + 55;
}

function isMeetingUpcoming(meeting, currentMeetingId) {
    if (currentMeetingId && meeting.id === currentMeetingId) return false;
    const [h, m] = meeting.time.split(':').map(Number);
    const meetingStart = h * 60 + m;
    const now = getCurrentTime();
    return meetingStart > now;
}

// ============================================================
//  RENDER CALENDAR
// ============================================================

export function renderCalendar(onJoin, onEdit, onDelete, meetings) {
    const grid = document.getElementById('calendarGrid');
    grid.innerHTML = '';

    const todayName = getTodayName();

    // Reorder days: today first, then the rest in order
    const todayIndex = DAYS.indexOf(todayName);
    const orderedDays = [
        ...DAYS.slice(todayIndex),
        ...DAYS.slice(0, todayIndex)
    ];

    // Find current and upcoming meetings for today
    const todayMeetings = meetings.filter(m => m.day === todayName)
        .sort((a, b) => a.time.localeCompare(b.time));

    let currentMeeting = null;
    let upcomingMeeting = null;

    for (const m of todayMeetings) {
        if (isMeetingCurrent(m)) {
            currentMeeting = m;
            break;
        }
    }

    if (!currentMeeting) {
        for (const m of todayMeetings) {
            if (isMeetingUpcoming(m, null)) {
                upcomingMeeting = m;
                break;
            }
        }
    } else {
        const currentIdx = todayMeetings.indexOf(currentMeeting);
        for (let i = currentIdx + 1; i < todayMeetings.length; i++) {
            if (isMeetingUpcoming(todayMeetings[i], currentMeeting.id)) {
                upcomingMeeting = todayMeetings[i];
                break;
            }
        }
    }

    // Render each day
    orderedDays.forEach(day => {
        const isToday = day === todayName;
        const dayMeetings = meetings.filter(m => m.day === day)
            .sort((a, b) => a.time.localeCompare(b.time));

        const cell = document.createElement('div');
        cell.className = `day-cell${isToday ? ' today' : ''}`;

        // Day header
        const header = document.createElement('div');
        header.className = 'day-header';
        header.innerHTML = `
            <span>${day}</span>
            <span class="day-number${isToday ? ' today-num' : ''}">${isToday ? 'Today' : ''}</span>
        `;
        cell.appendChild(header);

        if (dayMeetings.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'no-meetings';
            empty.textContent = '—';
            cell.appendChild(empty);
        } else {
            dayMeetings.forEach(m => {
                const entry = createMeetingEntry(
                    m,
                    onJoin,
                    onEdit,
                    onDelete,
                    currentMeeting,
                    upcomingMeeting
                );
                cell.appendChild(entry);
            });
        }

        grid.appendChild(cell);
    });
}

// ============================================================
//  CREATE MEETING ENTRY
// ============================================================

function createMeetingEntry(meeting, onJoin, onEdit, onDelete, currentMeeting, upcomingMeeting) {
    const entry = document.createElement('div');
    entry.className = 'meeting-entry';

    // Determine if this is current or upcoming
    let extraClass = '';
    let label = '';

    if (currentMeeting && meeting.id === currentMeeting.id) {
        extraClass = 'meeting-current';
        label = '<span class="badge-current">🔴 CURRENT</span> ';
    } else if (upcomingMeeting && meeting.id === upcomingMeeting.id) {
        extraClass = 'meeting-upcoming';
        label = '<span class="badge-upcoming">🔵 UPCOMING</span> ';
    }

    const typeLabel = meeting.type === 'private' ? 'Private' : 'Group';
    const typeClass = meeting.type === 'private' ? 'type-private' : 'type-group';
    const countClass = meeting.count > 10 ? 'count-high' : meeting.count >= 5 ? 'count-medium' : meeting.count >= 1 ? 'count-low' : 'count-zero';
    const participants = meeting.student_names ? meeting.student_names.length : 0;
    const rateDisplay = meeting.rate ? meeting.rate.toLocaleString() : '0';

    // Build student display
    let studentDisplay = '';
    if (meeting.student_names && meeting.student_names.length > 0) {
        studentDisplay = meeting.student_names.join(', ');
        if (studentDisplay.length > 30) {
            studentDisplay = studentDisplay.substring(0, 30) + '…';
        }
    }

    // Build entry HTML
    entry.innerHTML = `
        <div class="entry-top">
            <span class="entry-time">${meeting.time}</span>
            <span class="entry-name" data-id="${meeting.id}">${label}${meeting.nickname}</span>
            <span class="entry-type ${typeClass}">${typeLabel}</span>
            <span class="entry-participants">${participants} participant${participants > 1 ? 's' : ''}</span>
            <span class="entry-count ${countClass}" data-id="${meeting.id}">${meeting.count}</span>
            <span class="entry-rate">${rateDisplay}K</span>
        </div>
        <div class="entry-students">${studentDisplay}</div>
        ${meeting.homework ? `<div class="entry-homework">📖 ${meeting.homework}</div>` : ''}
        ${meeting.comments ? `<div class="entry-comments">💬 ${meeting.comments}</div>` : ''}
        <div class="entry-actions">
            <button class="entry-edit" data-id="${meeting.id}">✎</button>
            <button class="entry-delete" data-id="${meeting.id}">✕</button>
        </div>
    `;

    // Add extra class for current/upcoming
    if (extraClass) {
        entry.classList.add(extraClass);
    }

    // Attach event listeners
    const nameEl = entry.querySelector('.entry-name');
    const countEl = entry.querySelector('.entry-count');
    const editBtn = entry.querySelector('.entry-edit');
    const deleteBtn = entry.querySelector('.entry-delete');

    nameEl.addEventListener('click', () => onJoin(meeting.id));
    countEl.addEventListener('click', () => onJoin(meeting.id));
    editBtn.addEventListener('click', (e) => { e.stopPropagation(); onEdit(meeting.id); });
    deleteBtn.addEventListener('click', (e) => { e.stopPropagation(); onDelete(meeting.id); });

    return entry;
}