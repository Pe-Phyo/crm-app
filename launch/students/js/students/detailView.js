import { getStudent, apiCall, getAttendance, getPayments } from '../api.js';
import { escapeHtml } from '../utils/helpers.js';
import { openEditForm } from './addForm.js';

const detailModal = document.getElementById('detailModal');
const detailContent = document.getElementById('detailContent');
const closeDetailBtn = document.getElementById('closeDetailBtn');

closeDetailBtn.addEventListener('click', () => {
    detailModal.classList.remove('active');
});

export async function openStudentDetail(uuid) {
    try {
        const student = await getStudent(uuid);
        // Fetch attendance and payments in parallel
        const [attendance, payments] = await Promise.all([
            getAttendance(uuid).catch(() => []),
            getPayments(uuid).catch(() => [])
        ]);

        let invoiceDisplay = '';
        if (student.invoice_reference) {
            invoiceDisplay = `Next Invoice: see ${escapeHtml(student.invoice_reference)}`;
        } else {
            const amount = (student.next_invoice != null ? student.next_invoice : 0).toLocaleString();
            invoiceDisplay = `Next Invoice: ${amount} K`;
        }

        let html = `
            <h3>${escapeHtml(student.name)}</h3>
            <p><strong>Age Group:</strong> ${student.age_group || '—'} | <strong>Country:</strong> ${student.country || '—'} | <strong>TZ:</strong> ${student.timezone || '—'}</p>
            <p><strong>Phones:</strong> ${(student.phones || []).join(', ') || '—'}</p>
            <p><strong>Emails:</strong> ${(student.emails || []).join(', ') || '—'}</p>
            <p><strong>Telegram:</strong> ${student.telegram || '—'}</p>
            <p><strong>${invoiceDisplay}</strong></p>
            <p><strong>Meetings:</strong> ${student.meeting_times_summary || 'None'}</p>
            <h4>Attendance</h4>
            <div>${attendance.length ? attendance.map(a => `${a.date} - ${a.status}`).join('<br>') : 'No records'}</div>
            <h4>Payments</h4>
            <div>${payments.length ? payments.map(p => `${p.date}: ${p.amount} K`).join('<br>') : 'No payments'}</div>
            <h4>Linked Students</h4>
            <div>${(student.linked_students || []).map(l => `${l.name} (${l.relationship})`).join('<br>') || 'None'}</div>
            <hr>
            <button id="editStudentBtn" class="btn btn-primary">Edit</button>
            <button id="deleteStudentBtn" class="btn btn-danger" style="margin-left:10px;">Delete Student</button>
            <div id="deletePasswordArea" style="display:none; margin-top:10px;">
                <input type="password" id="deletePasswordInput" placeholder="Enter master password" style="width:200px;">
                <button id="confirmDeleteBtn" class="btn btn-danger" style="margin-left:5px;">Confirm Delete</button>
                <button id="cancelDeleteBtn" class="btn btn-secondary" style="margin-left:5px;">Cancel</button>
            </div>
        `;
        detailContent.innerHTML = html;
        detailModal.classList.add('active');

        document.getElementById('editStudentBtn').addEventListener('click', () => {
            detailModal.classList.remove('active');
            openEditForm(student);
        });

        document.getElementById('deleteStudentBtn').addEventListener('click', () => {
            document.getElementById('deletePasswordArea').style.display = 'block';
            document.getElementById('deletePasswordInput').focus();
        });

        document.getElementById('cancelDeleteBtn').addEventListener('click', () => {
            document.getElementById('deletePasswordArea').style.display = 'none';
            document.getElementById('deletePasswordInput').value = '';
        });

        document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
            const password = document.getElementById('deletePasswordInput').value;
            if (!password) {
                alert('Password required');
                return;
            }
            try {
                await apiCall('DELETE', `/students/${uuid}`, { password });
                detailModal.classList.remove('active');
                if (window._onStudentChanged) window._onStudentChanged();
            } catch (e) {
                alert('Deletion failed: ' + e.message);
            }
        });

    } catch (e) {
        alert('Failed to load student details');
    }
}