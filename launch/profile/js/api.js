import { CONFIG } from './config.js';

function getToken() {
    return localStorage.getItem('staff_token');
}

export async function apiCall(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${CONFIG.API_BASE}${path}`, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
}

// Own profile (already exists)
export function getMyProfile() {
    return apiCall('GET', '/staff/me');
}

export function updateMyProfile(data) {
    return apiCall('PUT', '/staff/me', data);
}

// Capabilities schema & data (new endpoints)
export function getCapabilitiesSchema() {
    return apiCall('GET', '/staff/me/capabilities/schema');
}

export function getMyCapabilities() {
    return apiCall('GET', '/staff/me/capabilities');
}

export function updateMyCapabilities(data) {
    return apiCall('PUT', '/staff/me/capabilities', data);
}

// Availability & holidays (existing)
export function getMyAvailability() {
    return apiCall('GET', '/staff/me/availability');
}

export function updateMyAvailability(slots) {
    return apiCall('PUT', '/staff/me/availability', { slots });
}

export function getMyHolidays() {
    return apiCall('GET', '/staff/me/holidays');
}

export function updateMyHolidays(holidays) {
    return apiCall('PUT', '/staff/me/holidays', { holidays });
}