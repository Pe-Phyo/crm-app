import { CONFIG } from './config.js';

export function getToken() {
    return localStorage.getItem('staff_token');
}

export async function apiCall(method, path, body = null, suppressAuth = false) {
    const headers = { 'Content-Type': 'application/json' };
    if (!suppressAuth) {
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${CONFIG.API_BASE}${path}`, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
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

// Attendance (now via Teacher domain)
export async function getAttendance(studentUuid) {
    return await apiCall('GET', `/teacher/attendance?student_uuid=${encodeURIComponent(studentUuid)}`);
}
export async function markAttendance(studentUuid, meetingId, date, status) {
    return await apiCall('POST', '/teacher/attendance', {
        student_uuid: studentUuid,
        meeting_id: meetingId,
        date,
        status
    });
}

// Payments (now via Front Office domain)
export async function getPayments(studentUuid) {
    return await apiCall('GET', `/frontoffice/payments?student_uuid=${encodeURIComponent(studentUuid)}`);
}
export async function addPayment(studentUuid, amount, date) {
    return await apiCall('POST', '/frontoffice/payments', {
        student_uuid: studentUuid,
        amount,
        date
    });
}

// Actions (still using legacy student index – we keep them for now)
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