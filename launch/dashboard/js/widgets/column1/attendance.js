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
        // 1. Get today's meetings
        const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
        const allMeetings = await apiCall('GET', '/api/meetings');
        const todayMeetings = allMeetings.filter(m => m.day === today);

        // 2. Collect unique student names
        const uniqueStudents = [];
        const seen = new Set();
        todayMeetings.forEach(m => {
            if (m.student_names) {
                m.student_names.forEach(name => {
                    if (!seen.has(name)) {
                        seen.add(name);
                        uniqueStudents.push(name);
                    }
                });
            }
        });

        if (uniqueStudents.length === 0) {
            listEl.innerHTML = '<p style="color:var(--muted);">No students today.</p>';
            return;
        }

        // 3. Fetch today's attendance (stub – returns empty array if endpoint missing)
        let attendanceRecords = [];
        try {
            attendanceRecords = await apiCall('GET', `/api/attendance?date=${new Date().toISOString().split('T')[0]}`);
        } catch (e) {
            // Endpoint not implemented yet – ignore
        }

        const presentSet = new Set(attendanceRecords.map(r => r.student_name));

        // 4. Render list with checkboxes
        listEl.innerHTML = uniqueStudents.map(name => `
            <div class="attendance-row">
                <input type="checkbox" class="attendance-check" data-student="${escapeHtml(name)}" ${presentSet.has(name) ? 'checked' : ''}>
                <span>${escapeHtml(name)}</span>
            </div>
        `).join('');

        // 5. Handle checkbox changes
        listEl.querySelectorAll('.attendance-check').forEach(cb => {
            cb.addEventListener('change', async () => {
                const student = cb.dataset.student;
                const status = cb.checked ? 'present' : 'absent';
                try {
                    await apiCall('POST', '/api/attendance/mark', {
                        student_name: student,
                        date: new Date().toISOString().split('T')[0],
                        status: status
                    });
                } catch (e) {
                    // Revert checkbox if save fails (endpoint not ready)
                    cb.checked = !cb.checked;
                    console.warn('Attendance save failed – backend not ready?');
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