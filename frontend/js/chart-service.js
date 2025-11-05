class ChartService {
    constructor() {
        this.charts = new Map();
    }

    initMarketChart() {
        const ctx = document.getElementById('marketChart');
        if (!ctx) return;

        this.charts.set('market', new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'S&P 500',
                    data: [],
                    borderColor: '#1E3A8A',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        }));
    }

    updateMarketChart(data) {
        const chart = this.charts.get('market');
        if (chart && data && data.dates && data.values) {
            chart.data.labels = this.formatDates(data.dates);
            chart.data.datasets[0].data = data.values;
            chart.update();
        }
    }

    initPortfolioChart() {
        const ctx = document.getElementById('portfolioChart');
        if (!ctx) return;

        this.charts.set('portfolio', new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: ['#3B82F6', '#10B981', '#6B7280', '#F59E0B', '#EF4444']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        }));
    }

    initStockDetailChart() {
        const ctx = document.getElementById('stockDetailChart');
        if (!ctx) return;

        this.charts.set('stockDetail', new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Price',
                    data: [],
                    borderColor: '#1E3A8A',
                    backgroundColor: 'rgba(59, 130, 246, 0.05)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        }));
    }

    updateStockDetailChart(data) {
        const chart = this.charts.get('stockDetail');
        if (chart && data) {
            chart.data.labels = this.formatDates(data.dates);
            chart.data.datasets[0].data = data.values;
            chart.update();
        }
    }

    formatDates(dates) {
        if (!dates || !Array.isArray(dates)) return [];
        return dates.map(date => {
            const d = new Date(date);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
    }
}

const chartService = new ChartService();