import { fetchChartData } from '../api.js';

export async function renderChart(container, widgetDef) {
    // In future, use Chart.js; for now, simple placeholder
    container.innerHTML = '<div class="chart-placeholder" style="height:200px; background:var(--bg); display:flex; align-items:center; justify-content:center; color:var(--muted);">📈 Chart loading...</div>';
    try {
        const data = await fetchChartData(widgetDef.chartId);
        // data would be { labels: [], values: [] }
        container.innerHTML = `<div class="chart-placeholder">Chart: ${widgetDef.chartId} (data loaded: ${data.values ? data.values.length : 0} points)</div>`;
    } catch (e) {
        container.innerHTML = `<div class="chart-placeholder">Chart unavailable</div>`;
    }
}