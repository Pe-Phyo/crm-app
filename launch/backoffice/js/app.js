import { getTeachers, getTemplates } from './api.js';
import { renderList } from './list.js';
import { openDetail } from './detailView.js';
import { openAddForm } from './form.js';

let teachers = [];
let templates = [];

export function getTeacherList() { return teachers; }
export function getTemplateList() { return templates; }
export function setTemplateList(list) { templates = list; }

export async function loadTemplates() {
    const teacherId = document.getElementById('teacherFilter').value;
    try {
        templates = await getTemplates(teacherId || null);
        renderList(templates, teachers, openDetail);
    } catch (e) {
        alert('Failed to load templates: ' + e.message);
    }
}

async function init() {
    // Token check (same pattern as students)
    const token = localStorage.getItem('staff_token');
    if (!token) {
        window.location.href = '/launch/index.html';
        return;
    }
    try {
        const res = await fetch('/api/staff/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Token invalid');
    } catch (e) {
        localStorage.clear();
        window.location.href = '/launch/index.html';
        return;
    }

    // Wire buttons
    document.getElementById('backBtn').addEventListener('click', () => {
        window.location.href = '/launch/dashboard/dashboard.html';
    });
    document.getElementById('addTemplateBtn').addEventListener('click', () => openAddForm(teachers));
    document.getElementById('applyFilterBtn').addEventListener('click', loadTemplates);
    document.getElementById('closeDetailBtn').addEventListener('click', () => {
        document.getElementById('detailModal').classList.remove('active');
    });
    document.getElementById('cancelFormBtn').addEventListener('click', () => {
        document.getElementById('templateFormModal').classList.remove('active');
    });

    // Load data
    try {
        teachers = await getTeachers();
        const select = document.getElementById('teacherFilter');
        select.innerHTML = '<option value="">All Teachers</option>';
        teachers.forEach(t => {
            select.innerHTML += `<option value="${t.uuid}">${t.display_name || t.username}</option>`;
        });
        await loadTemplates();
    } catch (e) {
        console.error('Init failed:', e);
    }
}

init();