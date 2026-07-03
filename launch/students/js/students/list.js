import { getStudents } from '../api.js';
import { escapeHtml } from '../utils/helpers.js';

const studentListContainer = document.getElementById('studentList');
const searchInput = document.getElementById('searchInput');
const statusFilter = document.getElementById('statusFilter');
const paymentFilter = document.getElementById('paymentFilter');
const rateMinInput = document.getElementById('rateMin');
const rateMaxInput = document.getElementById('rateMax');
const applyFiltersBtn = document.getElementById('applyFiltersBtn');

/**
 * Render student cards. Calls onStudentClick(uuid) when a card is clicked.
 */
export function renderStudentList(students, onStudentClick) {
    if (!studentListContainer) return;

    if (!students.length) {
        studentListContainer.innerHTML = '<div class="placeholder-box">No students yet.</div>';
        return;
    }

    studentListContainer.innerHTML = students.map(s => {
        const lastPayment = s.last_payment_date || 'Never';
        const att = s.attendance_percentage.toFixed(0);
        return `
        <div class="student-card" data-uuid="${s.uuid}">
            <div class="student-card-header">
                <strong>${escapeHtml(s.name)}</strong>
                <span class="status-badge ${s.status}">${s.status}</span>
            </div>
            <div class="student-card-body">
                <span>📍 ${escapeHtml(s.location) || '—'}</span>
                <span>💰 ${s.rate.toLocaleString()} K</span>
                <span>📅 Last payment: ${lastPayment}</span>
                <span>📊 Attendance: ${att}%</span>
                <span>🕒 ${s.meeting_times_summary || 'No meetings'}</span>
            </div>
        </div>`;
    }).join('');

    // Attach click handlers
    studentListContainer.querySelectorAll('.student-card').forEach(card => {
        card.addEventListener('click', () => {
            const uuid = card.dataset.uuid;
            if (onStudentClick) onStudentClick(uuid);
        });
    });
}

/**
 * Reads current filter values and returns an object for server-side filtering.
 * To keep it simple now, returns filters for client-side use.
 * Later we can pass these to the backend API.
 */
export function getActiveFilters() {
    return {
        search: searchInput?.value.trim() || '',
        status: statusFilter?.value || '',
        payment: paymentFilter?.value || '',
        rateMin: parseInt(rateMinInput?.value) || null,
        rateMax: parseInt(rateMaxInput?.value) || null
    };
}

/**
 * Applies client-side filtering to an array of students.
 * (Server-side filtering can be added later.)
 */
export function filterStudents(students) {
    const filters = getActiveFilters();
    return students.filter(s => {
        if (filters.search) {
            const nameMatch = s.name.toLowerCase().includes(filters.search.toLowerCase());
            if (!nameMatch) return false;
        }
        if (filters.status && s.status !== filters.status) return false;
        if (filters.payment) {
            const lastPayment = s.last_payment_date;
            if (filters.payment === 'paid') {
                // Simple check: paid this month (payment date within last 30 days)
                if (!lastPayment || new Date(lastPayment) < new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)) return false;
            } else if (filters.payment === 'overdue') {
                if (lastPayment && new Date(lastPayment) >= new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)) return false;
            }
        }
        if (filters.rateMin !== null && s.rate < filters.rateMin) return false;
        if (filters.rateMax !== null && s.rate > filters.rateMax) return false;
        return true;
    });
}

/**
 * Binds the filter button and Enter key to a callback that refreshes the list.
 */
export function bindFilterEvents(onFilterChange) {
    if (!applyFiltersBtn) return;

    applyFiltersBtn.addEventListener('click', () => {
        if (onFilterChange) onFilterChange();
    });

    // Optional: trigger on Enter in search field
    searchInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && onFilterChange) onFilterChange();
    });
}