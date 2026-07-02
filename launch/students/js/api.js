import { CONFIG } from './config.js';

let authToken = null;

export function setToken(token) {
    authToken = token;
    localStorage.setItem('student_token', token);
}

export function getToken() {
    if (!authToken) {
        authToken = localStorage.getItem('student_token');
    }
    return authToken;
}

export async function apiCall(method, path, body = null, suppressAuth = false) {
    const headers = {
        'Content-Type': 'application/json',
    };
    if (!suppressAuth) {
        const token = getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }
    const opts = { method, headers };
    if (body) {
        opts.body = JSON.stringify(body);
    }
    const res = await fetch(`${CONFIG.API_BASE}${path}`, opts);
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || 'Request failed');
    }
    return data;
}

export async function login(password) {
    const data = await apiCall('POST', '/auth/login', { password });
    setToken(data.token);
    return data;
}

export async function getStudents() {
    return await apiCall('GET', '/students');
}

export async function getActions() {
    return await apiCall('GET', '/actions');
}