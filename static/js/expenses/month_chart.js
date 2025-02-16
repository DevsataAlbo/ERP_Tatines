document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('monthChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: window.chartData.labels,
            datasets: [{
                data: window.chartData.values,
                backgroundColor: [
                    '#4F46E5', '#7C3AED', '#EC4899', '#EF4444', '#F59E0B',
                    '#10B981', '#3B82F6', '#6366F1', '#8B5CF6', '#D946EF'
                ]
            }]
        },
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
                            const percentage = ((value * 100) / total).toFixed(1);
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
});