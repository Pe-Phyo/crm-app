export default {
    greeting: null, // will be set dynamically by coordinator
    layout: '1fr 1fr',
    eyeMenu: [
        { label: 'Analytics', action: '#' },
        { label: 'Financials', action: '#' },
        { label: 'Profile', action: '/launch/staff/staff.html?mode=self' }
    ],
    widgets: [
        { id: 'upcoming-dates', type: 'upcomingDates', position: 'left', title: 'Upcoming Dates' },
        { id: 'attendance', type: 'attendance', position: 'left', title: 'Attendance' },
        { id: 'meetings', type: 'meetings', position: 'right', title: 'Meetings' }
    ],
    bottomTabs: [
        { id: 'my-actions', label: 'My Action Items', component: 'inbox' }
    ]
};