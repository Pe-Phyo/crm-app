import { apiCall } from '../../api.js';

export async function renderUpcomingDates(container) {
    container.innerHTML = '<p>Loading upcoming events...</p>';
    try {
        const data = await apiCall('GET', '/api/dashboard/upcoming-events?days=14');
        const events = data.events || [];
        if (!events.length) {
            container.innerHTML = '<p>No upcoming events in the next 14 days.</p>';
            return;
        }
        let html = '<h3>Upcoming</h3><ul>';
        events.forEach(e => {
            // e.flag is already an emoji like 🇲🇲
            html += `<li>${e.flag} <strong>${e.date}</strong> – ${escapeHtml(e.name)} (${e.type})</li>`;
        });
        html += '</ul>';
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = '<p>Could not load events.</p>';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}