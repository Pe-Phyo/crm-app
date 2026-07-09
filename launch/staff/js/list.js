import { escapeHtml } from '../../students/js/utils/helpers.js';  // reuse helper

let currentStaff = [];
let onDetailClick = null;

export function renderStaffList(staff, onDetail) {
    const container = document.getElementById('staffList');
    if (!container) return;
    currentStaff = staff;
    onDetailClick = onDetail;

    if (!staff.length) {
        container.innerHTML = '<div class="placeholder-box">No staff members.</div>';
        return;
    }

    container.innerHTML = staff.map(s => `
        <div class="staff-card" data-uuid="${s.uuid}">
            <div class="staff-card-header">
                <strong>${escapeHtml(s.display_name || s.full_name || s.username)}</strong>
                <span class="status-badge ${s.is_active ? 'active' : 'inactive'}">${s.is_active ? 'Active' : 'Inactive'}</span>
            </div>
            <div class="staff-card-body">
                <span>👤 ${s.role}</span>
                <span>📧 ${s.email || '—'}</span>
                <span>📞 ${s.phone || '—'}</span>
                <span>🕒 ${s.timezone || '—'}</span>
            </div>
        </div>
    `).join('');

    container.querySelectorAll('.staff-card').forEach(card => {
        card.addEventListener('click', () => {
            const uuid = card.dataset.uuid;
            if (onDetailClick) onDetailClick(uuid);
        });
    });
}

export function bindFilterEvents(staff, renderFn, onDetail) {
    const searchInput = document.getElementById('searchInput');
    const roleFilter = document.getElementById('roleFilter');
    const applyBtn = document.getElementById('applyFiltersBtn');

    function filter() {
        const search = searchInput.value.toLowerCase();
        const role = roleFilter.value;
        let filtered = staff;
        if (search) {
            filtered = filtered.filter(s =>
                (s.display_name || s.full_name || s.username).toLowerCase().includes(search)
            );
        }
        if (role) {
            filtered = filtered.filter(s => s.role === role);
        }
        renderFn(filtered, onDetail);
    }

    applyBtn.addEventListener('click', filter);
    searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') filter(); });
}