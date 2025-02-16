export function initializeCustomerSelect(selectElement) {
    if (!selectElement) {
        console.log('No se encontró el elemento select de clientes');
        return;
    }
    console.log('Inicializando selector de clientes');

    let searchTimeout;
    let lastSelectedId = null;

    async function searchCustomers(query) {
        try {
            const response = await fetch(`/customers/api/search/?term=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const customers = await response.json();
            console.log('Clientes encontrados:', customers);
            
            // Guardar el ID seleccionado antes de actualizar las opciones
            lastSelectedId = selectElement.value;
            
            selectElement.innerHTML = '<option value="">Seleccionar cliente</option>';
            
            customers.forEach(customer => {
                const option = document.createElement('option');
                option.value = customer.id;
                option.textContent = `${customer.text} (${customer.rut})`;
                // Restaurar la selección si este era el cliente seleccionado
                if (customer.id.toString() === lastSelectedId) {
                    option.selected = true;
                }
                selectElement.appendChild(option);
            });
            
            // Si el cliente seleccionado ya no está en los resultados,
            // asegurarse de que siga disponible
            if (lastSelectedId && !customers.find(c => c.id.toString() === lastSelectedId)) {
                const selectedCustomer = await getCustomerById(lastSelectedId);
                if (selectedCustomer) {
                    const option = document.createElement('option');
                    option.value = selectedCustomer.id;
                    option.textContent = `${selectedCustomer.text} (${selectedCustomer.rut})`;
                    option.selected = true;
                    selectElement.appendChild(option);
                }
            }
        } catch (error) {
            console.error('Error buscando clientes:', error);
        }
    }

    async function getCustomerById(id) {
        try {
            const response = await fetch(`/customers/api/search/?term=${id}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const customers = await response.json();
            return customers.find(c => c.id.toString() === id);
        } catch (error) {
            console.error('Error obteniendo cliente por ID:', error);
            return null;
        }
    }

    // Cargar clientes iniciales
    searchCustomers('');

    // Manejar búsqueda al escribir
    selectElement.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchCustomers(e.target.value);
        }, 300);
    });

    // Guardar el ID cuando se selecciona un cliente
    selectElement.addEventListener('change', (e) => {
        lastSelectedId = e.target.value;
    });
}