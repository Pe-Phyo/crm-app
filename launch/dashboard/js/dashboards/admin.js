export default {
    greeting: 'Admin Dashboard',
    layout: 'split-65-35',  // right 65%, left 35%
    // Role-switching menu for admin
    eyeMenu: [
        { label: 'teacher', action: 'switch-role:teacher' },
        { label: 'front office', action: 'switch-role:front_office' },
        { label: 'back office', action: 'switch-role:back_office' },
        { label: 'bot', action: 'switch-role:bot' },
        { label: 'dev', action: 'switch-role:dev' },
        { label: 'admin (own)', action: 'switch-role:admin' },
    ],
    widgets: [
        {
            id: 'upcoming-dates',
            type: 'upcomingDates',
            position: 'left',
            title: 'Upcoming Dates'
        },
        {
            id: 'student-highlights',
            type: 'studentHighlights',
            position: 'left',
            title: 'Student Highlights'
        },
        { id: 'analytics', type: 'analytics', position: 'right', chartId: 'monthly-sessions-income' },
    ],
    bottomTabs: [
        { id: 'inbox', label: 'Inbox', component: 'inbox' },
        { id: 'build-status', label: 'System', component: 'buildStatus' }  // <-- fixed name
    ]
};