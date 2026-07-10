import { apiCall, getStudents, createStudent, updateStudent } from '../api.js';
import { escapeHtml, setupMultiInput } from '../utils/helpers.js';

const studentModal = document.getElementById('studentModal');
const modalTitle = document.getElementById('modalTitle');
const studentForm = document.getElementById('studentForm');
const modalCancelBtn = document.getElementById('modalCancelBtn');
const loadPackagesBtn = document.getElementById('loadPackagesBtn');
const packageTemplateSelect = document.getElementById('packageTemplateSelect');

let editingStudentUuid = null;
let tempLinkedStudents = [];
let tempMeetingTimes = [];
let studentListCache = [];

// ------------------------------------------------------------
// Multi‑input helpers
// ------------------------------------------------------------
setupMultiInput('phoneNumbersContainer', 'phone-input');
setupMultiInput('emailsContainer', 'email-input');
setupMultiInput('parentPhonesContainer', 'parent-phone-input');
setupMultiInput('parentEmailsContainer', 'parent-email-input');

// ------------------------------------------------------------
// Teacher & Group meeting helpers
// ------------------------------------------------------------
let teacherCache = [];
let groupMeetingCache = [];

async function loadTeachers() {
    try {
        const res = await apiCall('GET', '/staff/teachers');
        teacherCache = res || [];
    } catch (e) {
        teacherCache = [];
    }
    // Populate the per-meeting teacher dropdown
    const select = document.getElementById('mtTeacherSelect');
    if (!select) return;
    select.innerHTML = '<option value="">-- Select --</option>' +
        teacherCache.map(t => `<option value="${t.uuid}">${t.display_name}</option>`).join('');
}

async function loadGroupMeetings() {
    try {
        const res = await apiCall('GET', '/meetings/groups');
        groupMeetingCache = res || [];
    } catch (e) {
        groupMeetingCache = [];
    }
}

function showGroupDropdown() {
    const container = document.getElementById('groupMeetingContainer');
    if (!container) return;
    container.innerHTML = '';
    container.innerHTML = `
        <label>Existing Group</label>
        <select id="groupMeetingSelect">
            <option value="">-- pick or new --</option>
            ${groupMeetingCache.map(g => `<option value="${g}">${g}</option>`).join('')}
            <option value="__new__">+ New group (enter name below)</option>
        </select>
    `;
    const meetingNameInput = document.getElementById('meetingName');
    const groupSelect = document.getElementById('groupMeetingSelect');
    groupSelect.addEventListener('change', () => {
        const val = groupSelect.value;
        if (val === '__new__') {
            meetingNameInput.value = '';
            meetingNameInput.disabled = false;
            meetingNameInput.placeholder = 'Enter new group name';
        } else if (val) {
            meetingNameInput.value = val;
            meetingNameInput.disabled = true;
        } else {
            meetingNameInput.value = '';
            meetingNameInput.disabled = false;
            meetingNameInput.placeholder = 'e.g., Math Group A';
        }
    });
    groupSelect.dispatchEvent(new Event('change'));
}

function hideGroupDropdown() {
    const container = document.getElementById('groupMeetingContainer');
    if (container) container.innerHTML = '';
    const meetingNameInput = document.getElementById('meetingName');
    if (meetingNameInput) {
        meetingNameInput.disabled = false;
        meetingNameInput.placeholder = 'e.g., Math Group A';
    }
}

// ------------------------------------------------------------
// Open / Close
// ------------------------------------------------------------
modalCancelBtn.addEventListener('click', closeForm);

export function openAddForm() {
    editingStudentUuid = null;
    modalTitle.textContent = 'Add Student';
    resetForm();
    loadTeachers();
    loadGroupMeetings();
    studentModal.classList.add('active');
}

export async function openEditForm(student) {
    if (!student) return;
    editingStudentUuid = student.uuid;
    modalTitle.textContent = 'Edit Student';
    resetForm();
    await populateLocationDropdown();
    document.getElementById('studentUuid').value = student.uuid;
    populateFormFromStudent(student);
    loadTeachers();
    loadGroupMeetings();
    studentModal.classList.add('active');
}

function closeForm() {
    studentModal.classList.remove('active');
}

function resetForm() {
    studentForm.reset();
    tempLinkedStudents = [];
    tempMeetingTimes = [];
    renderMeetingTimesList();
    renderLinkedStudentsList();
    toggleMinorSection();
    populateLocationDropdown();
    document.getElementById('timezoneSelect').value = '';
    hideGroupDropdown();
    document.getElementById('groupMeetingContainer').innerHTML = '';
    // Reset per-meeting teacher/rate fields
    const mtTeacher = document.getElementById('mtTeacherSelect');
    if (mtTeacher) mtTeacher.value = '';
    const mtRate = document.getElementById('mtRate');
    if (mtRate) mtRate.value = '0';
}

// ------------------------------------------------------------
// Location / Timezone dropdown
// ------------------------------------------------------------
async function populateLocationDropdown() {
    const tzSelect = document.getElementById('timezoneSelect');
    if (!tzSelect) return;
    try {
        const res = await apiCall('GET', '/locations', null, true);
        const locations = res.locations || [];
        tzSelect.innerHTML = '<option value="">-- Select --</option>' +
            locations.map(l => `<option value="${l.value}">${l.label}</option>`).join('');
    } catch (e) {
        console.error(e);
    }
}

// ------------------------------------------------------------
// Minor info toggle
// ------------------------------------------------------------
function toggleMinorSection() {
    const ageGroup = document.getElementById('ageGroupSelect').value;
    const minorSection = document.getElementById('minorInfoSection');
    minorSection.style.display = (ageGroup === 'Child' || ageGroup === 'Young Adult') ? 'block' : 'none';
}
document.getElementById('ageGroupSelect').addEventListener('change', toggleMinorSection);

// ------------------------------------------------------------
// Meeting times sub‑form
// ------------------------------------------------------------
document.getElementById('addMeetingBtn').addEventListener('click', () => {
    const name = document.getElementById('meetingName').value.trim();
    const day = document.getElementById('meetingDay').value;
    const time = document.getElementById('meetingTime').value;
    const type = document.getElementById('meetingType').value;
    const inPerson = document.getElementById('meetingInPerson').checked;
    const link = document.getElementById('meetingLink').value.trim();
    const teacherId = document.getElementById('mtTeacherSelect').value;
    const rate = parseInt(document.getElementById('mtRate').value) || 0;

    if (!day || !time) return;

    // Get teacher name from cache
    const teacher = teacherCache.find(t => t.uuid === teacherId);
    const teacherName = teacher ? teacher.display_name : '';

    tempMeetingTimes.push({
        name,
        day,
        time,
        type,
        is_in_person: inPerson,
        link,
        teacher_id: teacherId,
        teacher_name: teacherName,
        rate
    });

    renderMeetingTimesList();
    // Reset form fields for next meeting
    document.getElementById('meetingName').value = '';
    document.getElementById('meetingTime').value = '09:00';
    document.getElementById('meetingInPerson').checked = false;
    document.getElementById('meetingLink').value = '';
    document.getElementById('mtTeacherSelect').value = '';
    document.getElementById('mtRate').value = '0';
    updateMeetingLinkPlaceholder();
    hideGroupDropdown();
});

// Load teacher packages
loadPackagesBtn?.addEventListener('click', async () => {
    const teacherId = document.getElementById('mtTeacherSelect').value;
    if (!teacherId) {
        alert('Select a teacher first');
        return;
    }
    try {
        const templates = await apiCall('GET', `/pricing/templates?teacher_id=${encodeURIComponent(teacherId)}`);
        packageTemplateSelect.innerHTML = '<option value="">-- Select package --</option>' +
            templates.map(t => `<option value="${t.id}">${t.name} (${t.type}, ${t.lesson_count} lessons, ${t.default_rate}K)</option>`).join('');
        packageTemplateSelect.style.display = 'block';
    } catch (e) {
        alert('Could not load packages');
    }
});

// Auto‑fill from selected package template
packageTemplateSelect?.addEventListener('change', async () => {
    const templateId = packageTemplateSelect.value;
    if (!templateId) return;
    const teacherId = document.getElementById('mtTeacherSelect').value;
    try {
        const templates = await apiCall('GET', `/pricing/templates?teacher_id=${encodeURIComponent(teacherId)}`);
        const t = templates.find(t => t.id == templateId);
        if (!t) return;
        document.getElementById('meetingName').value = t.name;
        document.getElementById('meetingType').value = t.type;
        document.getElementById('mtRate').value = t.default_rate;
        try {
            const schedule = JSON.parse(t.schedule_json);
            if (schedule.length > 0) {
                document.getElementById('meetingDay').value = schedule[0].day;
                document.getElementById('meetingTime').value = schedule[0].time;
            }
        } catch (e) {}
        packageTemplateSelect.style.display = 'none';
    } catch (e) {
        alert('Could not load package details');
    }
});

function renderMeetingTimesList() {
    const list = document.getElementById('meetingTimesList');
    list.innerHTML = tempMeetingTimes.map((mt, idx) => `
        <div class="meeting-time-item">
            <strong>${mt.name || 'Unnamed'}</strong>: ${mt.day} ${mt.time} (${mt.type})
            ${mt.link ? ` — ${mt.link}` : ''}
            | Teacher: ${mt.teacher_name || 'None'} | Rate: ${mt.rate}K
            <button type="button" data-index="${idx}" class="remove-mt-btn">X</button>
        </div>
    `).join('');
    list.querySelectorAll('.remove-mt-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.index);
            tempMeetingTimes.splice(idx, 1);
            renderMeetingTimesList();
        });
    });
}

const nameInput = document.querySelector('[name="name"]');
nameInput?.addEventListener('input', updateMeetingLinkPlaceholder);
function updateMeetingLinkPlaceholder() {
    const name = nameInput.value.trim();
    const linkInput = document.getElementById('meetingLink');
    if (!linkInput) return;
    if (name && !editingStudentUuid) {
        const random = Math.floor(100 + Math.random() * 900);
        linkInput.placeholder = `https://meet.jit.si/Lucky${name.replace(/\s/g, '')}${random}`;
    } else {
        linkInput.placeholder = '';
    }
}

// ------------------------------------------------------------
// Linked students sub‑form
// ------------------------------------------------------------
document.getElementById('addLinkBtn').addEventListener('click', () => {
    const select = document.getElementById('linkStudentSelect');
    const relationship = document.getElementById('relationshipType').value;
    const invoiceGroup = document.getElementById('invoiceGroupCheck').checked;
    const uuid = select.value;
    if (!uuid) return;
    const name = select.options[select.selectedIndex].text;
    if (tempLinkedStudents.find(l => l.uuid === uuid)) {
        alert('Already linked');
        return;
    }
    tempLinkedStudents.push({ uuid, name, relationship, invoice_group: invoiceGroup });
    renderLinkedStudentsList();
    select.value = '';
    document.getElementById('invoiceGroupCheck').checked = false;
});

function renderLinkedStudentsList() {
    const container = document.getElementById('linkedStudentsList');
    container.innerHTML = tempLinkedStudents.map((l, idx) => `
        <div class="linked-student-item">
            <span>${l.name} (${l.relationship}) ${l.invoice_group ? '[Group Invoice]' : ''}</span>
            <button type="button" data-index="${idx}" class="remove-mt-btn">X</button>
        </div>
    `).join('');
    container.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.index);
            tempLinkedStudents.splice(idx, 1);
            renderLinkedStudentsList();
        });
    });
}

export function updateLinkSelect(students) {
    studentListCache = students;
    const select = document.getElementById('linkStudentSelect');
    if (!select) return;
    select.innerHTML = '<option value="">-- Select student --</option>';
    students.forEach(s => {
        if (s.uuid !== editingStudentUuid) {
            const opt = document.createElement('option');
            opt.value = s.uuid;
            opt.textContent = s.name;
            select.appendChild(opt);
        }
    });
}

// ------------------------------------------------------------
// Form submission
// ------------------------------------------------------------
studentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(studentForm);
    const tzSelect = document.getElementById('timezoneSelect');
    const tzLabel = tzSelect.options[tzSelect.selectedIndex]?.text || '';
    const phones = Array.from(document.querySelectorAll('.phone-input'))
        .map(inp => inp.value.trim()).filter(v => v);
    const emails = Array.from(document.querySelectorAll('.email-input'))
        .map(inp => inp.value.trim()).filter(v => v);
    const parentPhones = Array.from(document.querySelectorAll('.parent-phone-input'))
        .map(inp => inp.value.trim()).filter(v => v);
    const parentEmails = Array.from(document.querySelectorAll('.parent-email-input'))
        .map(inp => inp.value.trim()).filter(v => v);

    const data = {
        name: formData.get('name'),
        age_group: formData.get('age_group'),
        timezone: formData.get('timezone'),
        timezone_label: tzLabel,
        phones: phones,
        emails: emails,
        telegram: formData.get('telegram'),
        is_minor: (formData.get('age_group') === 'Child' || formData.get('age_group') === 'Young Adult'),
        parent_name: formData.get('parent_name'),
        parent_phones: parentPhones,
        parent_emails: parentEmails,
        school_name: formData.get('school_name'),
        academic_year: formData.get('academic_year'),
        educational_goals: formData.get('educational_goals'),
        general_comments: formData.get('general_comments'),
        meeting_times: tempMeetingTimes,
        linked_students: tempLinkedStudents,
        birthdate: formData.get('birthdate') || ''
        // No global teacher_id or rate
    };

    try {
        if (editingStudentUuid) {
            await updateStudent(editingStudentUuid, data);
        } else {
            await createStudent(data);
        }
        closeForm();
        if (window._onStudentChanged) window._onStudentChanged();
    } catch (err) {
        alert('Error: ' + err.message);
    }
});

// ------------------------------------------------------------
// Populate form for editing
// ------------------------------------------------------------
function populateFormFromStudent(student) {
    document.querySelector('[name="name"]').value = student.name || '';
    document.getElementById('ageGroupSelect').value = student.age_group || 'Adult';
    document.getElementById('timezoneSelect').value = student.timezone || '';
    document.querySelector('[name="telegram"]').value = student.telegram || '';
    document.querySelector('[name="educational_goals"]').value = student.educational_goals || '';
    document.querySelector('[name="general_comments"]').value = student.general_comments || '';
    document.querySelector('[name="parent_name"]').value = student.parent_name || '';
    document.querySelector('[name="school_name"]').value = student.school_name || '';
    document.querySelector('[name="academic_year"]').value = student.academic_year || '';
    document.querySelector('[name="birthdate"]').value = student.birthdate || '';

    // No global teacher select to populate

    // Multi‑value fields
    const addRow = (containerId, values, className) => {
        const container = document.getElementById(containerId);
        container.querySelectorAll('.multi-input-row').forEach((row, idx) => {
            if (idx > 0) row.remove();
        });
        const firstInput = container.querySelector(`.${className}`);
        if (firstInput && values.length > 0) {
            firstInput.value = values[0];
            for (let i = 1; i < values.length; i++) {
                const row = document.createElement('div');
                row.className = 'multi-input-row';
                const inp = document.createElement('input');
                inp.type = 'text';
                inp.className = className;
                inp.value = values[i];
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'remove-multi-btn';
                btn.textContent = '-';
                btn.addEventListener('click', () => row.remove());
                row.appendChild(inp);
                row.appendChild(btn);
                container.appendChild(row);
            }
        }
    };
    addRow('phoneNumbersContainer', student.phones || [], 'phone-input');
    addRow('emailsContainer', student.emails || [], 'email-input');
    addRow('parentPhonesContainer', student.parent_phones || [], 'parent-phone-input');
    addRow('parentEmailsContainer', student.parent_emails || [], 'parent-email-input');

    // Meeting times now include teacher and rate from backend
    tempMeetingTimes = (student.meeting_times || []).map(mt => ({
        ...mt,
        teacher_id: mt.teacher_id || '',
        teacher_name: mt.teacher_name || '',
        rate: mt.rate || 0
    }));
    renderMeetingTimesList();

    tempLinkedStudents = student.linked_students || [];
    renderLinkedStudentsList();
    updateLinkSelect(studentListCache);
    toggleMinorSection();

    // If editing a meeting time with type 'group', show group dropdown (basic)
    if (tempMeetingTimes.some(mt => mt.type === 'group')) {
        showGroupDropdown();
    }
}

// ------------------------------------------------------------
// Type change listener for group dropdown
// ------------------------------------------------------------
document.getElementById('meetingType').addEventListener('change', (e) => {
    if (e.target.value === 'group') {
        showGroupDropdown();
    } else {
        hideGroupDropdown();
    }
});