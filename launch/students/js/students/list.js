import { escapeHtml } from '../utils/helpers.js';

const studentListContainer = document.getElementById('studentList');
const searchInput = document.getElementById('searchInput');
const statusFilter = document.getElementById('statusFilter');
const paymentFilter = document.getElementById('paymentFilter');
const rateMinInput = document.getElementById('rateMin');
const rateMaxInput = document.getElementById('rateMax');
const applyFiltersBtn = document.getElementById('applyFiltersBtn');

let currentPage = 1;
const ITEMS_PER_PAGE = 5;

function currentTimeInTz(tz) {
    // If no timezone or it's not a string, show placeholder
    if (!tz || typeof tz !== 'string') return '--:--';

    // Try to match "GMT+6.5", "GMT-5", "GMT+5:30", "GMT+3.75", etc.
    let match = tz.match(/^GMT([+-])(\d+)(?::(\d+))?(?:\.(\d+))?$/);
    if (!match) return '--:--';

    let sign = match[1] === '+' ? 1 : -1;
    let hours = parseInt(match[2], 10);
    let minutes = 0;
    if (match[3]) {
        minutes = parseInt(match[3], 10);       // e.g. "GMT+5:30"
    } else if (match[4]) {
        minutes = Math.round(parseFloat('0.' + match[4]) * 60); // e.g. "GMT+6.5"
    }
    let totalOffsetMinutes = sign * (hours * 60 + minutes);

    let now = new Date();
    let utc = now.getTime() + now.getTimezoneOffset() * 60000;
    let localTime = new Date(utc + totalOffsetMinutes * 60000);

    return localTime.toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', hour12: true
    });
}

export function renderStudentList(students, onStudentClick) {
    if (!studentListContainer) return;

    if (!students.length) {
        studentListContainer.innerHTML = '<div class="placeholder-box">No students yet.</div>';
        return;
    }

    const totalPages = Math.ceil(students.length / ITEMS_PER_PAGE);
    if (currentPage > totalPages) currentPage = totalPages;
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const pageStudents = students.slice(start, start + ITEMS_PER_PAGE);

    const cardsHtml = pageStudents.map(s => {
        const lastPayment = s.last_payment_date || '—';
        const attendance = s.attendance_percentage != null ? s.attendance_percentage.toFixed(0) + '%' : '—';
        const meetingSummary = s.meeting_times_summary || 'No meetings';
        const meetingList = meetingSummary.split(',').map(m => m.trim()).join(' • ');
        const flag = s.flag || '';
        const localTime = currentTimeInTz(s.timezone || 'UTC');

        // Next Invoice display
        let invoiceDisplay = '';
        if (s.invoice_reference) {
            invoiceDisplay = `Next Invoice: see ${s.invoice_reference}`;
        } else {
            const amount = (s.next_invoice != null ? s.next_invoice : 0).toLocaleString();
            invoiceDisplay = `Next Invoice: ${amount} K`;
        }

        return `
        <div class="student-card" data-uuid="${s.uuid}">
            <div class="student-card-line1">
                <span class="student-name">${flag} ${escapeHtml(s.name)}</span>
                <span class="student-time">${localTime}</span>
                <span class="status-badge ${s.status}">${s.status}</span>
            </div>
            <div class="student-card-line2">
                <span>${invoiceDisplay}</span>
                <span>Last payment: ${lastPayment}</span>
                <span>Attendance: ${attendance}</span>
            </div>
            <div class="student-card-line3">
                <span>${meetingList}</span>
            </div>
        </div>`;
    }).join('');

    let paginationHtml = '';
    if (totalPages > 1) {
        paginationHtml = '<div class="pagination">';
        for (let i = 1; i <= totalPages; i++) {
            paginationHtml += `<button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
        paginationHtml += '</div>';
    }

    studentListContainer.innerHTML = cardsHtml + paginationHtml;

    studentListContainer.querySelectorAll('.student-card').forEach(card => {
        card.addEventListener('click', () => {
            const uuid = card.dataset.uuid;
            if (onStudentClick) onStudentClick(uuid);
        });
    });

    studentListContainer.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentPage = parseInt(btn.dataset.page);
            renderStudentList(students, onStudentClick);
        });
    });
}

export function getActiveFilters() {
    return {
        search: searchInput?.value.trim() || '',
        status: statusFilter?.value || '',
        payment: paymentFilter?.value || '',
        rateMin: parseInt(rateMinInput?.value) || null,
        rateMax: parseInt(rateMaxInput?.value) || null
    };
}

export function filterStudents(students) {
    const filters = getActiveFilters();
    return students.filter(s => {
        if (filters.search) {
            if (!s.name.toLowerCase().includes(filters.search.toLowerCase())) return false;
        }
        if (filters.status && s.status !== filters.status) return false;
        if (filters.payment) {
            const lastPayment = s.last_payment_date;
            if (filters.payment === 'paid') {
                if (!lastPayment || new Date(lastPayment) < new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)) return false;
            } else if (filters.payment === 'overdue') {
                if (lastPayment && new Date(lastPayment) >= new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)) return false;
            }
        }
        // Rate filter now uses next_invoice
        const invoiceAmount = s.next_invoice || 0;
        if (filters.rateMin !== null && invoiceAmount < filters.rateMin) return false;
        if (filters.rateMax !== null && invoiceAmount > filters.rateMax) return false;
        return true;
    });
}

export function bindFilterEvents(onFilterChange) {
    if (!applyFiltersBtn) return;
    applyFiltersBtn.addEventListener('click', () => {
        currentPage = 1;
        if (onFilterChange) onFilterChange();
    });
    searchInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            currentPage = 1;
            if (onFilterChange) onFilterChange();
        }
    });
}