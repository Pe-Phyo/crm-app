import { apiCall } from './api.js';
import { renderWidget, setWidgetRegistry } from './widgets.js';

const WIDGET_PATH_MAP = {
    upcomingDates:     './widgets/column1/upcomingDates.js',
    studentHighlights: './widgets/column1/studentHighlights.js',
    paymentsSummary:   './widgets/column1/paymentsSummary.js',
    attendance:        './widgets/column1/attendance.js',
    botHealth:         './widgets/column1/botHealth.js',
    agentHealth:       './widgets/column1/agentHealth.js',
    meetings:          './widgets/column2/meetings.js',
    messages:          './widgets/column2/messages.js',
    analytics:         './widgets/column2/analytics/index.js',
    inbox:             './widgets/bottom/inbox.js',
    buildStatus:       './widgets/bottom/buildStatus.js',
    allLogs:           './widgets/bottom/allLogs.js',
    errors:            './widgets/bottom/errors.js',
    templates:         './widgets/bottom/templates.js',
    addFinances:       './widgets/bottom/addFinances.js',
    activityLog:       './widgets/bottom/activityLog.js',
    apiConsole:        './widgets/bottom/apiConsole.js',
};

const widgetRegistry = {};
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

    const realRole = profile.role;
    const role = sessionStorage.getItem('view_as_role') || realRole;
    const isViewAs = !!sessionStorage.getItem('view_as_role');

    // ---- Top bar ----
    let greetingText;
    if (realRole === 'admin') {
        greetingText = 'Admin Dashboard';
    } else if (realRole === 'bot') {
        greetingText = 'Bot Management';
    } else if (realRole === 'dev') {
        greetingText = 'System & Dev Dashboard';
    } else {
        greetingText = 'Mingalabar ' + (profile.display_name || profile.username);
    }
    if (isViewAs) {
        greetingText = 'Viewing as ' + role;
    }

    const topBar = document.getElementById('top-bar');
    topBar.innerHTML = `
        <div class="greeting">${greetingText}</div>
        <div class="actions">
            <div class="eye-menu">
                <button class="btn" id="eye-btn">View</button>
                <div class="popup" id="eye-popup"></div>
            </div>
            <button class="btn" id="logout-btn">Logout</button>
        </div>
    `;

    // View-as banner
    if (isViewAs) {
        const banner = document.getElementById('view-as-banner');
        banner.style.display = 'block';
        banner.innerHTML = `Viewing as <strong>${role}</strong> – <a id="back-to-admin">Back to ${realRole}</a>`;
        document.getElementById('back-to-admin').addEventListener('click', () => {
            sessionStorage.removeItem('view_as_role');
            window.location.reload();
        });
    }

    // Logout
    document.getElementById('logout-btn').addEventListener('click', async () => {
        try { await apiCall('POST', '/api/auth/staff/logout'); } catch (e) {}
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = '/launch/index.html';
    });

    // ---- Load dashboard config FIRST ----
    try {
        const configModule = await import(`./dashboards/${role}.js`);
        currentDashboardConfig = configModule.default;
        if (!currentDashboardConfig) throw new Error('Empty config');
    } catch (e) {
        document.body.innerHTML = `<div style="color:var(--danger);padding:2rem;">
            <h2>Dashboard config not found</h2>
            <p>Could not load config for role <strong>${role}</strong>.</p>
            <p>File needed: <code>launch/dashboard/js/dashboards/${role}.js</code></p>
        </div>`;
        return;
    }

    // ---- Eye menu (now config is guaranteed to exist) ----
    const eyePopup = document.getElementById('eye-popup');
    const eyeMenu = currentDashboardConfig.eyeMenu || [];

    if (eyeMenu.length > 0) {
        eyePopup.innerHTML = eyeMenu.map((item, index) =>
            `<a href="#" data-index="${index}">${item.label}</a>`
        ).join('');
        eyePopup.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const idx = parseInt(link.dataset.index, 10);
                const item = eyeMenu[idx];
                if (!item) return;
                const action = item.action || '#';
                if (action.startsWith('switch-role:')) {
                    const targetRole = action.split(':')[1];
                    if (targetRole === realRole) {
                        sessionStorage.removeItem('view_as_role');
                    } else {
                        sessionStorage.setItem('view_as_role', targetRole);
                    }
                    window.location.reload();
                } else if (action && action !== '#') {
                    window.location.href = action;
                }
            });
        });
    } else {
        // Fallback to hardcoded role-switching for admin, placeholder for others
        if (realRole === 'admin') {
            const roles = ['teacher', 'front_office', 'back_office', 'bot', 'dev', 'admin'];
            eyePopup.innerHTML = roles.map(r => `<a href="#" data-role="${r}">${r.replace('_', ' ')}</a>`).join('');
            eyePopup.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const selectedRole = e.target.dataset.role;
                    if (selectedRole === realRole) {
                        sessionStorage.removeItem('view_as_role');
                    } else {
                        sessionStorage.setItem('view_as_role', selectedRole);
                    }
                    window.location.reload();
                });
            });
        } else {
            eyePopup.innerHTML = '<a href="#" style="color:var(--muted);">Coming soon</a>';
            eyePopup.querySelector('a').addEventListener('click', (e) => e.preventDefault());
        }
    }

    const eyeBtn = document.getElementById('eye-btn');
    eyeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        eyePopup.style.display = eyePopup.style.display === 'block' ? 'none' : 'block';
    });
    document.addEventListener('click', () => { eyePopup.style.display = 'none'; });

    // ---- Collect needed widgets ----
    const neededWidgets = new Set();
    currentDashboardConfig.widgets.forEach(w => neededWidgets.add(w.type));
    (currentDashboardConfig.bottomTabs || []).forEach(tab => neededWidgets.add(tab.component));

    // ---- Load widgets dynamically ----
    const loadPromises = Array.from(neededWidgets).map(async (type) => {
        const path = WIDGET_PATH_MAP[type];
        if (!path) {
            console.warn(`Widget type "${type}" has no entry in WIDGET_PATH_MAP. Skipping.`);
            return;
        }
        try {
            const module = await import(path);
            if (typeof module.render === 'function') {
                widgetRegistry[type] = module.render;
            } else if (typeof module.default === 'function') {
                widgetRegistry[type] = module.default;
            } else {
                const keys = Object.keys(module);
                const renderKey = keys.find(k => k.startsWith('render'));
                if (renderKey && typeof module[renderKey] === 'function') {
                    widgetRegistry[type] = module[renderKey];
                } else {
                    console.warn(`Widget "${type}" module loaded but no render function found.`);
                }
            }
        } catch (err) {
            console.warn(`Failed to load widget "${type}" from ${path}:`, err);
        }
    });
    await Promise.all(loadPromises);
    setWidgetRegistry(widgetRegistry);

    // ---- Build main grid ----
    const mainGrid = document.getElementById('main-grid');
    mainGrid.style.gridTemplateColumns = currentDashboardConfig.layout === 'split-65-35' ? '35fr 65fr' : '1fr 1fr';
    mainGrid.innerHTML = '';

    for (const widgetDef of currentDashboardConfig.widgets) {
        const widgetContainer = document.createElement('div');
        widgetContainer.className = 'widget';
        widgetContainer.id = `widget-${widgetDef.id}`;
        widgetContainer.style.gridColumn = widgetDef.position === 'right' ? '2' : '1';
        mainGrid.appendChild(widgetContainer);
        await renderWidget(widgetContainer, widgetDef);
    }

    // ---- Bottom tabs ----
    const tabNav = document.querySelector('.tab-nav');
    const tabContent = document.querySelector('.tab-content');
    const tabs = currentDashboardConfig.bottomTabs || [];
    tabs.forEach(tab => {
        const btn = document.createElement('button');
        btn.textContent = tab.label;
        btn.dataset.tabId = tab.id;
        btn.addEventListener('click', () => switchTab(tab.id));
        tabNav.appendChild(btn);
    });
    if (tabs.length > 0) switchTab(tabs[0].id);

    async function switchTab(tabId) {
        tabNav.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        const activeBtn = tabNav.querySelector(`[data-tab-id="${tabId}"]`);
        if (activeBtn) activeBtn.classList.add('active');
        const tabDef = tabs.find(t => t.id === tabId);
        tabContent.innerHTML = '';
        if (tabDef) {
            const renderFn = widgetRegistry[tabDef.component];
            if (renderFn) await renderFn(tabContent, tabDef);
            else tabContent.innerHTML = `<p>Widget "${tabDef.component}" not loaded.</p>`;
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
} else {
    boot();
}