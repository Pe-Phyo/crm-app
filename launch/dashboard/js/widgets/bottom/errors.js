export async function render(container) {
    container.innerHTML = `<p style="color:var(--muted);">Error log – to be built.</p>`;
}
export { render as renderErrors };