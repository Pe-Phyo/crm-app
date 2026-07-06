const getToken = () => localStorage.getItem('staff_token');

export async function apiCall(method, path, body = null) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
}

// Specific login function (no token needed)
export async function login(username, password) {
    const res = await fetch('/api/auth/staff/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Login failed');
    return data;
}

// Dashboard-specific endpoints
export function fetchDashboardSummary() {
    return apiCall('GET', '/api/dashboard/summary');
}

export function fetchInbox(role) {
    const query = role ? `?role=${role}` : '';
    return apiCall('GET', `/api/dashboard/inbox${query}`);
}

export function createNote(text, urgency, timeliness) {
    return apiCall('POST', '/api/dashboard/inbox/note', { text, urgent: urgency, timely: timeliness });
}

export function updateInboxItem(id, updates) {
    return apiCall('PATCH', `/api/dashboard/inbox/${id}`, updates);
}

export function fetchChartData(chartId) {
    return apiCall('GET', `/api/dashboard/analytics/${chartId}`);
}

export function fetchBuildStatus() {
    return apiCall('GET', '/api/dashboard/build-status');
}

export function fetchInboxConfig(role) {
    return apiCall('GET', `/api/dashboard/inbox-config?role=${role}`);
}