export async function renderStudentHighlights(container, widgetDef) {
    const active = 12; // replace with API call later
    const loyalty = [
        { name: 'Maria', duration: '2y 3m', anniversary: 'Apr 12' },
        { name: 'Thiri', duration: '1y 8m', anniversary: 'Nov 5' },
        { name: 'Aung', duration: '1y 1m', anniversary: 'Jun 22' }
    ];
    container.innerHTML = `
        <div class="highlight-number">${active}</div>
        <div style="color:var(--muted);">Active Students</div>
        <div style="margin-top:0.5rem;"><strong>Top 3 Loyalty:</strong></div>
        <ol style="font-size:0.8rem;">
            ${loyalty.map(s => `<li>${s.name} – ${s.duration} (${s.anniversary})</li>`).join('')}
        </ol>
    `;
}