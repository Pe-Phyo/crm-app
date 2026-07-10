import { apiCall } from '../../api.js';

export async function render(container) {
    container.innerHTML = `
        <div class="widget-header">
            <span class="widget-title">Today's Attendance</span>
        </div>
        <div id="attendance-list"></div>
    `;

    const listEl = container.querySelector('#attendance-list');

    try {
        const todayDay = new Date().toLocaleDateString('en-US', { weekday: 'long' });
        const todayISO = new Date().toISOString().split('T')[0];

        // 1. Get today's meetings
        const allMeetings = await apiCall('GET', '/api/meetings');
        const todayMeetings = allMeetings.filter(m => m.day === todayDay);

        // 2. Build list of unique students with their UUIDs
        //    meetings have student_ids (array of UUIDs) and student_names (array of names)
        const studentMap = new Map(); // uuid -> { name, meetingIds }
        todayMeetings.forEach(meeting => {
            if (meeting.student_ids && meeting.student_names) {
                meeting.student_ids.forEach((uuid, idx) => {
                    const name = meeting.student_names[idx] || uuid;
                    if (!studentMap.has(uuid)) {
                        studentMap.set(uuid, { name, meetingIds: [] });
                    }
                    studentMap.get(uuid).meetingIds.push(meeting.id);
                });
            }
        });

        if (studentMap.size === 0) {
            listEl.innerHTML = '<p style="color:var(--muted);">No students today.</p>';
            return;
        }

        // 3. For each student, fetch attendance and see if marked today
        const students = [];
        for (const [uuid, info] of studentMap.entries()) {
            let records = [];
            try {
                records = await apiCall('GET', `/teacher/attendance?student_uuid=${encodeURIComponent(uuid)}`);
            } catch (e) {
                // ignore
            }
            const presentToday = records.some(r => r.date === todayISO && r.status === 'present');
            students.push({
                uuid,
                name: info.name,
                presentToday,
                meetingIds: info.meetingIds   // first meeting ID could be used for marking
            });
        }

        // 4. Render list with checkboxes
        listEl.innerHTML = students.map(s => `
            <div class="attendance-row">
                <input type="checkbox" class="attendance-check"
                       data-student-uuid="${escapeHtml(s.uuid)}"
                       data-meeting-id="${escapeHtml(s.meetingIds[0] || '')}"
                       ${s.presentToday ? 'checked' : ''}>
                <span>${escapeHtml(s.name)}</span>
            </div>
        `).join('');

        // 5. Handle checkbox changes
        listEl.querySelectorAll('.attendance-check').forEach(cb => {
            cb.addEventListener('change', async () => {
                const studentUuid = cb.dataset.studentUuid;
                const meetingId = cb.dataset.meetingId;
                const status = cb.checked ? 'present' : 'absent';
                try {
                    await apiCall('POST', '/teacher/attendance', {
                        student_uuid: studentUuid,
                        meeting_id: meetingId,
                        date: todayISO,
                        status: status
                    });
                } catch (e) {
                    cb.checked = !cb.checked; // revert on failure
                }
            });
        });

    } catch (e) {
        listEl.innerHTML = '<p style="color:var(--muted);">Could not load attendance data.</p>';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

export { render as renderAttendance };