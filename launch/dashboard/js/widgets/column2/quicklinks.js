export async function render(container, widgetDef) {
    container.innerHTML = `
        <ul style="list-style:none; padding:0;">
            <li><a href="/launch/students/students.html">My Students</a></li>
            <li><a href="/launch/meetings/meetings.html">My Meetings</a></li>
            <li><a href="#">Payout Info (coming soon)</a></li>
        </ul>
    `;
}