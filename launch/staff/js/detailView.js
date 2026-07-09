import { getStaffProfile, updateStaffProfile } from './api.js';
import { escapeHtml } from '../../students/js/utils/helpers.js';

const detailModal = document.getElementById('detailModal');
const detailContent = document.getElementById('detailContent');

export async function openStaffDetail(uuid) {
    try {
        const profile = await getStaffProfile(uuid);
        const isActive = profile.is_active;
        const html = `
            <h3>${escapeHtml(profile.display_name || profile.full_name || profile.username)}</h3>
            <p><strong>Username:</strong> ${profile.username}</p>
            <p><strong>Role:</strong> ${profile.role}</p>
            <p><strong>Active:</strong> ${isActive ? 'Yes' : 'No'}</p>
            <p><strong>Email:</strong> ${profile.email || '—'}</p>
            <p><strong>Phone:</strong> ${profile.phone || '—'}</p>
            <p><strong>Timezone:</strong> ${profile.timezone || '—'}</p>
            <p><strong>Bio:</strong> ${profile.bio || '—'}</p>
            <div class="modal-actions" style="flex-wrap:wrap; gap:0.5rem; justify-content:flex-start;">
                <button id="editStaffBtn" class="btn btn-primary">Edit</button>
                <button id="toggleActiveBtn" class="btn btn-secondary">${isActive ? 'Deactivate' : 'Activate'}</button>
                <button id="resetPasswordBtn" class="btn btn-secondary">Reset Password</button>
                <button id="deleteStaffBtn" class="btn btn-danger">Delete</button>
            </div>
        `;
        detailContent.innerHTML = html;
        detailModal.classList.add('active');

        document.getElementById('editStaffBtn').addEventListener('click', () => {
            detailModal.classList.remove('active');
            openEditStaffModal(profile);
        });

        document.getElementById('toggleActiveBtn').addEventListener('click', async () => {
            const mep = prompt('Enter Master Encryption Password to ' + (isActive ? 'deactivate' : 'activate') + ' this staff member:');
            if (!mep) return;
            try {
                await updateStaffProfile(uuid, { is_active: !isActive, mep_password: mep });
                alert('Status updated.');
                detailModal.classList.remove('active');
                window.location.reload();
            } catch (err) {
                alert('Failed: ' + err.message);
            }
        });

        document.getElementById('resetPasswordBtn').addEventListener('click', async () => {
            const newPw = prompt('Enter new password (min 6 chars):');
            if (!newPw || newPw.length < 6) {
                alert('Password too short.');
                return;
            }
            const mep = prompt('Enter Master Encryption Password to confirm reset:');
            if (!mep) return;
            try {
                // Call the dedicated password reset endpoint
                const res = await fetch('/api/staff/' + uuid + '/password', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('staff_token')
                    },
                    body: JSON.stringify({ new_password: newPw, mep_password: mep })
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.error || 'Request failed');
                }
                alert('Password reset. User must change it on next login.');
                detailModal.classList.remove('active');
            } catch (err) {
                alert('Reset failed: ' + err.message);
            }
        });

        document.getElementById('deleteStaffBtn').addEventListener('click', async () => {
            if (!confirm('Permanently delete this staff member? This cannot be undone.')) return;
            const mep = prompt('Enter Master Encryption Password to confirm deletion:');
            if (!mep) return;
            try {
                const res = await fetch('/api/staff/' + uuid, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('staff_token')
                    },
                    body: JSON.stringify({ mep_password: mep })
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.error || 'Request failed');
                }
                alert('Staff deleted.');
                detailModal.classList.remove('active');
                window.location.reload();
            } catch (err) {
                alert('Deletion failed: ' + err.message);
            }
        });

    } catch (e) {
        alert('Failed to load staff details');
    }
}

function openEditStaffModal(profile) {
    detailContent.innerHTML = `
        <h3>Edit ${escapeHtml(profile.display_name || profile.full_name)}</h3>
        <form id="editStaffForm">
            <label>Full Name</label>
            <input type="text" name="full_name" value="${escapeHtml(profile.full_name || '')}">
            <label>Display Name</label>
            <input type="text" name="display_name" value="${escapeHtml(profile.display_name || '')}">
            <label>Email</label>
            <input type="email" name="email" value="${escapeHtml(profile.email || '')}">
            <label>Phone</label>
            <input type="text" name="phone" value="${escapeHtml(profile.phone || '')}">
            <label>Timezone</label>
            <input type="text" name="timezone" value="${escapeHtml(profile.timezone || '')}">
            <label>Bio</label>
            <textarea name="bio">${escapeHtml(profile.bio || '')}</textarea>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" id="cancelEditBtn">Cancel</button>
                <button type="submit" class="btn btn-success">Save</button>
            </div>
        </form>
    `;
    detailModal.classList.add('active');

    document.getElementById('cancelEditBtn').addEventListener('click', () => {
        detailModal.classList.remove('active');
    });

    document.getElementById('editStaffForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        try {
            await updateStaffProfile(profile.uuid, data);
            alert('Profile updated');
            detailModal.classList.remove('active');
            window.location.reload();
        } catch (err) {
            alert('Update failed: ' + err.message);
        }
    });
}