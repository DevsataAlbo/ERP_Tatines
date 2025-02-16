document.addEventListener('DOMContentLoaded', function() {
    const { monthlyData } = window.comparisonData;

    // Gráfico de comparación mensual
    new Chart(document.getElementById('monthlyComparisonChart'), {
        type: 'bar',
        data: {
            labels: monthlyData.labels,
            datasets: [{
                label: 'Año Actual',
                data: monthlyData.currentYear,
                backgroundColor: 'rgb(59, 130, 246)',
                borderColor: 'rgb(29, 78, 216)',
                borderWidth: 1
            }, {
                label: 'Año Anterior',
                data: monthlyData.previousYear,
                backgroundColor: 'rgb(209, 213, 219)',
                borderColor: 'rgb(107, 114, 128)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += new Intl.NumberFormat('es-CL', {
                                style: 'currency',
                                currency: 'CLP'
                            }).format(context.raw);
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => `$ ${new Intl.NumberFormat().format(value)}`
                    }
                }
            }
        }
    });
});