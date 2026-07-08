export default {
    greeting: 'System & Dev Dashboard',
    layout: '1fr 1fr',
    eyeMenu: [
        { label: 'Analytics', action: '#' },
        { label: 'Financials', action: '#' },
        { label: 'Profile', action: '#' },
    ],
    widgets: [
        { id: 'build-status', type: 'buildStatus', position: 'left', title: 'Build Status' },
        { id: 'performance-monitor', type: 'performanceMonitor', position: 'right', title: 'Performance Monitor' }
    ],
    bottomTabs: [
        { id: 'all-logs', label: 'All Logs', component: 'allLogs' },
        { id: 'errors', label: 'Errors', component: 'errorsTab' },
        { id: 'ai-agents', label: 'AI Agents', component: 'aiAgents' },
        { id: 'api-console', label: 'API Console', component: 'apiConsole' }
    ]
};