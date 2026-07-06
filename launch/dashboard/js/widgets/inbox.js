import { apiCall } from '../api.js';

export async function render(container) {
    // Build widget header with controls
    container.innerHTML = `
        <div class="widget-header">
            <span class="widget-title">Action Items</span>
            <div class="widget-controls">
                <button class="btn btn-sm btn-secondary" id="inbox-filter-all">All</button>
                <button class="btn btn-sm btn-secondary" id="inbox-filter-open">Open</button>
                <button class="btn btn-sm btn-secondary" id="inbox-filter-done">Done</button>
                <button class="btn btn-sm btn-primary" id="inbox-new-btn">+ New</button>
            </div>
        </div>
        <div id="inbox-list"></div>
        <div id="inbox-new-row" style="display:none; margin-top:5px;">
            <input type="text" id="inbox-new-input" placeholder="New action..." style="width:70%;">
            <button class="btn btn-sm btn-success" id="inbox-new-save">Save</button>
            <button class="btn btn-sm btn-secondary" id="inbox-new-cancel">Cancel</button>
        </div>
    `;

    const listContainer = document.getElementById('inbox-list');
    let allActions = [];
    let currentFilter = 'all';   // all | open | done

    // Load data
    try {
        allActions = await apiCall('GET', '/api/actions');
    } catch (e) {
        listContainer.innerHTML = '<p class="empty-state">Could not load actions.</p>';
        return;
    }

    // Filter function
    function filterActions() {
        if (currentFilter === 'open') return allActions.filter(a => !a.done);
        if (currentFilter === 'done') return allActions.filter(a => a.done);
        return allActions;
    }

    // Render the list (or empty state)
    function renderList() {
        const filtered = filterActions();
        if (filtered.length === 0) {
            listContainer.innerHTML = '<p class="empty-state">This queue is empty.</p>';
            return;
        }
        listContainer.innerHTML = filtered.map(a => `
            <div class="inbox-item ${a.done ? 'done' : ''}">
                <span class="inbox-text">${escapeHtml(a.text)}</span>
                <span class="inbox-status">${a.done ? 'Done' : 'Open'}</span>
            </div>
        `).join('');
    }

    // Initial render
    renderList();

    // ---- Event Listeners ----

    // Filter buttons
    document.getElementById('inbox-filter-all').addEventListener('click', () => {
        currentFilter = 'all';
        renderList();
    });
    document.getElementById('inbox-filter-open').addEventListener('click', () => {
        currentFilter = 'open';
        renderList();
    });
    document.getElementById('inbox-filter-done').addEventListener('click', () => {
        currentFilter = 'done';
        renderList();
    });

    // New action button
    document.getElementById('inbox-new-btn').addEventListener('click', () => {
        document.getElementById('inbox-new-row').style.display = 'block';
        document.getElementById('inbox-new-input').focus();
    });

    // Save new action
    document.getElementById('inbox-new-save').addEventListener('click', async () => {
        const input = document.getElementById('inbox-new-input');
        const text = input.value.trim();
        if (!text) return;
        try {
            await apiCall('POST', '/api/actions', { text });
            allActions = await apiCall('GET', '/api/actions');
            input.value = '';
            document.getElementById('inbox-new-row').style.display = 'none';
            renderList();
        } catch (e) {
            alert('Failed to add action');
        }
    });

    // Cancel new action
    document.getElementById('inbox-new-cancel').addEventListener('click', () => {
        document.getElementById('inbox-new-row').style.display = 'none';
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
export { render as renderInbox };