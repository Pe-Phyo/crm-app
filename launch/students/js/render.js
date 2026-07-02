export function renderStudentList(students, onStudentClick) {
    const container = document.getElementById('studentList');
    if (!students.length) {
        container.innerHTML = '<div class="placeholder-box">No students yet.</div>';
        return;
    }

    container.innerHTML = students.map(s => {
        const lastPayment = s.last_payment_date || 'Never';
        const att = s.attendance_percentage.toFixed(0);
        return `
        <div class="student-card" data-uuid="${s.uuid}">
            <div class="student-card-header">
                <strong>${escapeHtml(s.name)}</strong>
                <span class="status-badge ${s.status}">${s.status}</span>
            </div>
            <div class="student-card-body">
                <span>📍 ${escapeHtml(s.location) || '—'}</span>
                <span>💰 ${s.rate.toLocaleString()} K</span>
                <span>📅 Last payment: ${lastPayment}</span>
                <span>📊 Attendance: ${att}%</span>
                <span>🕒 ${s.meeting_times_summary || 'No meetings'}</span>
            </div>
        </div>`;
    }).join('');

    // Attach click handlers
    container.querySelectorAll('.student-card').forEach(card => {
        card.addEventListener('click', () => {
            const uuid = card.dataset.uuid;
            onStudentClick(uuid);
        });
    });
}

export function renderActions(actions, onToggle, onDelete, onAdd) {
    const container = document.getElementById('actionItems');
    let html = '<div style="display:flex;gap:5px;margin-bottom:10px;">';
    html += '<input type="text" id="newActionInput" placeholder="New action..." style="flex:1;padding:5px;border-radius:4px;border:1px solid #475569;background:#0f172a;color:#e2e8f0;">';
    html += '<button id="addActionBtn" class="btn btn-primary" style="padding:5px 10px;">+</button>';
    html += '</div>';

    if (!actions.length) {
        html += '<div class="placeholder-box">No actions</div>';
    } else {
        html += actions.map(a => `
            <div class="action-item ${a.done ? 'done' : ''}" data-id="${a.id}">
                <span class="action-text">${escapeHtml(a.text)}</span>
                <div class="action-btns">
                    <button class="btn-toggle" data-id="${a.id}">${a.done ? '✅' : '⬜'}</button>
                    <button class="btn-delete" data-id="${a.id}">🗑️</button>
                </div>
            </div>
        `).join('');
    }

    container.innerHTML = html;

    // Add new action
    document.getElementById('addActionBtn').addEventListener('click', () => {
        const input = document.getElementById('newActionInput');
        const text = input.value.trim();
        if (text) {
            onAdd(text);
            input.value = '';
        }
    });

    // Toggle & delete
    container.querySelectorAll('.btn-toggle').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            const item = actions.find(a => a.id === id);
            onToggle(id, !item.done);
        });
    });

    container.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            onDelete(id);
        });
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}