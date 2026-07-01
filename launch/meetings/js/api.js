// ============================================================
//  API LAYER - Talks to Python backend
// ============================================================

const API_BASE = '/api';

export async function fetchMeetings() {
    const res = await fetch(`${API_BASE}/meetings`);
    if (!res.ok) throw new Error('Failed to fetch meetings');
    return res.json();
}

export async function addMeeting(meeting) {
    const res = await fetch(`${API_BASE}/meetings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(meeting)
    });
    if (!res.ok) throw new Error('Failed to add meeting');
    return res.json();
}

export async function updateMeeting(id, updates) {
    const res = await fetch(`${API_BASE}/meetings/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
    });
    if (!res.ok) throw new Error('Failed to update meeting');
    return res.json();
}

export async function deleteMeeting(id) {
    const res = await fetch(`${API_BASE}/meetings/${id}`, {
        method: 'DELETE'
    });
    if (!res.ok) throw new Error('Failed to delete meeting');
    return res.json();
}