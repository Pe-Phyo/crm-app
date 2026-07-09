import { getMyProfile, getStaffDetailed } from './api.js';
import { renderOwnProfile } from './profile.js';
import { renderStaffList, bindFilterEvents } from './list.js';
import { openStaffDetail } from './detailView.js';
import { openAddStaffForm } from './addForm.js';

let currentStaff = [];

async function init() {
    const token = localStorage.getItem('staff_token');
    if (!token) {
        window.location.href = '/launch/index.html';
        return;
    }

    // Verify token
    try {
        await fetch('/api/staff/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
    } catch (e) {
        localStorage.clear();
        window.location.href = '/launch/index.html';
        return;
    }

    // Back button
    document.getElementById('backBtn').addEventListener('click', () => {
        window.location.href = '/launch/dashboard/dashboard.html';
    });

    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');
    const myProfile = await getMyProfile();
    const role = myProfile.role;

    if (mode === 'self' || (role !== 'admin' && role !== 'back_office')) {
        document.getElementById('pageTitle').textContent = 'My Profile';
        document.getElementById('ownProfile').style.display = 'block';
        renderOwnProfile(myProfile);
    } else {
        document.getElementById('addStaffBtn').style.display = 'inline-block';
        document.getElementById('managementView').style.display = 'block';
        currentStaff = await getStaffDetailed();
        renderStaffList(currentStaff, openStaffDetail);
        bindFilterEvents(currentStaff, renderStaffList, openStaffDetail);
    }

    document.getElementById('closeDetailBtn').addEventListener('click', () => {
        document.getElementById('detailModal').classList.remove('active');
        document.getElementById('addStaffBtn').addEventListener('click', openAddStaffForm);
    });
}

init();