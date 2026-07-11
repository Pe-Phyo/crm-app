import { apiCall } from '../../api.js';

export async function render(container, widgetDef) {
    container.innerHTML = '<p>Loading profile...</p>';
    let profile;
    try {
        profile = await apiCall('GET', '/api/staff/me');
    } catch (err) {
        container.innerHTML = '<p style="color:red;">Failed to load profile.</p>';
        return;
    }

    const displayName = profile.display_name || profile.full_name || profile.username;
    const role = profile.role || '—';
    const email = profile.email || '—';
    const phone = profile.phone || '—';
    const timezone = profile.timezone || '—';
    const rate = profile.default_hourly_rate ? `${profile.default_hourly_rate} MMK` : '—';
    const bio = profile.bio || '—';

    container.innerHTML = `
        <div class="profile-card">
            <h3>${escapeHtml(displayName)}</h3>
            <p><strong>Role:</strong> ${role}</p>
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Phone:</strong> ${phone}</p>
            <p><strong>Timezone:</strong> ${timezone}</p>
            <p><strong>Rate:</strong> ${rate}</p>
            <p><strong>Bio:</strong> ${escapeHtml(bio)}</p>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}