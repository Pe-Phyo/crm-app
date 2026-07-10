import { apiCall } from '../../dashboard/js/api.js';

let teachers = [];
let templates = [];
let currentTemplateId = null;

const detailModal = document.getElementById('detailModal');
const detailContent = document.getElementById('detailContent');
const closeDetailBtn = document.getElementById('closeDetailBtn');

// ---------- Init ----------
document.addEventListener('DOMContentLoaded', () => {
    loadTeachers();
    document.getElementById('applyFilterBtn').addEventListener('click', loadTemplates);
    document.getElementById('addTemplateBtn').addEventListener('click', openAddForm);
    document.getElementById('backBtn').addEventListener('click', () => {
        window.location.href = '/launch/dashboard/dashboard.html';
    });
    closeDetailBtn.addEventListener('click', () => detailModal.classList.remove('active'));
    loadTemplates();
});

// ---------- Teachers ----------
async function loadTeachers() {
    try {
        const data = await apiCall('GET', '/api/staff/teachers');
        teachers = data.filter(t => t.role === 'teacher');
        const select = document.getElementById('teacherFilter');
        select.innerHTML = '<option value="">All Teachers</option>';
        teachers.forEach(t => {
            select.innerHTML += `<option value="${t.uuid}">${t.display_name || t.username}</option>`;
        });
    } catch (e) {
        console.error(e);
    }
}

// ---------- Templates ----------
async function loadTemplates() {
    const teacherId = document.getElementById('teacherFilter').value;
    let url = '/api/pricing/templates';
    if (teacherId) url += `?teacher_id=${encodeURIComponent(teacherId)}`;
    try {
        templates = await apiCall('GET', url);
        renderList();
    } catch (e) {
        alert('Failed to load templates: ' + e.message);
    }
}

function renderList() {
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
            <div class="staff-card" data-id="${t.id}">
                <div class="staff-card-header">
                    <strong>${escapeHtml(t.name)}</strong>
                    <span class="status-badge active">${t.type}</span>
                </div>
                <div class="staff-card-body">
                    <span>👤 ${escapeHtml(teacherName)}</span>
                    <span>📚 ${t.lesson_count} lessons</span>
                    <span>💰 ${t.default_rate} MMK</span>
                    <span>🔄 ${t.billing_cycle}</span>
                    <span>📅 ${scheduleStr || '—'}</span>
                </div>
            </div>
        `;
    }).join('');

    container.querySelectorAll('.staff-card').forEach(card => {
        card.addEventListener('click', () => openDetail(card.dataset.id));
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ---------- Detail modal (read‑only view with Edit/Delete) ----------
function openDetail(id) {
    const t = templates.find(t => t.id == id);
    if (!t) return;
    currentTemplateId = id;
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
        openEditForm(t);
    });
    document.getElementById('deleteTemplateBtn').addEventListener('click', () => {
        if (confirm('Delete this template?')) {
            apiCall('DELETE', `/api/pricing/templates/${id}`)
                .then(() => {
                    detailModal.classList.remove('active');
                    loadTemplates();
                })
                .catch(err => alert('Delete failed: ' + err.message));
        }
    });
}

// ---------- Add form ----------
function openAddForm() {
    currentTemplateId = null;
    detailContent.innerHTML = buildFormHTML();
    detailModal.classList.add('active');
    bindFormEvents(null);
}

function openEditForm(template) {
    currentTemplateId = template.id;
    detailContent.innerHTML = buildFormHTML(template);
    detailModal.classList.add('active');
    bindFormEvents(template);
}

function buildFormHTML(template = null) {
    const t = template || {};
    const schedule = t.schedule_json ? JSON.parse(t.schedule_json) : [];
    return `
        <h3>${template ? 'Edit Template' : 'Add Template'}</h3>
        <form id="templateForm">
            <input type="hidden" id="templateId" value="${t.id || ''}">
            <label>Teacher *</label>
            <select id="formTeacher" required>
                <option value="">-- Select --</option>
                ${teachers.map(te => `<option value="${te.uuid}" ${t.teacher_id === te.uuid ? 'selected' : ''}>${te.display_name || te.username}</option>`).join('')}
            </select>
            <label>Package Name *</label>
            <input type="text" id="formName" value="${escapeHtml(t.name || '')}" required>
            <label>Type *</label>
            <select id="formType" required>
                <option value="private" ${t.type === 'private' ? 'selected' : ''}>Private</option>
                <option value="group" ${t.type === 'group' ? 'selected' : ''}>Group</option>
            </select>
            <label>Lesson Count *</label>
            <input type="number" id="formLessonCount" min="1" value="${t.lesson_count || 4}" required>
            <label>Default Rate (MMK) *</label>
            <input type="number" id="formRate" step="100" value="${t.default_rate || 0}" required>
            <label>Subject</label>
            <input type="text" id="formSubject" value="${escapeHtml(t.subject || '')}">
            <label>Billing Cycle</label>
            <select id="formBillingCycle">
                <option value="monthly" ${t.billing_cycle === 'monthly' ? 'selected' : ''}>Monthly</option>
                <option value="one-time" ${t.billing_cycle === 'one-time' ? 'selected' : ''}>One-time</option>
                <option value="per-lesson" ${t.billing_cycle === 'per-lesson' ? 'selected' : ''}>Per Lesson</option>
            </select>
            <label>Schedule</label>
            <div id="scheduleEntries"></div>
            <button type="button" id="addScheduleRowBtn" class="btn btn-secondary btn-sm">+ Add Day/Time</button>
            <div class="modal-actions" style="margin-top:1rem;">
                <button type="button" class="btn btn-secondary" id="cancelFormBtn">Cancel</button>
                <button type="submit" class="btn btn-success">Save</button>
            </div>
        </form>
    `;
}

function bindFormEvents(template) {
    const schedule = template ? JSON.parse(template.schedule_json || '[]') : [];
    const entriesDiv = document.getElementById('scheduleEntries');
    entriesDiv.innerHTML = '';

    function addRow(day = '', time = '') {
        const row = document.createElement('div');
        row.className = 'schedule-row';
        row.style.display = 'flex';
        row.style.gap = '0.5rem';
        row.style.alignItems = 'center';
        row.style.marginBottom = '0.4rem';
        row.innerHTML = `
            <select class="day-select">
                <option>Monday</option><option>Tuesday</option><option>Wednesday</option>
                <option>Thursday</option><option>Friday</option><option>Saturday</option><option>Sunday</option>
            </select>
            <input type="time" class="time-input" value="${time || '09:00'}">
            <button type="button" class="btn btn-sm btn-danger remove-schedule">X</button>
        `;
        if (day) row.querySelector('.day-select').value = day;
        row.querySelector('.remove-schedule').addEventListener('click', () => row.remove());
        entriesDiv.appendChild(row);
    }

    schedule.forEach(s => addRow(s.day, s.time));
    if (!schedule.length) addRow();

    document.getElementById('addScheduleRowBtn').addEventListener('click', () => addRow());

    document.getElementById('cancelFormBtn').addEventListener('click', () => {
        detailModal.classList.remove('active');
    });

    document.getElementById('templateForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = {
            teacher_id: document.getElementById('formTeacher').value,
            name: document.getElementById('formName').value.trim(),
            type: document.getElementById('formType').value,
            lesson_count: parseInt(document.getElementById('formLessonCount').value),
            default_rate: parseInt(document.getElementById('formRate').value),
            subject: document.getElementById('formSubject').value.trim(),
            billing_cycle: document.getElementById('formBillingCycle').value,
        };
        const rows = document.querySelectorAll('#scheduleEntries .schedule-row');
        const scheduleJson = [];
        rows.forEach(row => {
            const day = row.querySelector('.day-select').value;
            const time = row.querySelector('.time-input').value;
            if (day && time) scheduleJson.push({ day, time });
        });
        formData.schedule_json = JSON.stringify(scheduleJson);

        const method = currentTemplateId ? 'PUT' : 'POST';
        const path = currentTemplateId ? `/api/pricing/templates/${currentTemplateId}` : '/api/pricing/templates';
        try {
            await apiCall(method, path, formData);
            detailModal.classList.remove('active');
            loadTemplates();
        } catch (err) {
            alert('Save failed: ' + err.message);
        }
    });
}