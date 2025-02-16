document.addEventListener('DOMContentLoaded', function() {
    const { profitableProducts, expenseCategories } = window.kpisData;

    // Productos Rentables
    new Chart(document.getElementById('profitableProductsChart'), {
        type: 'bar',
        data: {
            labels: profitableProducts.map(p => p.name),
            datasets: [{
                label: 'Margen de Ganancia',
                data: profitableProducts.map(p => p.profit_margin),
                backgroundColor: 'rgb(34, 197, 94)',
                barThickness: 20
            }]
        },
        options: {
            indexAxis: 'y',
            elements: {
                bar: {
                    borderWidth: 2,
                }
            },
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: value => `${value}%`
                    }
                }
            }
        }
    });

    // Gastos por Categoría
    new Chart(document.getElementById('expensesChart'), {
        type: 'doughnut',
        data: {
            labels: expenseCategories.map(c => c.name),
            datasets: [{
                data: expenseCategories.map(c => c.total),
                backgroundColor: [
                    'rgb(59, 130, 246)',
                    'rgb(16, 185, 129)',
                    'rgb(245, 158, 11)',
                    'rgb(239, 68, 68)',
                    'rgb(139, 92, 246)'
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