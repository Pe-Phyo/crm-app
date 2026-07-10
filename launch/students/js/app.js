import { getStudents, getActions, addAction, updateAction, deleteAction } from './api.js';
import { renderStudentList, filterStudents, bindFilterEvents } from './students/list.js';
import { openAddForm, updateLinkSelect } from './students/addForm.js';
import { openStudentDetail } from './students/detailView.js';

// State
let currentStudents = [];

// Called by addForm after create/update
window._onStudentChanged = async () => {
    currentStudents = await getStudents();
    const filtered = filterStudents(currentStudents);
    renderStudentList(filtered, openStudentDetail);
    updateLinkSelect(currentStudents);
};

// Load data and render everything
async function loadData() {
    currentStudents = await getStudents();
    renderAll();
}

function renderAll() {
    const filtered = filterStudents(currentStudents);
    renderStudentList(filtered, openStudentDetail);
    updateLinkSelect(currentStudents);
}

// Action item handlers
async function addActionHandler(text) {
    await addAction(text);
    currentActions = await getActions();
}

async function toggleAction(id, done) {
    await updateAction(id, { done });
    currentActions = await getActions();
}

async function deleteActionHandler(id) {
    await deleteAction(id);
    currentActions = await getActions();
}

// Init
async function init() {
    // Verify staff token
    const staffToken = localStorage.getItem('staff_token');
    if (!staffToken) {
        // Not logged in – redirect to main dashboard
        window.location.href = '/launch/index.html';
        return;
    }

    // Check that token is still valid
    try {
        const res = await fetch('/api/staff/me', {
            headers: { 'Authorization': `Bearer ${staffToken}` }
        });
        if (!res.ok) {
            localStorage.clear();
            window.location.href = '/launch/index.html';
            return;
        }
    } catch (e) {
        localStorage.clear();
        window.location.href = '/launch/index.html';
        return;
    }

    // Token valid – proceed
    document.getElementById('mainPanel').style.display = 'block';

    // Wire UI
    document.getElementById('backBtn')?.addEventListener('click', () => {
        window.location.href = '/launch/index.html';
    });

    document.getElementById('addStudentBtn')?.addEventListener('click', openAddForm);

    bindFilterEvents(async () => {
        const filtered = filterStudents(currentStudents);
        renderStudentList(filtered, openStudentDetail);
    });

    await loadData();
}

init();