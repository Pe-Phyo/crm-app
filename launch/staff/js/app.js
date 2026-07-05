import { apiCall } from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    const role = localStorage.getItem('staff_role');
    if (role === 'admin') {
        document.getElementById('admin-panel').style.display = 'block';
        loadStaffList();
    } else {
        document.getElementById('own-profile').style.display = 'block';
        loadOwnProfile();
    }
    setupCreateForm();
    setupProfileForm();
});

// Admin functions
async function loadStaffList() {
    try {
        const staff = await apiCall('GET', '/staff');
        const ul = document.getElementById('staff-list');
        ul.innerHTML = staff.map(s => 
            `<li>${s.username} (${s.role}) - ${s.is_active ? 'Active' : 'Inactive'} [UUID: ${s.uuid}]</li>`
        ).join('');
    } catch(e) { console.error(e); }
}

window.approveStaff = async () => {
    const uuid = document.getElementById('approve-uuid').value;
    const mep = document.getElementById('approve-mep').value;
    try {
        await apiCall('POST', `/staff/approve/${uuid}`, { mep_password: mep });
        alert('Staff approved');
        loadStaffList();
    } catch(e) { alert(e.message); }
};

window.deleteStaff = async () => {
    const uuid = document.getElementById('delete-uuid').value;
    const mep = document.getElementById('delete-mep').value;
    if (!confirm('Are you sure?')) return;
    try {
        await apiCall('DELETE', `/staff/${uuid}`, { mep_password: mep });
        alert('Deleted');
        loadStaffList();
    } catch(e) { alert(e.message); }
};

function setupCreateForm() {
    document.getElementById('create-staff-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('new-username').value;
        const password = document.getElementById('new-password').value;
        const role = document.getElementById('new-role').value;
        const full_name = document.getElementById('new-fullname').value;
        try {
            await apiCall('POST', '/staff', { username, password, role, full_name });
            alert('Staff created (inactive). UUID shown in list.');
            loadStaffList();
        } catch(e) { alert(e.message); }
    });
}

// Profile functions
async function loadOwnProfile() {
    try {
        const profile = await apiCall('GET', '/staff/me');
        document.getElementById('full_name').value = profile.full_name || '';
        document.getElementById('display_name').value = profile.display_name || '';
        document.getElementById('email').value = profile.email || '';
        document.getElementById('phone').value = profile.phone || '';
        document.getElementById('timezone').value = profile.timezone || '';
        document.getElementById('hourly_rate').value = profile.default_hourly_rate || 0;
        document.getElementById('meeting_link_pattern').value = profile.default_meeting_link_pattern || '';
        document.getElementById('bio').value = profile.bio || '';
        // Load availability and holidays
        const avail = await apiCall('GET', '/staff/me/availability');
        renderAvailabilityGrid(avail);
        const holidays = await apiCall('GET', '/staff/me/holidays');
        renderHolidays(holidays);
    } catch(e) { console.error(e); }
}

function setupProfileForm() {
    document.getElementById('profile-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            full_name: document.getElementById('full_name').value,
            display_name: document.getElementById('display_name').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            timezone: document.getElementById('timezone').value,
            default_hourly_rate: parseInt(document.getElementById('hourly_rate').value) || 0,
            default_meeting_link_pattern: document.getElementById('meeting_link_pattern').value,
            bio: document.getElementById('bio').value
        };
        try {
            await apiCall('PUT', '/staff/me', data);
            alert('Profile updated');
        } catch(e) { alert(e.message); }
    });
}

window.changePassword = async () => {
    const old_pw = document.getElementById('old-pw').value;
    const new_pw = document.getElementById('new-pw').value;
    try {
        await apiCall('PUT', '/staff/me/password', { old_password: old_pw, new_password: new_pw });
        alert('Password changed');
    } catch(e) { alert(e.message); }
};

// Availability grid
let availabilitySlots = [];

function renderAvailabilityGrid(slots) {
    availabilitySlots = slots;
    const tbody = document.querySelector('#availability-grid tbody');
    tbody.innerHTML = '';
    const hours = ['06:00','07:00','08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00','20:00','21:00','22:00'];
    const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
    hours.forEach(hour => {
        const row = document.createElement('tr');
        const timeCell = document.createElement('td');
        timeCell.textContent = hour;
        row.appendChild(timeCell);
        days.forEach((day, idx) => {
            const cell = document.createElement('td');
            cell.dataset.day = idx; // 0=Mon
            cell.dataset.time = hour;
            // Check if slot exists
            const slot = slots.find(s => s.day_of_week == idx && s.start_time == hour);
            if (slot) {
                cell.classList.add(slot.status); // 'approved' or 'pending'
            }
            cell.addEventListener('click', () => toggleSlot(cell, idx, hour));
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
}

function toggleSlot(cell, dayOfWeek, startTime) {
    const existing = availabilitySlots.find(s => s.day_of_week == dayOfWeek && s.start_time == startTime);
    if (existing) {
        // Remove slot
        availabilitySlots = availabilitySlots.filter(s => s !== existing);
        cell.className = '';
    } else {
        // Add slot (default end time 1 hour later)
        const endHour = String(parseInt(startTime) + 1).padStart(2, '0') + ':00';
        const newSlot = {
            day_of_week: dayOfWeek,
            start_time: startTime,
            end_time: endHour,
            status: 'pending'   // will be saved as pending unless admin
        };
        availabilitySlots.push(newSlot);
        cell.classList.add('pending');
    }
}

// Save availability button
document.getElementById('save-availability-btn')?.addEventListener('click', async () => {
    try {
        await apiCall('PUT', '/staff/me/availability', { slots: availabilitySlots });
        document.getElementById('availability-status').textContent = 'Saved!';
        // Refresh to show approved status if admin
        loadOwnProfile();
    } catch(e) {
        document.getElementById('availability-status').textContent = 'Error: ' + e.message;
    }
});

// Holidays
let holidaysList = [];

function renderHolidays(holidays) {
    holidaysList = holidays;
    const ul = document.getElementById('holidays-list');
    ul.innerHTML = holidays.map(h => `<li>${h.start_date} to ${h.end_date} - ${h.description} (${h.status}) <button class="remove-holiday" data-id="${h.id}">X</button></li>`).join('');
    // Attach remove handlers
    ul.querySelectorAll('.remove-holiday').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = parseInt(btn.dataset.id);
            holidaysList = holidaysList.filter(h => h.id !== id);
            renderHolidays(holidaysList);
        });
    });
}

document.getElementById('add-holiday-btn')?.addEventListener('click', () => {
    const start = document.getElementById('holiday-start').value;
    const end = document.getElementById('holiday-end').value;
    const desc = document.getElementById('holiday-desc').value;
    if (!start || !end) return;
    const newHoliday = {
        id: Date.now(),   // temporary id (backend will replace on save)
        start_date: start,
        end_date: end,
        description: desc,
        status: 'pending'
    };
    holidaysList.push(newHoliday);
    renderHolidays(holidaysList);
    // Clear inputs
    document.getElementById('holiday-start').value = '';
    document.getElementById('holiday-end').value = '';
    document.getElementById('holiday-desc').value = '';
});

document.getElementById('save-holidays-btn')?.addEventListener('click', async () => {
    try {
        await apiCall('PUT', '/staff/me/holidays', { holidays: holidaysList });
        document.getElementById('holidays-status').textContent = 'Saved!';
        loadOwnProfile();
    } catch(e) {
        document.getElementById('holidays-status').textContent = 'Error: ' + e.message;
    }
});