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

// Students CRUD
export async function getStudents() {
    return await apiCall('GET', '/students');
}

export async function getStudent(uuid) {
    return await apiCall('GET', `/students/${uuid}`);
}

export async function createStudent(data) {
    return await apiCall('POST', '/students', data);
}

export async function updateStudent(uuid, data) {
    return await apiCall('PUT', `/students/${uuid}`, data);
}

export async function deleteStudent(uuid) {
    return await apiCall('DELETE', `/students/${uuid}`);
}

// Attendance
export async function getAttendance(uuid) {
    return await apiCall('GET', `/students/${uuid}/attendance`);
}

export async function addAttendance(uuid, data) {
    return await apiCall('POST', `/students/${uuid}/attendance`, data);
}

export async function updateAttendance(uuid, logId, data) {
    return await apiCall('PUT', `/students/${uuid}/attendance/${logId}`, data);
}

// Payments
export async function getPayments(uuid) {
    return await apiCall('GET', `/students/${uuid}/payments`);
}

export async function addPayment(uuid, data) {
    return await apiCall('POST', `/students/${uuid}/payments`, data);
}

// Actions
export async function getActions() {
    return await apiCall('GET', '/actions');
}

export async function addAction(text) {
    return await apiCall('POST', '/actions', { text });
}

export async function updateAction(id, updates) {
    return await apiCall('PUT', `/actions/${id}`, updates);
}

export async function deleteAction(id) {
    return await apiCall('DELETE', `/actions/${id}`);
}