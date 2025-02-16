document.addEventListener('DOMContentLoaded', function() {
    const chartEl = document.getElementById('salesChart');
    if (chartEl) {
        const chartData = JSON.parse(document.getElementById('sales-chart-data').textContent);
        new Chart(chartEl, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Ventas',
                    data: chartData.data,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return '$ ' + new Intl.NumberFormat('es-CL', {
                                    maximumFractionDigits: 0
                                }).format(context.raw);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => '$ ' + new Intl.NumberFormat('es-CL', {
                                maximumFractionDigits: 0
                            }).format(value)
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            callback: function(value, index) {
                                return 'Día ' + this.getLabelForValue(value);
                            }
                        }
                    }
                }
            }
        });
    }
});