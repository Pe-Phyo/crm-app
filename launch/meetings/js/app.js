// ============================================================
//  APP CONTROLLER
// ============================================================

import { fetchMeetings, addMeeting, updateMeeting, deleteMeeting } from './api.js';
import { renderCalendar } from './render.js';
import { JITSI_PARAMS, MAX_GROUP_SIZE, DEFAULT_COUNT, DAYS } from './config.js';

// ============================================================
//  HELPERS
// ============================================================

function generateId(prefix) {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`;
}

function generateStudentIds(names) {
    return names.map(() => generateId('stu'));
}

let meetingsCache = [];

// ============================================================
//  JOIN MEETING
// ============================================================

export async function joinMeeting(id) {
    const m = meetingsCache.find(m => m.id === id);
    if (!m) return;
    if (m.count > 0) {
        m.count--;
        await updateMeeting(id, { count: m.count });
        meetingsCache = await fetchMeetings();
        renderAll();
    }
    window.open(m.link + JITSI_PARAMS, '_blank');
}

// ============================================================
//  RENDER WRAPPER
// ============================================================

function renderAll() {
    renderCalendar(joinMeeting, openEditModal, deleteMeetingHandler, meetingsCache);
}

// ============================================================
//  DELETE HANDLER
// ============================================================

async function deleteMeetingHandler(id) {
    if (!confirm('Delete this meeting?')) return;
    await deleteMeeting(id);
    meetingsCache = await fetchMeetings();
    renderAll();
}

// ============================================================
//  RESET COUNTS
// ============================================================

async function resetAllCounts() {
    if (!confirm('Reset all counts to 8?')) return;
    for (const m of meetingsCache) {
        await updateMeeting(m.id, { count: 8 });
    }
    meetingsCache = await fetchMeetings();
    renderAll();
}

// ============================================================
//  ADD MEETING MODAL
// ============================================================

let addStudents = [];

function openAddModal() {
    addStudents = [];
    document.getElementById('addStudentList').innerHTML = '<div class="empty-students">No students added</div>';
    document.getElementById('addName').value = '';
    document.getElementById('addDay').value = 'Monday';
    document.getElementById('addTime').value = '09:00';
    document.getElementById('addType').value = 'group';
    document.getElementById('addLink').value = '';
    document.getElementById('addRate').value = '';
    document.getElementById('addHomework').value = '';
    document.getElementById('addComments').value = '';
    document.getElementById('addStudentInput').value = '';
    document.getElementById('addModal').classList.add('active');
}

function closeAddModal() {
    document.getElementById('addModal').classList.remove('active');
}

function renderAddStudentList() {
    const container = document.getElementById('addStudentList');
    if (addStudents.length === 0) {
        container.innerHTML = '<div class="empty-students">No students added</div>';
        return;
    }
    container.innerHTML = addStudents.map((s, i) =>
        `<div class="student-item">
            <span>${s}</span>
            <button data-index="${i}">✕</button>
        </div>`
    ).join('');
    container.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.index);
            addStudents.splice(idx, 1);
            renderAddStudentList();
        });
    });
}

async function submitAddMeeting() {
    const name = document.getElementById('addName').value.trim();
    const day = document.getElementById('addDay').value;
    const time = document.getElementById('addTime').value;
    const type = document.getElementById('addType').value;
    const link = document.getElementById('addLink').value.trim();
    const rate = parseInt(document.getElementById('addRate').value) || 0;
    const homework = document.getElementById('addHomework').value.trim();
    const comments = document.getElementById('addComments').value.trim();

    if (!name || !day || !time || !link) {
        alert('All fields required');
        return;
    }
    if (addStudents.length === 0) {
        alert('At least one student required');
        return;
    }
    if (!link.startsWith('https://')) {
        alert('Link must start with https://');
        return;
    }

    const studentNames = addStudents;
    const studentIds = generateStudentIds(studentNames);

    await addMeeting({
        id: generateId('m'),
        day,
        time,
        nickname: name,
        type,
        student_ids: studentIds,
        student_names: studentNames,
        link,
        count: DEFAULT_COUNT,
        rate: rate,
        homework: homework,
        comments: comments,
        attendance: []
    });

    closeAddModal();
    meetingsCache = await fetchMeetings();
    renderAll();
}

// ============================================================
//  EDIT MEETING MODAL
// ============================================================

let editStudents = [];
let editStudentIds = [];
let editingId = null;

function openEditModal(id) {
    const m = meetingsCache.find(m => m.id === id);
    if (!m) return;

    editingId = id;
    editStudents = [...m.student_names];
    editStudentIds = [...m.student_ids];

    document.getElementById('editId').value = id;
    document.getElementById('editName').value = m.nickname;
    document.getElementById('editDay').value = m.day;
    document.getElementById('editTime').value = m.time;
    document.getElementById('editType').value = m.type;
    document.getElementById('editLink').value = m.link;
    document.getElementById('editRate').value = m.rate || '';
    document.getElementById('editHomework').value = m.homework || '';
    document.getElementById('editComments').value = m.comments || '';
    document.getElementById('editStudentInput').value = '';
    renderEditStudentList();
    document.getElementById('editModal').classList.add('active');
}

function closeEditModal() {
    document.getElementById('editModal').classList.remove('active');
    editingId = null;
}

function renderEditStudentList() {
    const container = document.getElementById('editStudentList');
    if (editStudents.length === 0) {
        container.innerHTML = '<div class="empty-students">No students added</div>';
        return;
    }
    container.innerHTML = editStudents.map((s, i) =>
        `<div class="student-item">
            <span>${s}</span>
            <button data-index="${i}">✕</button>
        </div>`
    ).join('');
    container.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.index);
            editStudents.splice(idx, 1);
            editStudentIds.splice(idx, 1);
            renderEditStudentList();
        });
    });
}

async function submitEditMeeting() {
    const id = document.getElementById('editId').value;
    const name = document.getElementById('editName').value.trim();
    const day = document.getElementById('editDay').value;
    const time = document.getElementById('editTime').value;
    const type = document.getElementById('editType').value;
    const link = document.getElementById('editLink').value.trim();
    const rate = parseInt(document.getElementById('editRate').value) || 0;
    const homework = document.getElementById('editHomework').value.trim();
    const comments = document.getElementById('editComments').value.trim();

    if (!name || !day || !time || !link) {
        alert('All fields required');
        return;
    }
    if (editStudents.length === 0) {
        alert('At least one student required');
        return;
    }
    if (!link.startsWith('https://')) {
        alert('Link must start with https://');
        return;
    }

    await updateMeeting(id, {
        day,
        time,
        nickname: name,
        type,
        student_ids: editStudentIds,
        student_names: editStudents,
        link,
        rate: rate,
        homework: homework,
        comments: comments
    });

    closeEditModal();
    meetingsCache = await fetchMeetings();
    renderAll();
}

async function deleteMeetingFromEdit() {
    const id = document.getElementById('editId').value;
    if (!confirm('Delete this meeting?')) return;
    await deleteMeeting(id);
    closeEditModal();
    meetingsCache = await fetchMeetings();
    renderAll();
}

// ============================================================
//  ATTENDANCE CONTROLS (for Edit Modal)
// ============================================================

function setupAttendanceControls() {
    document.getElementById('markAllBtn').addEventListener('click', () => {
        // Mark all students as attended
        const list = document.getElementById('editAttendanceList');
        list.querySelectorAll('.student-item').forEach(item => {
            // Visual toggle
        });
    });

    document.getElementById('unmarkAllBtn').addEventListener('click', () => {
        // Unmark all students
        const list = document.getElementById('editAttendanceList');
        list.querySelectorAll('.student-item').forEach(item => {
            // Visual toggle
        });
    });
}

// ============================================================
//  EVENT BINDING
// ============================================================

function init() {
    // Navigation
    document.getElementById('backBtn').addEventListener('click', () => {
        window.location.href = '../index.html';
    });

    // Add modal
    document.getElementById('addBtn').addEventListener('click', openAddModal);
    document.getElementById('addCancelBtn').addEventListener('click', closeAddModal);
    document.getElementById('addSubmitBtn').addEventListener('click', submitAddMeeting);

    document.getElementById('addStudentInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const name = e.target.value.trim();
            if (name) {
                const type = document.getElementById('addType').value;
                if (type === 'group' && addStudents.length >= MAX_GROUP_SIZE) {
                    alert(`Max ${MAX_GROUP_SIZE} students`);
                    return;
                }
                addStudents.push(name);
                e.target.value = '';
                renderAddStudentList();
            }
        }
    });

    // Edit modal
    document.getElementById('editCancelBtn').addEventListener('click', closeEditModal);
    document.getElementById('editSaveBtn').addEventListener('click', submitEditMeeting);
    document.getElementById('editDeleteBtn').addEventListener('click', deleteMeetingFromEdit);

    document.getElementById('editStudentInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const name = e.target.value.trim();
            if (name) {
                const type = document.getElementById('editType').value;
                if (type === 'group' && editStudents.length >= MAX_GROUP_SIZE) {
                    alert(`Max ${MAX_GROUP_SIZE} students`);
                    return;
                }
                editStudents.push(name);
                editStudentIds.push(generateId('stu'));
                e.target.value = '';
                renderEditStudentList();
            }
        }
    });

    // Reset counts
    document.getElementById('resetBtn').addEventListener('click', resetAllCounts);

    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(el => {
        el.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });

    setupAttendanceControls();

    // Initial load
    loadInitialData();
}

// ============================================================
//  LOAD INITIAL DATA
// ============================================================

async function loadInitialData() {
    meetingsCache = await fetchMeetings();
    renderAll();
}

// ============================================================
//  START
// ============================================================

document.addEventListener('DOMContentLoaded', init);