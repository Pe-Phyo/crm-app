import { apiCall } from '../../api.js';

export async function render(container, widgetDef) {
    container.innerHTML = '<p>Loading...</p>';
    try {
        const holidays = await apiCall('GET', '/api/staff/me/holidays');
        const upcoming = (holidays || []).filter(h => h.status === 'approved' || h.status === 'pending');
        if (upcoming.length === 0) {
            container.innerHTML = '<p>No upcoming time off.</p>';
        } else {
            const list = upcoming.map(h => `<li>${h.start_date} → ${h.end_date} (${h.status})</li>`).join('');
            container.innerHTML = `<ul>${list}</ul>`;
        }
        container.innerHTML += '<p style="margin-top:1em;">Time off requests will be available in the profile editor.</p>';
    } catch (e) {
        container.innerHTML = '<p>Could not load time off data.</p>';
    }
}