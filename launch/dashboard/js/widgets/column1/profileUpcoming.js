import { apiCall } from '../../api.js';

export async function render(container, widgetDef) {
    container.innerHTML = '<p>Loading...</p>';
    try {
        const holidays = await apiCall('GET', '/api/staff/me/holidays');
        if (!holidays || holidays.length === 0) {
            container.innerHTML = '<p>No upcoming holidays.</p>';
            return;
        }
        const list = holidays.map(h => `
            <div class="event-item">
                <span>${h.start_date} → ${h.end_date}</span>
                <span>${h.description || ''}</span>
                <span class="status">${h.status}</span>
            </div>
        `).join('');
        container.innerHTML = `<div class="events-list">${list}</div>`;
    } catch (e) {
        container.innerHTML = '<p>Could not load holidays.</p>';
    }
}