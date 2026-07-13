import { escapeHtml } from '../../students/js/utils/helpers.js';
import {
    getMyAvailability,
    updateMyAvailability
} from './api.js';

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
        </div>
        <div class="availability-section" style="margin-top:20px;">
            <h3>Availability</h3>
            <div id="availabilityList"></div>
            <button id="editAvailabilityBtn" class="btn btn-secondary">Edit Availability</button>
        </div>
    `;

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