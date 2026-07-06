export default {
    greeting: 'Admin Dashboard',
    layout: 'split-65-35',  // right 65%, left 35%
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
        {
            id: 'analytics',
            type: 'chart',
            position: 'right',
            defaultChart: 'Monthly Sessions vs Income',
            chartId: 'monthly-sessions-income'
        }
    ],
    bottomTabs: [
        { id: 'inbox', label: 'Inbox', component: 'inbox' },
        { id: 'build-status', label: 'System', component: 'buildStatus' }  // <-- fixed name
    ]
};