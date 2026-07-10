import { escapeHtml } from '../../students/js/utils/helpers.js';
import { createTemplate, updateTemplate } from './api.js';
import { loadTemplates } from './app.js';

const formModal = document.getElementById('templateFormModal');
const formTitle = document.getElementById('formModalTitle');
let currentTemplateId = null;

function populateTeacherSelect(teachers, selectedUuid = null) {
    const select = document.getElementById('formTeacher');
    select.innerHTML = '<option value="">-- Select --</option>';
    teachers.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.uuid;
        opt.textContent = t.display_name || t.username;
        if (selectedUuid === t.uuid) opt.selected = true;
        select.appendChild(opt);
    });
}

function buildScheduleRows(schedule) {
    const entriesDiv = document.getElementById('scheduleEntries');
    entriesDiv.innerHTML = '';

    function addRow(day = '', time = '') {
        const row = document.createElement('div');
        row.className = 'multi-input-row';
        row.innerHTML = `
            <select class="day-select">
                <option>Monday</option><option>Tuesday</option><option>Wednesday</option>
                <option>Thursday</option><option>Friday</option><option>Saturday</option><option>Sunday</option>
            </select>
            <input type="time" class="time-input" value="${time || '09:00'}">
            <button type="button" class="remove-multi-btn">X</button>
        `;
        if (day) row.querySelector('.day-select').value = day;
        row.querySelector('.remove-multi-btn').addEventListener('click', () => row.remove());
        entriesDiv.appendChild(row);
    }

    schedule.forEach(s => addRow(s.day, s.time));
    if (!schedule.length) addRow();

    document.getElementById('addScheduleRowBtn').onclick = () => addRow();
}

function resetForm() {
    document.getElementById('templateId').value = '';
    document.getElementById('templateForm').reset();
    document.getElementById('formLessonCount').value = '4';
    document.getElementById('formRate').value = '0';
    document.getElementById('formBillingCycle').value = 'monthly';
    buildScheduleRows([]);
}

export function openAddForm(teachers) {
    currentTemplateId = null;
    formTitle.textContent = 'Add Template';
    populateTeacherSelect(teachers);
    resetForm();
    formModal.classList.add('active');
}

export function openEditForm(template, teachers) {
    currentTemplateId = template.id;
    formTitle.textContent = 'Edit Template';
    populateTeacherSelect(teachers, template.teacher_id);
    document.getElementById('templateId').value = template.id;
    document.getElementById('formName').value = template.name;
    document.getElementById('formType').value = template.type;
    document.getElementById('formLessonCount').value = template.lesson_count;
    document.getElementById('formRate').value = template.default_rate;
    document.getElementById('formSubject').value = template.subject || '';
    document.getElementById('formBillingCycle').value = template.billing_cycle;
    buildScheduleRows(JSON.parse(template.schedule_json || '[]'));
    formModal.classList.add('active');
}

document.getElementById('templateForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        teacher_id: document.getElementById('formTeacher').value,
        name: document.getElementById('formName').value.trim(),
        type: document.getElementById('formType').value,
        lesson_count: parseInt(document.getElementById('formLessonCount').value),
        default_rate: parseInt(document.getElementById('formRate').value),
        subject: document.getElementById('formSubject').value.trim(),
        billing_cycle: document.getElementById('formBillingCycle').value,
    };
    const rows = document.querySelectorAll('#scheduleEntries .multi-input-row');
    const scheduleJson = [];
    rows.forEach(row => {
        const day = row.querySelector('.day-select').value;
        const time = row.querySelector('.time-input').value;
        if (day && time) scheduleJson.push({ day, time });
    });
    data.schedule_json = JSON.stringify(scheduleJson);

    try {
        if (currentTemplateId) {
            await updateTemplate(currentTemplateId, data);
        } else {
            await createTemplate(data);
        }
        formModal.classList.remove('active');
        loadTemplates();
    } catch (err) {
        alert('Save failed: ' + err.message);
    }
});