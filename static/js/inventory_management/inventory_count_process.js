document.addEventListener('DOMContentLoaded', function() {
    // Obtener ID del inventario
    const container = document.querySelector('[data-inventory-id]');
    const inventoryId = container ? container.dataset.inventoryId : null;

    if (!inventoryId) {
        console.error('No se pudo obtener el ID del inventario');
        return;
    }

    // Elementos del DOM
    const searchInput = document.getElementById('searchProduct');
    const searchResults = document.getElementById('searchResults');
    const searchResultsBody = document.getElementById('searchResultsBody');
    const currentProduct = document.getElementById('currentProduct');
    
    let searchTimeout;

    // Búsqueda de productos
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.trim();
            
            // Limpiar timeout anterior
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }

            if (query.length < 2) {
                searchResults.classList.add('hidden');
                return;
            }

            // Establecer nuevo timeout para la búsqueda
            searchTimeout = setTimeout(() => {
                fetch(`/inventory/api/search-products/?inventory_id=${inventoryId}&query=${query}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            searchResultsBody.innerHTML = '';
                            
                            data.results.forEach(product => {
                                const row = document.createElement('tr');
                                row.className = 'hover:bg-gray-50 cursor-pointer';
                                row.innerHTML = `
                                    <td class="px-6 py-4">
                                        <div class="text-sm font-medium text-gray-900">${product.product_name}</div>
                                        <div class="text-sm text-gray-500">${product.product_code || 'Sin código'}</div>
                                        <div class="text-sm text-gray-500">${product.category}</div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        Stock esperado: ${product.expected_quantity}
                                    </td>
                                `;
                                
                                row.addEventListener('click', () => selectProduct(product));
                                searchResultsBody.appendChild(row);
                            });

                            searchResults.classList.remove('hidden');
                        } else {
                            throw new Error(data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error en búsqueda:', error);
                        alert('Error al buscar productos: ' + error.message);
                    });
            }, 300);
        });
    }

    // Función para seleccionar un producto
    function selectProduct(product) {
        console.log('Producto seleccionado:', product); // Debug
    
        // Ocultar resultados de búsqueda
        if (searchResults) {
            searchResults.classList.add('hidden');
        }
        if (searchInput) {
            searchInput.value = '';
        }
    
        // Obtener referencias a los elementos del DOM
        const productNameElement = document.getElementById('productName');
        const productCodeElement = document.getElementById('productCode');
        const productCategoryElement = document.getElementById('productCategory');
        const expectedQuantityElement = document.getElementById('expectedQuantity');
        const actualQuantityInput = document.getElementById('actualQuantity');
        const countNotesInput = document.getElementById('countNotes');
        const unitTypeSpan = document.getElementById('unitType'); // Agregar esta línea
    
        // Verificar que todos los elementos existan antes de manipularlos
        if (!productNameElement || !productCodeElement || !productCategoryElement || 
            !expectedQuantityElement || !actualQuantityInput || !countNotesInput || !currentProduct) {
            console.error('Elementos del DOM no encontrados');
            return;
        }
    
        try {
            // Mostrar información del producto
            productNameElement.textContent = product.product_name || 'Sin nombre';
            productCodeElement.textContent = product.product_code || 'Sin código';
            productCategoryElement.textContent = product.category || 'Sin categoría';
            expectedQuantityElement.textContent = product.expected_quantity || '0';
    
            // Configurar input según tipo de producto
            if (product.is_bulk) {
                actualQuantityInput.setAttribute('step', '0.01');
                actualQuantityInput.setAttribute('min', '0');
                actualQuantityInput.setAttribute('placeholder', 'Ingrese kilos');
                if (unitTypeSpan) unitTypeSpan.textContent = '(kilos)';
            } else {
                actualQuantityInput.setAttribute('step', '1');
                actualQuantityInput.setAttribute('min', '0');
                actualQuantityInput.setAttribute('placeholder', 'Ingrese unidades');
                if (unitTypeSpan) unitTypeSpan.textContent = '(unidades)';
            }
    
            // Limpiar campos de entrada
            actualQuantityInput.value = '';
            countNotesInput.value = '';
    
            // Guardar ID del detalle seleccionado
            currentProduct.dataset.detailId = product.id;
            currentProduct.classList.remove('hidden');
    
            // Enfocar campo de cantidad
            actualQuantityInput.focus();
        } catch (error) {
            console.error('Error al seleccionar producto:', error);
            alert('Error al mostrar el producto seleccionado');
        }
    }

    // Guardar conteo
    const saveButton = document.getElementById('saveCount');
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            const detailId = currentProduct.dataset.detailId;
            const quantity = document.getElementById('actualQuantity').value;
            const notes = document.getElementById('countNotes').value;

            if (!quantity) {
                alert('Por favor ingrese la cantidad contada');
                return;
            }

            fetch('/inventory/api/save-count/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    detail_id: detailId,
                    quantity: quantity,
                    notes: notes
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Actualizar progreso
                    updateProgress(data.progress);
                    // Limpiar y ocultar formulario
                    currentProduct.classList.add('hidden');
                    // Enfocar búsqueda para siguiente producto
                    searchInput.focus();
                    location.reload(); // Forzar recarga para actualizar la vista
                } else {
                    throw new Error(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al guardar el conteo: ' + error.message);
            });
        });
    }

    // Actualizar progreso
    function updateProgress(progress) {
        document.getElementById('countedProducts').textContent = progress.counted;
        document.getElementById('pendingProducts').textContent = 
            progress.total - progress.counted;
        
        const percentage = Math.round((progress.counted / progress.total) * 100);
        document.getElementById('progressPercentage').textContent = `${percentage}%`;
        document.querySelector('.progress-bar-fill').style.width = `${percentage}%`;
    }

    // Función para obtener CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Manejar botón de pausa
    const pauseButton = document.getElementById('pauseButton');
    if (pauseButton) {
        pauseButton.addEventListener('click', function() {
            if (confirm('¿Está seguro de pausar el conteo? Podrá continuarlo más tarde.')) {
                fetch(`/inventory/${inventoryId}/pause/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        window.location.href = data.redirect_url;
                    } else {
                        throw new Error(data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(error.message || 'Error al pausar el inventario');
                });
            }
        });
    }

    // Manejar botón de finalizar
    const finishButton = document.getElementById('finishButton');
    if (finishButton) {
        finishButton.addEventListener('click', function() {
            if (confirm('¿Está seguro de finalizar el conteo? Esta acción no se puede deshacer.')) {
                fetch(`/inventory/${inventoryId}/finish/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        window.location.href = data.redirect_url;
                    } else {
                        throw new Error(data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(error.message || 'Error al finalizar el inventario');
                });
            }
        });
    }
});