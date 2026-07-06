let registry = {};

export function setWidgetRegistry(widgets) {
    registry = { ...registry, ...widgets };
}

export async function renderWidget(container, widgetDef) {
    // Create widget header
    const header = document.createElement('div');
    header.className = 'widget-header';
    
    const title = document.createElement('div');
    title.className = 'widget-title';
    // If it's a chart, make title editable for search
    if (widgetDef.type === 'chart') {
        const input = document.createElement('input');
        input.type = 'text';
        input.value = widgetDef.defaultChart || 'Monthly Sessions vs Income';
        input.addEventListener('change', (e) => {
            // Re-render chart with new chart ID
            widgetDef.chartId = e.target.value;
            renderWidgetBody(container.querySelector('.widget-body'), widgetDef);
        });
        title.appendChild(input);
    } else {
        title.textContent = widgetDef.title || '';
    }
    header.appendChild(title);
    
    // Toolbar (filters, sort) – can be added per widget type
    // For now, simple placeholder actions
    
    container.appendChild(header);
    
    const body = document.createElement('div');
    body.className = 'widget-body';
    container.appendChild(body);
    
    await renderWidgetBody(body, widgetDef);
}

async function renderWidgetBody(bodyContainer, widgetDef) {
    const renderFn = registry[widgetDef.type];
    if (renderFn) {
        await renderFn(bodyContainer, widgetDef);
    } else {
        bodyContainer.innerHTML = `<p style="color:var(--muted);">Widget type "${widgetDef.type}" not found.</p>`;
    }
}