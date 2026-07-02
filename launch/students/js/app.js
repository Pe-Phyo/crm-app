import { login, getStudents, getActions, apiCall } from './api.js';

// Screens
const setupScreen = document.getElementById('setupScreen');
const loginScreen = document.getElementById('loginScreen');
const mainPanel = document.getElementById('mainPanel');

// Setup elements
const setupPassword = document.getElementById('setupPassword');
const setupConfirm = document.getElementById('setupConfirm');
const setupBtn = document.getElementById('setupBtn');
const setupError = document.getElementById('setupError');

// Login elements
const passwordInput = document.getElementById('passwordInput');
const loginBtn = document.getElementById('loginBtn');
const loginError = document.getElementById('loginError');

// Main elements
const studentList = document.getElementById('studentList');
const actionItems = document.getElementById('actionItems');

// Navigation
document.getElementById('backBtn').addEventListener('click', () => {
    window.location.href = '/launch/index.html';
});

// ------------------------------------------------------------
// Check if password is already set
// ------------------------------------------------------------
async function checkSetup() {
    try {
        // Try a dummy login to see if setup is needed
        await apiCall('POST', '/auth/login', { password: '' }, true);
        // If we get here, auth endpoint exists but password is wrong – so setup is complete
        showLogin();
    } catch (e) {
        // If the error indicates no database or setup needed, show setup screen
        // The backend will return 500 or error message; we treat that as "not set up"
        showSetup();
    }
}

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
// Setup handler
// ------------------------------------------------------------
setupBtn.addEventListener('click', async () => {
    const pw = setupPassword.value;
    const confirm = setupConfirm.value;
    if (pw.length < 6) {
        setupError.textContent = 'Password must be at least 6 characters';
        return;
    }
    if (pw !== confirm) {
        setupError.textContent = 'Passwords do not match';
        return;
    }
    try {
        await apiCall('POST', '/auth/setup', { password: pw });
        // Setup successful, now login
        await login(pw);
        showMain();
        loadData();
    } catch (e) {
        setupError.textContent = 'Setup failed: ' + e.message;
    }
});

// ------------------------------------------------------------
// Login handler
// ------------------------------------------------------------
loginBtn.addEventListener('click', async () => {
    const pw = passwordInput.value;
    try {
        await login(pw);
        showMain();
        loadData();
    } catch (e) {
        loginError.textContent = 'Wrong password';
    }
});

passwordInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') loginBtn.click();
});

// ------------------------------------------------------------
// Modal stubs
// ------------------------------------------------------------
document.getElementById('addStudentBtn').addEventListener('click', () => {
    document.getElementById('studentModal').classList.add('active');
});
document.getElementById('modalCancelBtn').addEventListener('click', () => {
    document.getElementById('studentModal').classList.remove('active');
});

// ------------------------------------------------------------
// Data loading
// ------------------------------------------------------------
async function loadData() {
    try {
        const students = await getStudents();
        renderStudentList(students);
        const actions = await getActions();
        renderActions(actions);
    } catch (e) {
        console.error(e);
    }
}

function renderStudentList(students) {
    if (students.length === 0) {
        studentList.innerHTML = '<div class="placeholder-box">No students yet.</div>';
        return;
    }
    const html = students.map(s => `
        <div class="student-card" style="background:#1e293b;padding:15px;border-radius:8px;margin-bottom:10px;">
            <strong>${s.name}</strong> <span style="color:#94a3b8;">${s.location}</span><br>
            Rate: ${s.rate} MMK | Attendance: ${s.attendance_percentage.toFixed(0)}%<br>
            Meetings: ${s.meeting_times_summary || 'None'}<br>
            Status: ${s.status}
        </div>
    `).join('');
    studentList.innerHTML = html;
}

function renderActions(actions) {
    if (actions.length === 0) {
        actionItems.innerHTML = '<div class="placeholder-box">No action items.</div>';
        return;
    }
    actionItems.innerHTML = actions.map(a => `
        <div class="placeholder-box" style="margin-bottom:5px;">${a.done ? '✅' : '⬜'} ${a.text}</div>
    `).join('');
}

// ------------------------------------------------------------
// Initial load
// ------------------------------------------------------------
checkSetup();