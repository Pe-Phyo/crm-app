import { escapeHtml } from '../../students/js/utils/helpers.js';
import { deleteTemplate } from './api.js';
import { openEditForm } from './form.js';
import { loadTemplates, getTemplateList, getTeacherList } from './app.js';

const detailModal = document.getElementById('detailModal');
const detailContent = document.getElementById('detailContent');

export function openDetail(id) {
    const templates = getTemplateList();
    const t = templates.find(t => t.id == id);
    if (!t) return;

    const teachers = getTeacherList();
    const teacher = teachers.find(te => te.uuid === t.teacher_id);
    const teacherName = teacher ? (teacher.display_name || teacher.username) : t.teacher_id;
    const schedule = JSON.parse(t.schedule_json || '[]');
    const scheduleStr = schedule.map(s => `${s.day} ${s.time}`).join(', ') || '—';

    detailContent.innerHTML = `
        <h3>${escapeHtml(t.name)}</h3>
        <p><strong>Teacher:</strong> ${escapeHtml(teacherName)}</p>
        <p><strong>Type:</strong> ${t.type}</p>
        <p><strong>Lesson Count:</strong> ${t.lesson_count}</p>
        <p><strong>Default Rate:</strong> ${t.default_rate} MMK</p>
        <p><strong>Subject:</strong> ${t.subject || '—'}</p>
        <p><strong>Billing Cycle:</strong> ${t.billing_cycle}</p>
        <p><strong>Schedule:</strong> ${scheduleStr}</p>
        <div class="modal-actions">
            <button id="editTemplateBtn" class="btn btn-primary">Edit</button>
            <button id="deleteTemplateBtn" class="btn btn-danger">Delete</button>
        </div>
    `;
    detailModal.classList.add('active');

    document.getElementById('editTemplateBtn').addEventListener('click', () => {
        detailModal.classList.remove('active');
        openEditForm(t, getTeacherList());
    });
    document.getElementById('deleteTemplateBtn').addEventListener('click', async () => {
        if (confirm('Delete this template?')) {
            try {
                await deleteTemplate(id);
                detailModal.classList.remove('active');
                loadTemplates();
            } catch (err) {
                alert('Delete failed: ' + err.message);
            }
        }
    });
}