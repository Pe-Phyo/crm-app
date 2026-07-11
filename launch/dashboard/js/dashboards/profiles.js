export default {
    greeting: null, // dynamically set
    layout: '1fr 1fr',
    eyeButtonLabel: 'Update',
    eyeAction: 'open-profile-modal',   // directly triggers the modal
    eyeMenu: [],                        // no dropdown menu
    widgets: [
        { id: 'profile-summary', type: 'profileSummary', position: 'left', title: 'Profile' },
        { id: 'profile-upcoming', type: 'profileUpcoming', position: 'left', title: 'Upcoming Dates' },
        { id: 'profile-wellness', type: 'profileWellness', position: 'right', title: 'Wellness' },
        { id: 'profile-activity', type: 'profileActivity', position: 'right', title: 'Recent Activity' },
        { id: 'quick-links', type: 'quickLinks', position: 'right', title: 'Quick Links' }
    ],
    bottomTabs: [
        { id: 'inbox', label: 'HR Inbox', component: 'inbox' },
        { id: 'timeoff', label: 'Time Off', component: 'timeOff' }
    ]
};