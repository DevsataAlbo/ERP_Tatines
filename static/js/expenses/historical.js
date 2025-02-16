document.addEventListener('DOMContentLoaded', function() {
    const chartConfig = {
        type: 'pie',
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 20
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value * 100) / total);
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };

    // Los datos se pasan desde el backend como variables globales
    window.yearsData.forEach(yearData => {
        new Chart(document.getElementById(`chart-${yearData.year}`), {
            ...chartConfig,
            data: {
                labels: yearData.chart_data.labels,
                datasets: [{
                    data: yearData.chart_data.data,
                    backgroundColor: yearData.chart_data.colors
                }]
            }
        });
    });
});