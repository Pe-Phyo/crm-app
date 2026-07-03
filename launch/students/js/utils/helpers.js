export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Sets up dynamic add/remove behaviour for multi‑input containers
 * @param {string} containerId  - The ID of the container element
 * @param {string} inputClass   - CSS class for the <input> elements
 */
export function setupMultiInput(containerId, inputClass) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.addEventListener('click', (e) => {
        if (e.target.classList.contains('add-multi-btn')) {
            const row = document.createElement('div');
            row.className = 'multi-input-row';

            const input = document.createElement('input');
            input.type = inputClass.includes('phone') ? 'text' : 'email';
            input.className = inputClass;

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-multi-btn';
            removeBtn.textContent = '-';
            removeBtn.addEventListener('click', () => row.remove());

            row.appendChild(input);
            row.appendChild(removeBtn);
            container.appendChild(row);
        }
    });
}