document.addEventListener('DOMContentLoaded', function() {
    const dateFrom = document.getElementById('date-from');
    const dateTo = document.getElementById('date-to');
    const applyFilters = document.getElementById('apply-filters');
    const salesTableBody = document.getElementById('sales-table-body');
    const customerId = window.location.pathname.split('/').filter(Boolean).pop();

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-CL', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function formatMoney(amount) {
        return new Intl.NumberFormat('es-CL', {
            style: 'currency',
            currency: 'CLP',
            minimumFractionDigits: 0
        }).format(amount);
    }

    function getStatusClass(status) {
        return status === 'COMPLETED' 
            ? 'bg-green-100 text-green-800'
            : 'bg-yellow-100 text-yellow-800';
    }

    async function updateSalesHistory() {
        try {
            const params = new URLSearchParams();
            if (dateFrom.value) params.append('date_from', dateFrom.value);
            if (dateTo.value) params.append('date_to', dateTo.value);

            const response = await fetch(`/customers/api/customer/${customerId}/history/?${params}`);
            if (!response.ok) throw new Error('Error al cargar historial');
            
            const data = await response.json();
            
            // Actualizar métricas
            document.querySelector('[data-metric="total-spent"]').textContent = formatMoney(data.metrics.total_spent);
            document.querySelector('[data-metric="total-sales"]').textContent = data.metrics.total_sales;
            document.querySelector('[data-metric="avg-ticket"]').textContent = formatMoney(data.metrics.avg_ticket);
            document.querySelector('[data-metric="purchase-frequency"]').textContent = 
                `${data.metrics.purchase_frequency} días`;

            // Actualizar tabla
            salesTableBody.innerHTML = data.sales.map(sale => `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap">${formatDate(sale.date)}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${sale.number}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${sale.items}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${formatMoney(sale.total)}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClass(sale.status)}">
                            ${sale.status_display}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <a href="/sales/${sale.id}/" class="text-blue-600 hover:text-blue-900">
                            Ver detalle
                        </a>
                    </td>
                </tr>
            `).join('');

        } catch (error) {
            console.error('Error actualizando historial:', error);
        }
    }

    if (applyFilters) {
        applyFilters.addEventListener('click', updateSalesHistory);
    }
});