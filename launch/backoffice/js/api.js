import { apiCall } from '../../dashboard/js/api.js';

export async function getTeachers() {
    // Same endpoint used by student form; already returns only teachers
    return await apiCall('GET', '/api/staff/teachers');
}

export async function getTemplates(teacherId = null) {
    let url = '/api/pricing/templates';
    if (teacherId) url += `?teacher_id=${encodeURIComponent(teacherId)}`;
    return await apiCall('GET', url);
}

export async function createTemplate(data) {
    return await apiCall('POST', '/api/pricing/templates', data);
}

export async function updateTemplate(id, data) {
    return await apiCall('PUT', `/api/pricing/templates/${id}`, data);
}

export async function deleteTemplate(id) {
    return await apiCall('DELETE', `/api/pricing/templates/${id}`);
}