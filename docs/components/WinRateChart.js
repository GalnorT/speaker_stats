export class WinRateChart {
    constructor(containerId, debater) {
        this.chart = null; // Chart.js instance
        this.canvasElement = null;
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container with id "${containerId}" not found`);
        }
        this.container = container;
        this.currentDebater = debater;
        this.render();
    }
    render() {
        const h2 = this.container.querySelector('h2');
        this.container.innerHTML = '';
        if (h2) {
            this.container.appendChild(h2);
        }
        this.canvasElement = document.createElement('canvas');
        this.canvasElement.className = 'chart-canvas';
        const details = document.createElement('div');
        details.className = 'win-rate-details';
        details.innerHTML = `
      <h2>Win Rate</h2>
      <p><strong>Overall:</strong> ${(this.currentDebater.side_win_rates.total * 100).toFixed(1)}%</p>
      <p><strong>Affirmative:</strong> ${(this.currentDebater.side_win_rates.aff * 100).toFixed(1)}%</p>
      <p><strong>Negative:</strong> ${(this.currentDebater.side_win_rates.neg * 100).toFixed(1)}%</p>
    `;
        this.container.appendChild(this.canvasElement);
        this.container.appendChild(details);
        this.initializeChart();
    }
    initializeChart() {
        if (!this.canvasElement)
            return;
        // @ts-ignore - Chart.js is loaded via CDN
        const Chart = window.Chart;
        if (!Chart) {
            console.error('Chart.js not loaded');
            return;
        }
        const ctx = this.canvasElement.getContext('2d');
        if (!ctx)
            return;
        const winRate = this.currentDebater.side_win_rates.total;
        const lossRate = 1 - winRate;
        this.chart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Wins', 'Losses'],
                datasets: [{
                        data: [winRate * 100, lossRate * 100],
                        backgroundColor: [
                            'rgba(34, 197, 94, 0.8)', // Green for wins
                            'rgba(239, 68, 68, 0.8)' // Red for losses
                        ],
                        borderColor: [
                            'rgba(34, 197, 94, 1)',
                            'rgba(239, 68, 68, 1)'
                        ],
                        borderWidth: 2
                    }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: ${value.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
    }
    update(debater) {
        this.currentDebater = debater;
        if (this.chart) {
            const winRate = debater.side_win_rates.total;
            const lossRate = 1 - winRate;
            this.chart.data.datasets[0].data = [winRate * 100, lossRate * 100];
            this.chart.update();
            const details = this.container.querySelector('.win-rate-details');
            if (details) {
                details.innerHTML = `
          <h2>Win Rate</h2>
          <p><strong>Overall:</strong> ${(debater.side_win_rates.total * 100).toFixed(1)}%</p>
          <p><strong>Affirmative:</strong> ${(debater.side_win_rates.aff * 100).toFixed(1)}%</p>
          <p><strong>Negative:</strong> ${(debater.side_win_rates.neg * 100).toFixed(1)}%</p>
        `;
            }
        }
        else {
            // If chart doesn't exist, re-render
            this.render();
        }
    }
}
