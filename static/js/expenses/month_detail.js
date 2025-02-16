document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const closeMonthBtn = document.getElementById('closeMonthBtn');
    const closeMonthModal = document.getElementById('closeMonthModal');
    const confirmCloseBtn = document.getElementById('confirmCloseBtn');
    const cancelCloseBtn = document.getElementById('cancelCloseBtn');

    // Inicializar gráfico de distribución
    const ctx = document.getElementById('monthDistributionChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: window.monthData.categories,
            datasets: [{
                data: window.monthData.amounts,
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
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value * 100) / total);
                            return `${label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });

    // Manejadores para el modal de cierre de mes
    if (closeMonthBtn) {
        closeMonthBtn.addEventListener('click', () => {
            closeMonthModal.classList.remove('hidden');
        });

        confirmCloseBtn.addEventListener('click', async () => {
            try {
                const response = await fetch(window.monthData.closeUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    const data = await response.json();
                    alert(data.error || 'Error al cerrar el mes');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error al procesar la solicitud');
            }
        });

        cancelCloseBtn.addEventListener('click', () => {
            closeMonthModal.classList.add('hidden');
        });

        // Cerrar modal al hacer clic fuera
        closeMonthModal.addEventListener('click', (e) => {
            if (e.target === closeMonthModal) {
                closeMonthModal.classList.add('hidden');
            }
        });
    }
});