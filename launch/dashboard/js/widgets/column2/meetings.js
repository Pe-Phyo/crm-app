import { apiCall } from '../../api.js';

// ------------------ Day helpers ------------------
const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

function getTodayName() {
    return DAYS[new Date().getDay()];
}

// ------------------ Main render ------------------
export async function render(container) {
    container.innerHTML = `
        <div class="day-controls">
            <button class="btn btn-sm" id="meeting-prev-day">◀</button>
            <span id="meeting-day-label" style="margin:0 8px;"></span>
            <button class="btn btn-sm" id="meeting-next-day">▶</button>
        </div>
        <div id="meeting-list"></div>
    `;

    const dayLabel = container.querySelector('#meeting-day-label');
    const listEl = container.querySelector('#meeting-list');
    const prevBtn = container.querySelector('#meeting-prev-day');
    const nextBtn = container.querySelector('#meeting-next-day');

    let currentDay = getTodayName();
    let meetings = [];

    // Load all meetings once
    let url = '/api/meetings';
    const profile = window.__dashboardProfile;
    if (profile && profile.role === 'teacher' && profile.uuid) {
        url = `/api/meetings?teacher_id=${encodeURIComponent(profile.uuid)}`;
    }

    try {
        meetings = await apiCall('GET', url);
    } catch (e) {
        listEl.innerHTML = '<p style="color:var(--muted);">Could not load meetings.</p>';
        return;
    }

    // --- Day navigation ---
    function dayIndex(day) { return DAYS.indexOf(day); }
    function offsetDay(day, offset) {
        const idx = (dayIndex(day) + offset + 7) % 7;
        return DAYS[idx];
    }

    function renderDay() {
        dayLabel.textContent = currentDay;
        const dayMeetings = meetings
            .filter(m => m.day === currentDay)
            .sort((a, b) => a.time.localeCompare(b.time));

        if (dayMeetings.length === 0) {
            listEl.innerHTML = '<p style="color:var(--muted);">No meetings today.</p>';
            return;
        }
        listEl.innerHTML = dayMeetings.map(m => {
            const participants = m.student_names ? m.student_names.length : 0;
            const rateDisplay = m.rate ? m.rate.toLocaleString() : '0';
            const typeLabel = m.type === 'private' ? 'Private' : 'Group';
            const typeClass = m.type === 'private' ? 'type-private' : 'type-group';
            return `
                <div class="meeting-entry" data-id="${m.id}">
                    <div class="entry-top">
                        <span class="entry-time">${m.time}</span>
                        <span class="entry-name">${m.nickname}</span>
                        <span class="entry-type ${typeClass}">${typeLabel}</span>
                        <span class="entry-participants">${participants} participant${participants!==1?'s':''}</span>
                        <span class="entry-rate">${rateDisplay}K</span>
                    </div>
                    <div class="entry-students">${m.student_names ? m.student_names.join(', ') : ''}</div>
                    ${m.homework ? `<div class="entry-homework">📖 ${m.homework}</div>` : ''}
                    ${m.comments ? `<div class="entry-comments">💬 ${m.comments}</div>` : ''}
                    <div class="entry-actions">
                        <button class="entry-edit btn btn-sm" data-id="${m.id}">✎</button>
                        <button class="entry-delete btn btn-sm btn-danger" data-id="${m.id}">✕</button>
                    </div>
                </div>
            `;
        }).join('');

        // Attach event listeners
        listEl.querySelectorAll('.entry-name').forEach(el => {
            el.addEventListener('click', () => {
                const id = el.closest('.meeting-entry').dataset.id;
                const meet = meetings.find(m => m.id === id);
                if (meet && meet.link) window.open(meet.link, '_blank');
            });
        });

        listEl.querySelectorAll('.entry-edit').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.closest('.meeting-entry').dataset.id;
                const meet = meetings.find(m => m.id === id);
                if (meet) openEditModal(meet);
            });
        });

        listEl.querySelectorAll('.entry-delete').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.closest('.meeting-entry').dataset.id;
                if (!confirm('Delete this meeting?')) return;
                try {
                    await apiCall('DELETE', `/api/meetings/${id}`);
                    meetings = meetings.filter(m => m.id !== id);
                    renderDay();
                } catch (e) {
                    alert('Delete failed');
                }
            });
        });
    }

    prevBtn.addEventListener('click', () => {
        currentDay = offsetDay(currentDay, -1);
        renderDay();
    });

    nextBtn.addEventListener('click', () => {
        currentDay = offsetDay(currentDay, 1);
        renderDay();
    });

    renderDay();   // initial

    // ---- Edit Modal (appended to body) ----
    function openEditModal(meeting) {
        // Remove any existing modal
        const old = document.getElementById('meeting-edit-modal');
        if (old) old.remove();

        const modalHtml = `
            <div class="modal-overlay active" id="meeting-edit-modal">
                <div class="modal" style="max-width:500px;">
                    <h3>Edit Meeting: ${meeting.nickname}</h3>
                    <label>Homework</label>
                    <input type="text" id="edit-homework" value="${escapeHtml(meeting.homework || '')}" placeholder="Chapter 3 exercises">
                    <label>Comments for Next Lesson</label>
                    <textarea id="edit-comments" rows="2" placeholder="Review past tense...">${escapeHtml(meeting.comments || '')}</textarea>
                    <div class="modal-actions" style="justify-content:space-between;">
                        <button class="btn btn-danger" id="edit-delete-btn">Delete</button>
                        <div>
                            <button class="btn btn-secondary" id="edit-cancel-btn">Cancel</button>
                            <button class="btn btn-success" id="edit-save-btn">Save</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const modalEl = document.getElementById('meeting-edit-modal');
        const closeModal = () => modalEl.remove();

        modalEl.querySelector('#edit-cancel-btn').addEventListener('click', closeModal);
        modalEl.querySelector('#edit-delete-btn').addEventListener('click', async () => {
            if (!confirm('Delete this meeting?')) return;
            try {
                await apiCall('DELETE', `/api/meetings/${meeting.id}`);
                meetings = meetings.filter(m => m.id !== meeting.id);
                closeModal();
                renderDay();
            } catch (e) {
                alert('Delete failed');
            }
        });

        modalEl.querySelector('#edit-save-btn').addEventListener('click', async () => {
            const homework = modalEl.querySelector('#edit-homework').value.trim();
            const comments = modalEl.querySelector('#edit-comments').value.trim();
            try {
                await apiCall('PUT', `/api/meetings/${meeting.id}`, { homework, comments });
                // Update local cache
                const m = meetings.find(m => m.id === meeting.id);
                if (m) {
                    m.homework = homework;
                    m.comments = comments;
                }
                closeModal();
                renderDay();
            } catch (e) {
                alert('Update failed');
            }
        });

        // Close on overlay click
        modalEl.addEventListener('click', (e) => {
            if (e.target === modalEl) closeModal();
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

export { render as renderMeetings };