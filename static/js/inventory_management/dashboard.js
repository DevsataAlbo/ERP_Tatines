document.addEventListener('DOMContentLoaded', function() {
    // Configuración común para los gráficos
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        }
    };

    // Variables para los gráficos
    let trendsChart = null;
    let categoriesChart = null;

    // Función para inicializar/actualizar datos
    function loadDashboardData() {
        const period = document.getElementById('periodFilter').value;
        const trendType = document.getElementById('trendType').value;
        const categoryMetric = document.getElementById('categoryMetric').value;
        const problemMetric = document.getElementById('problemMetric').value;

        fetch(`/inventory/api/dashboard-data/?period=${period}&trend_type=${trendType}&category_metric=${categoryMetric}&problem_metric=${problemMetric}`)
            .then(response => response.json())
            .then(data => {
                updateSummaryCards(data.summary);
                updateTrendsChart(data.trends);
                updateCategoriesChart(data.categories);
                updateProblematicProducts(data.problematic_products);
            })
            .catch(error => {
                console.error('Error cargando datos del dashboard:', error);
            });
    }

    // Actualizar tarjetas de resumen con tendencias
    function updateSummaryCards(summary) {
        console.log('Datos de resumen recibidos:', summary); // Debug

        const updateCardValue = (elementId, data) => {
            const element = document.getElementById(elementId);
            if (element && data) {
                const valueSpan = element.querySelector('.value');
                
                // Para valores monetarios
                if (elementId === 'totalValue') {
                    valueSpan.textContent = formatCurrency(data.value || 0);
                } else {
                    // Para valores numéricos normales
                    valueSpan.textContent = formatNumber(data.value || 0);
                }

                // Para tendencias
                const trendSpan = element.querySelector('.trend');
                if (trendSpan) {
                    const trend = data.trend || 0;
                    if (trend > 0) {
                        trendSpan.innerHTML = `<i class="fas fa-arrow-up text-green-500"></i> ${formatNumber(trend)}%`;
                    } else if (trend < 0) {
                        trendSpan.innerHTML = `<i class="fas fa-arrow-down text-red-500"></i> ${formatNumber(Math.abs(trend))}%`;
                    } else {
                        trendSpan.innerHTML = `<i class="fas fa-minus text-gray-500"></i>`;
                    }
                }
            }
        };

        // Función de formato de moneda
        function formatCurrency(value) {
            if (typeof value !== 'number' || isNaN(value)) {
                return '$0';
            }
            return new Intl.NumberFormat('es-CL', {
                style: 'currency',
                currency: 'CLP',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(value);
        }

        // Función de formato de números
        function formatNumber(value) {
            if (typeof value !== 'number' || isNaN(value)) {
                return '0';
            }
            return new Intl.NumberFormat('es-CL', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            }).format(value);
        }

        // Actualizar cada card
        updateCardValue('totalInventories', summary.totalInventories);
        updateCardValue('inProgressCount', summary.inProgressCount);
        updateCardValue('totalDifferences', summary.totalDifferences);
        updateCardValue('totalValue', summary.totalValue);
    }

    // Inicializar/Actualizar gráfico de tendencias
    function updateTrendsChart(trendsData) {
        const ctx = document.getElementById('trendsChart').getContext('2d');
        
        if (trendsChart) {
            trendsChart.destroy();
        }

        trendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendsData.labels,
                datasets: [
                    {
                        label: 'Diferencias Positivas',
                        data: trendsData.positive_differences,
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        fill: true
                    },
                    {
                        label: 'Diferencias Negativas',
                        data: trendsData.negative_differences,
                        borderColor: 'rgb(239, 68, 68)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: true
                    }
                ]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: getTrendAxisLabel()
                        }
                    }
                }
            }
        });
    }

    // Inicializar/Actualizar gráfico de categorías
    function updateCategoriesChart(categoriesData) {
        const ctx = document.getElementById('categoriesChart').getContext('2d');
        
        if (categoriesChart) {
            categoriesChart.destroy();
        }

        categoriesChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: categoriesData.labels,
                datasets: [{
                    label: getCategoryDatasetLabel(),
                    data: categoriesData.values,
                    backgroundColor: categoriesData.labels.map((_, index) => 
                        `hsl(${index * (360 / categoriesData.labels.length)}, 70%, 60%)`
                    )
                }]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: getCategoryAxisLabel()
                        }
                    }
                }
            }
        });
    }

    // Actualizar tabla de productos problemáticos
    function updateProblematicProducts(products) {
        const tbody = document.getElementById('problematicProductsBody');
        tbody.innerHTML = '';

        products.forEach(product => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">${product.name}</div>
                    <div class="text-sm text-gray-500">${product.code || 'Sin código'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs font-medium rounded-full ${
                        product.total_difference < 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    }">
                        ${formatNumber(product.total_difference)}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="w-16 bg-gray-200 rounded-full h-2">
                        <div class="bg-blue-600 h-2 rounded-full" 
                            style="width: ${Math.min(100, product.frequency)}%">
                        </div>
                    </div>
                    <span class="ml-2 text-sm text-gray-500">
                        ${formatNumber(product.frequency)}%
                    </span>
                </div>
            </td>
        `;
        tbody.appendChild(row);
        });
    }

    // Funciones auxiliares
    function getTrendAxisLabel() {
        const type = document.getElementById('trendType').value;
        switch (type) {
            case 'differences': return 'Cantidad';
            case 'counts': return 'Número de Conteos';
            case 'value': return 'Valor (CLP)';
            default: return 'Cantidad';
        }
    }

    function getCategoryDatasetLabel() {
        const metric = document.getElementById('categoryMetric').value;
        switch (metric) {
            case 'quantity': return 'Diferencias por Cantidad';
            case 'value': return 'Diferencias por Valor';
            case 'frequency': return 'Frecuencia de Diferencias';
            default: return 'Diferencias por Categoría';
        }
    }

    function getCategoryAxisLabel() {
        const metric = document.getElementById('categoryMetric').value;
        switch (metric) {
            case 'quantity': return 'Cantidad';
            case 'value': return 'Valor (CLP)';
            case 'frequency': return 'Frecuencia (%)';
            default: return 'Cantidad';
        }
    }

    function formatCurrency(value) {
        return new Intl.NumberFormat('es-CL', {
            style: 'currency',
            currency: 'CLP'
        }).format(value);
    }

    function formatNumber(value) {
        // Para porcentajes, redondear a 2 decimales
        if (typeof value === 'number') {
            return new Intl.NumberFormat('es-CL', {
                maximumFractionDigits: 2
            }).format(value);
        }
        return '0';
    }

    // Event Listeners
    document.getElementById('periodFilter').addEventListener('change', loadDashboardData);
    document.getElementById('trendType').addEventListener('change', loadDashboardData);
    document.getElementById('categoryMetric').addEventListener('change', loadDashboardData);
    document.getElementById('problemMetric').addEventListener('change', loadDashboardData);

    // Exportar productos problemáticos
    const exportButton = document.getElementById('exportProblematicProducts');
    if (exportButton) {
        exportButton.addEventListener('click', function() {
            const metric = document.getElementById('problemMetric').value;
            window.location.href = `/inventory/api/export-problematic-products/?metric=${metric}`;
        });
    }

    // Inicializar datos
    loadDashboardData();

    // Actualizar datos cada 5 minutos
    setInterval(loadDashboardData, 5 * 60 * 1000);
});