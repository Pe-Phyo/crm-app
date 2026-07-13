import { CONFIG } from './config.js';

export function getToken() {
    return localStorage.getItem('staff_token');
}

export async function apiCall(method, path, body = null) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${CONFIG.API_BASE}${path}`, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
}

// Own profile
export async function getMyProfile() {
    return await apiCall('GET', '/staff/me');
}

export async function updateMyProfile(data) {
    return await apiCall('PUT', '/staff/me', data);
}

export async function getMyAvailability() {
    return await apiCall('GET', '/staff/me/availability');
}

export async function updateMyAvailability(slots) {
    return await apiCall('PUT', '/staff/me/availability', { slots });
}

// Management (admin/back‑office)
export async function getStaffList() {
    return await apiCall('GET', '/staff');
}

export async function getStaffDetailed() {
    return await apiCall('GET', '/staff/detailed');
}

export async function getStaffProfile(uuid) {
    return await apiCall('GET', `/staff/${uuid}`);
}

export async function updateStaffProfile(uuid, data) {
    return await apiCall('PUT', `/staff/${uuid}`, data);
}

export async function getCapabilitiesSchema() {
    return await apiCall('GET', '/staff/me/capabilities/schema');
}

export async function getMyCapabilities() {
    return await apiCall('GET', '/staff/me/capabilities');
}

export async function updateMyCapabilities(data) {
    return await apiCall('PUT', '/staff/me/capabilities', data);
}