// static/js/financial_reports/dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    const { salesTrends, expenseData } = window.dashboardData;

    // Gráfico de tendencia de ventas
    if (salesTrends && salesTrends.length > 0) {
        const ctx = document.getElementById('salesTrendChart');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: salesTrends.map(item => {
                    const fecha = new Date(item.fecha);
                    return fecha.toLocaleDateString('es-CL', {
                        day: '2-digit',
                        month: 'short'
                    });
                }),
                datasets: [{
                    label: 'Ventas',
                    data: salesTrends.map(item => item.total_ventas),
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return '$ ' + new Intl.NumberFormat('es-CL').format(context.raw);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => '$ ' + new Intl.NumberFormat('es-CL').format(value)
                        }
                    }
                }
            }
        });
    }

    // Gráfico de gastos por categoría
    const expenseCtx = document.getElementById('expensePieChart');
        if (expenseCtx && expenseData) {  // Removemos la verificación de by_category
            new Chart(expenseCtx, {
                type: 'pie',
                data: {
                    labels: expenseData.map(item => item.category__name || 'Sin categoría'),
                    datasets: [{
                        data: expenseData.map(item => parseFloat(item.total || 0)),
                        backgroundColor: [
                            'rgb(59, 130, 246)',  // Azul
                            'rgb(34, 197, 94)',   // Verde
                            'rgb(245, 158, 11)',  // Naranja
                            'rgb(239, 68, 68)',   // Rojo
                            'rgb(139, 92, 246)',  // Morado
                            'rgb(14, 165, 233)'   // Celeste
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.raw;
                                    return `${context.label}: $ ${new Intl.NumberFormat('es-CL').format(value)}`;
                                }
                            }
                        }
                    }
                }
            });
        };


        // Manejo de selectores de período
        const periodSelectors = document.querySelectorAll('.period-selector');
        periodSelectors.forEach(button => {
            button.addEventListener('click', function() {
                const period = this.dataset.period;
                const currentUrl = new URL(window.location.href);
                
                // Limpiar filtros de fecha manual si existen
                currentUrl.searchParams.delete('date_from');
                currentUrl.searchParams.delete('date_to');
                
                // Establecer nuevo período
                currentUrl.searchParams.set('period', period);
                window.location.href = currentUrl.toString();
            });
        });
});