export default {
    greeting: null,
    layout: '1fr 1fr',
    eyeMenu: [
        { label: 'Staff Management', action: '/launch/staff/staff.html' },
        { label: 'Financials', action: '#' },
        { label: 'Payroll & Expenses', action: '#' },
        { label: 'Student View', action: '#' },
        { label: 'Meetings View', action: '#' },
        { label: 'Analytics', action: '#' },
        { label: 'Profile', action: '/launch/staff/staff.html?mode=self' }
    ],
    widgets: [
        { id: 'upcoming-dates', type: 'upcomingDates', position: 'left', title: 'Upcoming Dates' },
        { id: 'absences', type: 'studentHighlights', position: 'left', title: 'Today’s Absences' }, // placeholder reusing studentHighlights
        { id: 'financial-overview', type: 'financialOverview', position: 'right', title: 'Financial Overview' }
    ],
    bottomTabs: [
        { id: 'inbox', label: 'Inbox', component: 'inbox' },
        { id: 'payroll', label: 'Payroll & Expenses', component: 'payrollExpenses' }
    ]
};