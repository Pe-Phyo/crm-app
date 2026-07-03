import { checkSetup, bindAuthEvents } from './auth/auth.js';
import { renderStudentList, filterStudents, bindFilterEvents } from './students/list.js';
import { openAddForm, updateLinkSelect } from './students/addForm.js';
import { openStudentDetail } from './students/detailView.js';
import { renderActions } from './actions/actions.js';
import { getStudents, getActions, addAction, updateAction, deleteAction } from './api.js';

// State
let currentStudents = [];
let currentActions = [];

// Called by addForm after create/update
window._onStudentChanged = async () => {
    currentStudents = await getStudents();
    const filtered = filterStudents(currentStudents);
    renderStudentList(filtered, openStudentDetail);
    updateLinkSelect(currentStudents);
};

// Load data from backend and render
async function loadData() {
    currentStudents = await getStudents();
    currentActions = await getActions();
    renderAll();
}

function renderAll() {
    const filtered = filterStudents(currentStudents);
    renderStudentList(filtered, openStudentDetail);
    updateLinkSelect(currentStudents);
    renderActions(currentActions, toggleAction, deleteActionHandler, addActionHandler);
}

// Action item handlers
async function addActionHandler(text) {
    await addAction(text);
    currentActions = await getActions();
    renderActions(currentActions, toggleAction, deleteActionHandler, addActionHandler);
}

async function toggleAction(id, done) {
    await updateAction(id, { done });
    currentActions = await getActions();
    renderActions(currentActions, toggleAction, deleteActionHandler, addActionHandler);
}

async function deleteActionHandler(id) {
    await deleteAction(id);
    currentActions = await getActions();
    renderActions(currentActions, toggleAction, deleteActionHandler, addActionHandler);
}

// Init
function init() {
    document.getElementById('backBtn')?.addEventListener('click', () => {
        window.location.href = '/launch/index.html';
    });

    document.getElementById('addStudentBtn')?.addEventListener('click', openAddForm);

    bindFilterEvents(async () => {
        const filtered = filterStudents(currentStudents);
        renderStudentList(filtered, openStudentDetail);
    });

    bindAuthEvents(async () => {
        await loadData();
    });

    checkSetup();
}

init();