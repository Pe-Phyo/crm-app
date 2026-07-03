import { getActions, addAction, updateAction, deleteAction } from '../api.js';
import { escapeHtml } from '../utils/helpers.js';

const actionsContainer = document.getElementById('actionItems');

/**
 * Render action items and the "add new" input.
 * @param {Array} actions - current list of action objects
 * @param {Function} onToggle - called with (id, newDoneState)
 * @param {Function} onDelete - called with (id)
 * @param {Function} onAdd    - called with (text)
 */
export function renderActions(actions, onToggle, onDelete, onAdd) {
    if (!actionsContainer) return;

    let html = '<div style="display:flex;gap:5px;margin-bottom:10px;">';
    html += '<input type="text" id="newActionInput" placeholder="New action..." style="flex:1;padding:5px;border-radius:4px;border:1px solid #475569;background:#0f172a;color:#e2e8f0;">';
    html += '<button id="addActionBtn" class="btn btn-primary" style="padding:5px 10px;">+</button>';
    html += '</div>';

    if (!actions.length) {
        html += '<div class="placeholder-box">No actions</div>';
    } else {
        html += actions.map(a => `
            <div class="action-item ${a.done ? 'done' : ''}" data-id="${a.id}">
                <span class="action-text">${escapeHtml(a.text)}</span>
                <div class="action-btns">
                    <button class="btn-toggle" data-id="${a.id}">${a.done ? '✅' : '⬜'}</button>
                    <button class="btn-delete" data-id="${a.id}">🗑️</button>
                </div>
            </div>
        `).join('');
    }

    actionsContainer.innerHTML = html;

    // Add new action button
    const addBtn = document.getElementById('addActionBtn');
    const newInput = document.getElementById('newActionInput');
    if (addBtn && newInput) {
        addBtn.addEventListener('click', () => {
            const text = newInput.value.trim();
            if (text && onAdd) {
                onAdd(text);
                newInput.value = '';
            }
        });
    }

    // Toggle buttons
    actionsContainer.querySelectorAll('.btn-toggle').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            const item = actions.find(a => a.id === id);
            if (item && onToggle) {
                onToggle(id, !item.done);
            }
        });
    });

    // Delete buttons
    actionsContainer.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            if (onDelete) onDelete(id);
        });
    });
}