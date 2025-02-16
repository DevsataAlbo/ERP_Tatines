document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const tableBody = document.getElementById('customers-table-body');
    let searchTimeout;

    async function searchCustomers(query) {
        try {
            const response = await fetch(`/customers/api/search/?term=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('Error en la búsqueda');
            const customers = await response.json();
            
            updateTable(customers);
        } catch (error) {
            console.error('Error buscando clientes:', error);
        }
    }

    function updateTable(customers) {
        if (customers.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-4 text-center text-gray-500">
                        No se encontraron clientes
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = customers.map(customer => `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${customer.rut}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${customer.text}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${customer.customer_type || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${customer.email || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${customer.phone || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <a href="/customers/${customer.id}/" 
                       class="text-blue-600 hover:text-blue-900">
                        Ver detalle
                    </a>
                </td>
            </tr>
        `).join('');
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchCustomers(e.target.value);
            }, 300);
        });
    }
});