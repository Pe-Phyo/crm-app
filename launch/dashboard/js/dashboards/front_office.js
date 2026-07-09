export default {
    greeting: null,
    layout: '1fr 1fr',
    eyeMenu: [
        { label: 'Student View', action: '/launch/students/students.html' },
        { label: 'Meetings View', action: '/launch/meetings/meetings.html' },
        { label: 'Payment Screen', action: '#' },
        { label: 'Financials', action: '#' },
        { label: 'Profile', action: '/launch/staff/staff.html?mode=self' }
    ],
    widgets: [
        { id: 'payments-summary', type: 'paymentsSummary', position: 'left', title: 'Payments Summary' },
        { id: 'messages', type: 'messages', position: 'right', title: 'Messages' }
    ],
    bottomTabs: [
        { id: 'reception', label: 'Today’s Reception', component: 'receptionCheckin' }
    ]
};