export default {
    greeting: 'Bot Management',
    layout: '1fr 1fr',
    eyeMenu: [
        { label: 'Bot Settings', action: '#' }
    ],
    widgets: [
        { id: 'bot-status', type: 'botStatus', position: 'left', title: 'Bot Status' },
        { id: 'live-activity', type: 'liveActivity', position: 'right', title: 'Live Activity' }
    ],
    bottomTabs: [
        { id: 'activity-log', label: 'Activity Log', component: 'activityLog' },
        { id: 'templates', label: 'Templates', component: 'templates' },
        { id: 'errors', label: 'Errors', component: 'errorsTab' }
    ]
};