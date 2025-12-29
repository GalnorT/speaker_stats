export class SpeakerPointsChart {
    constructor(containerId, debater) {
        this.chart = null;
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
        this.container.appendChild(this.canvasElement);
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
        const sortedDebates = [...this.currentDebater.debates].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
        const dates = sortedDebates.map(d => d.date);
        const points = sortedDebates.map(d => d.speaker_points);
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                        label: 'Speaker Points',
                        data: points,
                        borderColor: 'rgba(59, 130, 246, 1)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        tension: 0.4, // Smooth curves
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function (context) {
                                const date = context[0].label;
                                return date;
                            },
                            label: function (context) {
                                return `Speaker Points: ${context.parsed.y.toFixed(1)}`;
                            }
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x'
                        },
                        pan: {
                            enabled: true,
                            mode: 'x'
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'dd.MM.yyyy'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        min: 50,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Speaker Points'
                        }
                    }
                }
            }
        });
    }
    update(debater) {
        this.currentDebater = debater;
        if (!this.chart) {
            this.render();
        }
        const sortedDebates = [...debater.debates].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
        const dates = sortedDebates.map(d => d.date);
        const points = sortedDebates.map(d => d.speaker_points);
        this.chart.data.labels = dates;
        this.chart.data.datasets[0].data = points;
        this.chart.update();
    }
}
