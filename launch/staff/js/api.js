import { API_BASE } from './config.js';

const getToken = () => localStorage.getItem('staff_token');

export async function apiCall(method, path, body = null) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${path}`, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
}