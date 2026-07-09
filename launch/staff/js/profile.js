import { escapeHtml } from '../../students/js/utils/helpers.js';
import { updateMyProfile, getMyAvailability, updateMyAvailability } from './api.js';

export async function renderOwnProfile(profile) {
    const container = document.getElementById('ownProfile');
    if (!container) return;

    container.innerHTML = `
        <div class="profile-card">
            <h2>${escapeHtml(profile.display_name || profile.full_name)}</h2>
            <p><strong>Username:</strong> ${profile.username}</p>
            <p><strong>Role:</strong> ${profile.role}</p>
            <p><strong>Email:</strong> ${profile.email || '—'}</p>
            <p><strong>Phone:</strong> ${profile.phone || '—'}</p>
            <p><strong>Timezone:</strong> ${profile.timezone || '—'}</p>
            <p><strong>Rate:</strong> ${profile.default_hourly_rate || 0} K</p>
            <p><strong>Bio:</strong> ${profile.bio || '—'}</p>
            <button id="editOwnProfileBtn" class="btn btn-primary">Edit Profile</button>
        </div>
        <div class="availability-section" style="margin-top:20px;">
            <h3>Availability</h3>
            <div id="availabilityList"></div>
            <button id="editAvailabilityBtn" class="btn btn-secondary">Edit Availability</button>
        </div>
    `;

    document.getElementById('editOwnProfileBtn').addEventListener('click', () => {
        const editHtml = `
            <form id="editOwnForm">
                <label>Full Name</label>
                <input type="text" name="full_name" value="${escapeHtml(profile.full_name || '')}">
                <label>Display Name</label>
                <input type="text" name="display_name" value="${escapeHtml(profile.display_name || '')}">
                <label>Email</label>
                <input type="email" name="email" value="${escapeHtml(profile.email || '')}">
                <label>Phone</label>
                <input type="text" name="phone" value="${escapeHtml(profile.phone || '')}">
                <label>Timezone</label>
                <input type="text" name="timezone" value="${escapeHtml(profile.timezone || '')}">
                <label>Rate (MMK)</label>
                <input type="number" name="default_hourly_rate" value="${profile.default_hourly_rate || 0}">
                <label>Bio</label>
                <textarea name="bio">${escapeHtml(profile.bio || '')}</textarea>
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" id="cancelOwnEditBtn">Cancel</button>
                    <button type="submit" class="btn btn-success">Save</button>
                </div>
            </form>
        `;
        container.innerHTML = editHtml;
        document.getElementById('cancelOwnEditBtn').addEventListener('click', () => renderOwnProfile(profile));
        document.getElementById('editOwnForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            data.default_hourly_rate = parseInt(data.default_hourly_rate, 10) || 0;
            try {
                await updateMyProfile(data);
                alert('Profile updated. Reloading...');
                window.location.reload();
            } catch (err) {
                alert('Update failed: ' + err.message);
            }
        });
    });

    loadAvailability();
}

async function loadAvailability() {
    try {
        const avail = await getMyAvailability();
        const list = document.getElementById('availabilityList');
        if (!list) return;
        if (avail && avail.slots && avail.slots.length) {
            list.innerHTML = avail.slots.map(s => `<div>${s.day} ${s.start}-${s.end} (${s.status})</div>`).join('');
        } else {
            list.innerHTML = '<p>No availability set.</p>';
        }
    } catch (e) {}
}

document.addEventListener('click', async (e) => {
    if (e.target.id === 'editAvailabilityBtn') {
        const current = await getMyAvailability();
        const slots = current && current.slots ? current.slots : [];
        const jsonStr = prompt('Edit availability (JSON array):', JSON.stringify(slots, null, 2));
        if (jsonStr !== null) {
            try {
                const newSlots = JSON.parse(jsonStr);
                await updateMyAvailability(newSlots);
                alert('Availability updated. Reloading...');
                window.location.reload();
            } catch (err) {
                alert('Invalid JSON or update failed: ' + err.message);
            }
        }
    }
});