document.addEventListener('DOMContentLoaded', function() {
    const { monthlyData, paymentMethods } = window.trendsData;

    // Ventas vs Gastos
    new Chart(document.getElementById('salesVsExpensesChart'), {
        type: 'line',
        data: {
            labels: monthlyData.map(item => item.month),
            datasets: [{
                label: 'Ventas',
                data: monthlyData.map(item => item.sales),
                borderColor: 'rgb(59, 130, 246)',
                tension: 0.1
            }, {
                label: 'Gastos',
                data: monthlyData.map(item => item.expenses),
                borderColor: 'rgb(239, 68, 68)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top'
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

    // Rentabilidad Mensual
    new Chart(document.getElementById('profitabilityChart'), {
        type: 'bar',
        data: {
            labels: monthlyData.map(item => item.month),
            datasets: [{
                label: 'Margen de Ganancia',
                data: monthlyData.map(item => item.profit_margin),
                backgroundColor: monthlyData.map(item => 
                    item.profit_margin >= 20 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'
                )
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => `${value}%`
                    }
                }
            }
        }
    });

    // Métodos de Pago
    new Chart(document.getElementById('paymentMethodsChart'), {
        type: 'doughnut',
        data: {
            labels: paymentMethods.map(item => item.method),
            datasets: [{
                data: paymentMethods.map(item => item.total),
                backgroundColor: [
                    'rgb(59, 130, 246)',
                    'rgb(16, 185, 129)',
                    'rgb(245, 158, 11)',
                    'rgb(239, 68, 68)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
});