import { escapeHtml } from '../../students/js/utils/helpers.js';

export function renderList(templates, teachers, onDetailClick) {
    const container = document.getElementById('templatesList');
    if (!templates.length) {
        container.innerHTML = '<div class="placeholder-box">No templates found.</div>';
        return;
    }

    container.innerHTML = templates.map(t => {
        const teacher = teachers.find(te => te.uuid === t.teacher_id);
        const teacherName = teacher ? (teacher.display_name || teacher.username) : t.teacher_id;
        const schedule = JSON.parse(t.schedule_json || '[]');
        const scheduleStr = schedule.map(s => `${s.day} ${s.time}`).join(', ');
        return `
            <div class="template-card" data-id="${t.id}">
                <div class="template-card-line1">
                    <span style="flex:1;">${escapeHtml(t.name)}</span>
                    <span class="status-badge active">${t.type}</span>
                </div>
                <div class="template-card-line2">
                    <span>👤 ${escapeHtml(teacherName)}</span>
                    <span>📚 ${t.lesson_count} lessons</span>
                    <span>💰 ${t.default_rate} MMK</span>
                    <span>🔄 ${t.billing_cycle}</span>
                    <span>📅 ${scheduleStr || '—'}</span>
                </div>
            </div>
        `;
    }).join('');

    container.querySelectorAll('.template-card').forEach(card => {
        card.addEventListener('click', () => onDetailClick(card.dataset.id, templates, teachers));
    });
}