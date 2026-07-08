import { apiCall } from '../../api.js';

export async function render(container) {
    // Header with title and refresh button
    container.innerHTML = `
        <div class="widget-header">
            <span class="widget-title">System Status</span>
            <div class="widget-controls">
                <button class="btn btn-sm btn-secondary" id="buildstatus-refresh-btn">Refresh</button>
            </div>
        </div>
        <div id="buildstatus-content"></div>
    `;

    const content = document.getElementById('buildstatus-content');

    async function refresh() {
        content.innerHTML = '<p>Checking…</p>';

        let info = {
            version: '0.2.0',
            dbStatus: 'ok',
            studentCount: 'unknown',
            backup: 'manual only'
        };

        try {
            const students = await apiCall('GET', '/api/students');
            info.studentCount = students.length;
        } catch (e) {
            info.dbStatus = 'error';
        }

        // Staleness check for holiday/exam data
        let stalenessWarning = '';
        try {
            const metaRes = await apiCall('GET', '/api/events/meta');
            const meta = metaRes.meta || {};
            if (meta.last_updated && meta.update_interval_years) {
                const last = new Date(meta.last_updated);
                const now = new Date();
                const diffMs = now - last;
                const diffYears = diffMs / (1000 * 60 * 60 * 24 * 365.25);
                if (diffYears > meta.update_interval_years) {
                    stalenessWarning = `<p style="color:orange;">Warning: Holiday/exam data may be out of date. Last updated: ${meta.last_updated}</p>`;
                }
            }
        } catch (e) {}

        content.innerHTML = `
            <ul>
                <li>Version: ${info.version}</li>
                <li>Database: ${info.dbStatus}</li>
                <li>Students: ${info.studentCount}</li>
                <li>Backups: ${info.backup}</li>
            </ul>
            ${stalenessWarning}
        `;
    }

    // Initial load
    await refresh();

    // Refresh button
    document.getElementById('buildstatus-refresh-btn').addEventListener('click', refresh);
}
export { render as renderBuildStatus };