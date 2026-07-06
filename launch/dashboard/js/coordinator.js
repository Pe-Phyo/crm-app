import { apiCall } from './api.js';
import { renderWidget, setWidgetRegistry } from './widgets.js';

// Register built-in widgets
import { renderChart } from './widgets/chart.js';
import { renderUpcomingDates } from './widgets/upcomingDates.js';
import { renderStudentHighlights } from './widgets/studentHighlights.js';
import { renderInbox } from './widgets/inbox.js';
import { renderBuildStatus } from './widgets/buildStatus.js';

const widgetRegistry = {
    chart: renderChart,
    upcomingDates: renderUpcomingDates,
    studentHighlights: renderStudentHighlights,
    inbox: renderInbox,
    buildStatus: renderBuildStatus,
};
setWidgetRegistry(widgetRegistry);

let currentDashboardConfig = null;

async function boot() {
    const token = localStorage.getItem('staff_token');
    if (!token) {
        window.location.href = '/launch/index.html';
        return;
    }

    let profile;
    try {
        profile = await apiCall('GET', '/api/staff/me');
    } catch (e) {
        localStorage.clear();
        window.location.href = '/launch/index.html';
        return;
    }

    const role = sessionStorage.getItem('view_as_role') || profile.role || localStorage.getItem('staff_role');
    const isViewAs = !!sessionStorage.getItem('view_as_role');

    // Top bar
    const topBar = document.getElementById('top-bar');
    topBar.innerHTML = `
        <div class="greeting">${isViewAs ? 'Viewing as ' + role : profile.display_name || profile.username}</div>
        <div class="actions">
            <div class="eye-menu">
                <button class="btn" id="eye-btn">View as...</button>
                <div class="popup" id="eye-popup"></div>
            </div>
            <button class="btn" id="logout-btn">Logout</button>
        </div>
    `;

    // View-as banner
    if (isViewAs) {
        const banner = document.getElementById('view-as-banner');
        banner.style.display = 'block';
        banner.innerHTML = `Viewing as <strong>${role}</strong> – <a id="back-to-admin">Back to Admin</a>`;
        document.getElementById('back-to-admin').addEventListener('click', () => {
            sessionStorage.removeItem('view_as_role');
            window.location.reload();
        });
    }

    // Eye menu
    const eyePopup = document.getElementById('eye-popup');
    if (profile.role === 'admin') {
        const roles = ['teacher', 'front_office', 'back_office', 'bot', 'dev'];
        eyePopup.innerHTML = roles.map(r => `<a href="#" data-role="${r}">${r.replace('_', ' ')}</a>`).join('')
            + '<a href="#" data-role="admin">admin (own)</a>';
        eyePopup.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const selectedRole = e.target.dataset.role;
                if (selectedRole === 'admin') {
                    sessionStorage.removeItem('view_as_role');
                } else {
                    sessionStorage.setItem('view_as_role', selectedRole);
                }
                window.location.reload();
            });
        });
    } else {
        eyePopup.innerHTML = '<a href="#">No other roles</a>';
    }

    const eyeBtn = document.getElementById('eye-btn');
    eyeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        eyePopup.style.display = eyePopup.style.display === 'block' ? 'none' : 'block';
    });
    document.addEventListener('click', () => { eyePopup.style.display = 'none'; });

    // Logout
    document.getElementById('logout-btn').addEventListener('click', async () => {
        try { await apiCall('POST', '/api/auth/staff/logout'); } catch (e) {}
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = '/launch/index.html';
    });

    // Load dashboard config
    const configModule = await import(`./dashboards/${role}.js`);
    currentDashboardConfig = configModule.default;

    // Build main grid
    const mainGrid = document.getElementById('main-grid');
    mainGrid.style.gridTemplateColumns = currentDashboardConfig.layout === 'split-65-35' ? '35fr 65fr' : '1fr 1fr';
    mainGrid.innerHTML = '';

    for (const widgetDef of currentDashboardConfig.widgets) {
        const widgetContainer = document.createElement('div');
        widgetContainer.className = 'widget';
        widgetContainer.id = `widget-${widgetDef.id}`;
        const position = widgetDef.position || 'left';
        widgetContainer.style.gridColumn = position === 'right' ? '2' : '1';
        mainGrid.appendChild(widgetContainer);
        await renderWidget(widgetContainer, widgetDef);
    }

    // Bottom tabs
    const tabNav = document.querySelector('.tab-nav');
    const tabContent = document.querySelector('.tab-content');
    const tabs = currentDashboardConfig.bottomTabs || [];

    tabs.forEach((tab, index) => {
        const btn = document.createElement('button');
        btn.textContent = tab.label;
        btn.dataset.tabId = tab.id;
        btn.addEventListener('click', () => switchTab(tab.id));
        tabNav.appendChild(btn);
    });

    if (tabs.length > 0) {
        switchTab(tabs[0].id);
    }

    async function switchTab(tabId) {
        tabNav.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        const activeBtn = tabNav.querySelector(`[data-tab-id="${tabId}"]`);
        if (activeBtn) activeBtn.classList.add('active');

        const tabDef = tabs.find(t => t.id === tabId);
        tabContent.innerHTML = '';

        if (tabDef && tabDef.component) {
            try {
                const module = await import(`./widgets/${tabDef.component}.js`);
                if (module && typeof module.render === 'function') {
                    await module.render(tabContent);
                } else {
                    tabContent.innerHTML = `<p>Widget "${tabDef.component}" has no render function.</p>`;
                }
            } catch (err) {
                console.warn(`Could not load widget "${tabDef.component}":`, err);
                tabContent.innerHTML = `<p>Widget "${tabDef.component}" not found.</p>`;
            }
        }
    } // end of switchTab
} // end of boot

// Auto-start
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
} else {
    boot();
}