import {
    apiCall, login, getStudents, getStudent, createStudent, updateStudent, deleteStudent,
    getActions, addAction, updateAction, deleteAction,
    getAttendance, addAttendance, updateAttendance, getPayments, addPayment
} from './api.js';
import { renderStudentList, renderActions } from './render.js';

// Screen elements
const setupScreen = document.getElementById('setupScreen');
const loginScreen = document.getElementById('loginScreen');
const mainPanel = document.getElementById('mainPanel');

// Auth elements
const setupPassword = document.getElementById('setupPassword');
const setupConfirm = document.getElementById('setupConfirm');
const setupBtn = document.getElementById('setupBtn');
const setupError = document.getElementById('setupError');
const passwordInput = document.getElementById('passwordInput');
const loginBtn = document.getElementById('loginBtn');
const loginError = document.getElementById('loginError');

// Main panel
const studentList = document.getElementById('studentList');
const actionItems = document.getElementById('actionItems');
const addStudentBtn = document.getElementById('addStudentBtn');

// Modals
const studentModal = document.getElementById('studentModal');
const modalTitle = document.getElementById('modalTitle');
const studentForm = document.getElementById('studentForm');
const modalCancelBtn = document.getElementById('modalCancelBtn');
const detailModal = document.getElementById('detailModal');
const detailContent = document.getElementById('detailContent');
const closeDetailBtn = document.getElementById('closeDetailBtn');

// State
let currentStudents = [];
let currentActions = [];

// ------------------------------------------------------------
// Screen switching
// ------------------------------------------------------------
function showSetup() {
    setupScreen.style.display = 'block';
    loginScreen.style.display = 'none';
    mainPanel.style.display = 'none';
}
function showLogin() {
    setupScreen.style.display = 'none';
    loginScreen.style.display = 'block';
    mainPanel.style.display = 'none';
}
function showMain() {
    setupScreen.style.display = 'none';
    loginScreen.style.display = 'none';
    mainPanel.style.display = 'block';
}

// ------------------------------------------------------------
// Auth flow
// ------------------------------------------------------------
async function checkSetup() {
    try {
        const status = await apiCall('GET', '/auth/status', null, true);
        if (status.setup) {
            showLogin();
        } else {
            showSetup();
        }
    } catch (e) {
        showLogin(); // assume setup done
    }
}

setupBtn.addEventListener('click', async () => {
    const pw = setupPassword.value;
    const confirm = setupConfirm.value;
    if (pw.length < 6) { setupError.textContent = 'Min 6 characters'; return; }
    if (pw !== confirm) { setupError.textContent = 'Passwords do not match'; return; }
    try {
        await apiCall('POST', '/auth/setup', { password: pw }, true);
        await login(pw);
        showMain();
        loadData();
    } catch (e) {
        setupError.textContent = e.message;
    }
});

loginBtn.addEventListener('click', async () => {
    try {
        await login(passwordInput.value);
        showMain();
        loadData();
    } catch (e) {
        loginError.textContent = 'Wrong password';
    }
});

// ------------------------------------------------------------
// Data loading
// ------------------------------------------------------------
async function loadData() {
    try {
        currentStudents = await getStudents();
        currentActions = await getActions();
        renderAll();
    } catch (e) {
        console.error(e);
    }
}

function renderAll() {
    renderStudentList(currentStudents, openStudentDetail);
    renderActions(currentActions, toggleAction, deleteActionHandler, addActionHandler);
}

// ------------------------------------------------------------
// Action items handlers
// ------------------------------------------------------------
async function addActionHandler(text) {
    await addAction(text);
    currentActions = await getActions();
    renderAll();
}

async function toggleAction(id, done) {
    await updateAction(id, { done });
    currentActions = await getActions();
    renderAll();
}

async function deleteActionHandler(id) {
    await deleteAction(id);
    currentActions = await getActions();
    renderAll();
}

// ------------------------------------------------------------
// Student CRUD
// ------------------------------------------------------------
addStudentBtn.addEventListener('click', () => {
    openStudentForm();
});

function openStudentForm(student = null) {
    modalTitle.textContent = student ? 'Edit Student' : 'Add Student';
    studentForm.reset();
    document.getElementById('studentUuid').value = student?.uuid || '';

    if (student) {
        // Pre-fill form (will implement later)
    }

    // Reset meeting times list
    window._meetingTimes = student?.meeting_times ? [...student.meeting_times] : [];
    renderMeetingTimesList();

    studentModal.classList.add('active');
}

modalCancelBtn.addEventListener('click', () => {
    studentModal.classList.remove('active');
});

studentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const uuid = document.getElementById('studentUuid').value;
    const formData = new FormData(studentForm);
    const data = {
        name: formData.get('name'),
        location: formData.get('location'),
        timezone: formData.get('timezone'),
        age_group: formData.get('age_group'),
        academic_year: formData.get('academic_year'),
        phone: formData.get('phone'),
        telegram: formData.get('telegram'),
        email: formData.get('email'),
        is_minor: formData.get('is_minor') === 'on',
        parent_name: formData.get('parent_name'),
        parent_phone: formData.get('parent_phone'),
        rate: parseInt(formData.get('rate')) || 0,
        educational_goals: formData.get('educational_goals'),
        behavioral_comments: formData.get('behavioral_comments'),
        general_comments: formData.get('general_comments'),
        meeting_times: window._meetingTimes || []
    };

    try {
        if (uuid) {
            await updateStudent(uuid, data);
        } else {
            await createStudent(data);
        }
        studentModal.classList.remove('active');
        currentStudents = await getStudents();
        renderAll();
    } catch (err) {
        alert('Error: ' + err.message);
    }
});

// Meeting times sub-form
document.getElementById('addMeetingBtn').addEventListener('click', () => {
    const day = document.getElementById('meetingDay').value;
    const time = document.getElementById('meetingTime').value;
    const type = document.getElementById('meetingType').value;
    const inPerson = document.getElementById('meetingInPerson').checked;
    if (!day || !time) return;
    window._meetingTimes.push({ day, time, type, is_in_person: inPerson });
    renderMeetingTimesList();
});

function renderMeetingTimesList() {
    const list = document.getElementById('meetingTimesList');
    const times = window._meetingTimes || [];
    list.innerHTML = times.map((mt, idx) => `
        <div class="meeting-time-item">
            ${mt.day} ${mt.time} (${mt.type}) ${mt.is_in_person ? '🏫' : '💻'}
            <button type="button" data-index="${idx}" class="remove-mt-btn">✕</button>
        </div>
    `).join('');
    list.querySelectorAll('.remove-mt-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.index);
            window._meetingTimes.splice(idx, 1);
            renderMeetingTimesList();
        });
    });
}

// ------------------------------------------------------------
// Student Detail Modal
// ------------------------------------------------------------
async function openStudentDetail(uuid) {
    try {
        const student = await getStudent(uuid);
        const att = student.attendance || [];
        const payments = student.payments || [];
        const profile = student;

        let html = `
            <h3>${escapeHtml(profile.name)}</h3>
            <p><strong>Location:</strong> ${profile.location} | <strong>Timezone:</strong> ${profile.timezone}</p>
            <p><strong>Age Group:</strong> ${profile.age_group} | <strong>Year:</strong> ${profile.academic_year}</p>
            <p><strong>Contact:</strong> ${profile.phone} / ${profile.telegram} / ${profile.email}</p>
            <p><strong>Rate:</strong> ${profile.rate} K</p>
            <p><strong>Meetings:</strong> ${profile.meeting_times_summary || 'None'}</p>
            <hr>
            <h4>Attendance</h4>
            <div>${att.map(a => `<span>${a.date} - ${a.status}</span><br>`).join('') || 'No records'}</div>
            <hr>
            <h4>Payments</h4>
            <div>${payments.map(p => `<span>${p.date}: ${p.amount} K</span><br>`).join('') || 'No payments'}</div>
            <hr>
            <button id="editStudentBtn" class="btn btn-primary">Edit</button>
        `;
        detailContent.innerHTML = html;
        detailModal.classList.add('active');

        document.getElementById('editStudentBtn').addEventListener('click', () => {
            detailModal.classList.remove('active');
            openStudentForm(profile);
        });
    } catch (e) {
        alert('Failed to load student details');
    }
}

closeDetailBtn.addEventListener('click', () => {
    detailModal.classList.remove('active');
});

// Helper
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ------------------------------------------------------------
// Initialisation
// ------------------------------------------------------------
checkSetup();