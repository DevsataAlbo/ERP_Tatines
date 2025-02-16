document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Cargado - Inicializando manejadores de reconteo');

    // Inicializar barras de progreso
    function initializeProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar-fill');
        progressBars.forEach(bar => {
            const percentage = bar.dataset.progress || 0;
            requestAnimationFrame(() => {
                bar.style.transition = 'width 0.5s ease-out';
                bar.style.width = `${percentage}%`;
            });
        });
    }

    // Búsqueda y filtrado
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const rows = document.querySelectorAll('.product-row');

    function filterProducts() {
        const searchTerm = searchInput.value.toLowerCase();
        const filterStatus = statusFilter.value;

        rows.forEach(row => {
            const productName = row.querySelector('td:first-child').textContent.toLowerCase();
            const rowStatus = row.dataset.status;
            const difference = row.querySelector('td:nth-child(4)').textContent.trim();
            const hasDifference = difference !== '-' && difference !== '0';

            let showRow = productName.includes(searchTerm);

            if (filterStatus === 'pending') {
                showRow = showRow && rowStatus === 'pending';
            } else if (filterStatus === 'counted') {
                showRow = showRow && rowStatus === 'counted';
            } else if (filterStatus === 'differences') {
                showRow = showRow && hasDifference;
            }

            row.style.display = showRow ? '' : 'none';
        });

        updateSummary();
    }

    // Actualizar resumen
    function updateSummary() {
        const visibleRows = document.querySelectorAll('.product-row:not([style*="display: none"])');
        const totalRows = rows.length;
        const countedRows = document.querySelectorAll('.product-row[data-status="counted"]').length;
        
        // Actualizar contadores
        document.getElementById('counted-products').textContent = countedRows;
        
        // Actualizar porcentaje
        const percentage = Math.round((countedRows / totalRows) * 100);
        document.getElementById('progress-percentage').textContent = percentage;
        
        // Actualizar barra de progreso
        const progressBar = document.querySelector('.progress-bar-fill');
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
    }

    // Event listeners
    if (searchInput) {
        searchInput.addEventListener('input', filterProducts);
    }

    if (statusFilter) {
        statusFilter.addEventListener('change', filterProducts);
    }

    // Ordenamiento de columnas
    document.querySelectorAll('th').forEach(headerCell => {
        headerCell.addEventListener('click', () => {
            const tableBody = document.querySelector('tbody');
            const rows = Array.from(tableBody.querySelectorAll('tr'));
            const columnIndex = Array.from(headerCell.parentNode.children).indexOf(headerCell);
            const isNumeric = headerCell.textContent.includes('Cantidad') || 
                            headerCell.textContent.includes('Diferencia');

            // Determinar dirección de ordenamiento
            const currentDirection = headerCell.dataset.direction === 'asc' ? 'desc' : 'asc';
            headerCell.dataset.direction = currentDirection;

            // Ordenar filas
            rows.sort((a, b) => {
                const aValue = a.children[columnIndex].textContent.trim();
                const bValue = b.children[columnIndex].textContent.trim();

                if (isNumeric) {
                    const aNum = aValue === '-' ? 0 : parseFloat(aValue);
                    const bNum = bValue === '-' ? 0 : parseFloat(bValue);
                    return currentDirection === 'asc' ? aNum - bNum : bNum - aNum;
                }

                if (currentDirection === 'asc') {
                    return aValue.localeCompare(bValue);
                } else {
                    return bValue.localeCompare(aValue);
                }
            });

            // Actualizar tabla
            rows.forEach(row => tableBody.appendChild(row));

            // Actualizar indicadores visuales de ordenamiento
            document.querySelectorAll('th').forEach(th => {
                th.classList.remove('sorted-asc', 'sorted-desc');
            });
            headerCell.classList.add(`sorted-${currentDirection}`);
        });
    });

    // Exportar a Excel (si existe el botón)
    const exportButton = document.getElementById('exportButton');
    if (exportButton) {
        exportButton.addEventListener('click', function() {
            const inventoryId = this.dataset.inventoryId;
            window.location.href = `/inventory/${inventoryId}/export/`;
        });
    }

    // Inicialización
    initializeProgressBars();
    
    // Actualizar resumen inicial
    updateSummary();

    // Tooltip para diferencias (opcional)
    const differenceCells = document.querySelectorAll('td:nth-child(4)');
    differenceCells.forEach(cell => {
        const value = parseFloat(cell.textContent);
        if (!isNaN(value) && value !== 0) {
            cell.title = value > 0 ? 'Sobrante' : 'Faltante';
        }
    });

    // Obtener ID del inventario
    const inventoryId = document.querySelector('[data-inventory-id]').dataset.inventoryId;

    // Manejar botón de inicio de conteo
    const startCountButton = document.getElementById('startCountButton');
    if (startCountButton) {
        startCountButton.addEventListener('click', function() {
            if (confirm('¿Está seguro de iniciar el conteo? Una vez iniciado, no podrá modificar la configuración del inventario.')) {
                fetch(`/inventory/${inventoryId}/start/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
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
                    alert(error.message || 'Error al iniciar el conteo');
                });
            }
        });
    }

    // Manejar solicitudes de reconteo
    document.querySelectorAll('.request-recount-btn').forEach(button => {
        console.log('Botón de reconteo encontrado');
        
        button.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Botón de reconteo clickeado');
            
            const detailId = this.dataset.detailId;
            const productName = this.dataset.productName;
            
            console.log('Detail ID:', detailId);
            console.log('Product Name:', productName);
    
            const reason = prompt(`Ingrese el motivo para el reconteo de ${productName}:`);
            if (reason === null) {
                console.log('Usuario canceló el prompt');
                return;
            }
    
            console.log('Razón ingresada:', reason);
            console.log('Enviando solicitud de reconteo...');
    
            // URL corregida
            fetch(`/inventory/api/recount/${detailId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ reason: reason })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert(data.message);
                    window.location.reload();
                } else {
                    throw new Error(data.message || 'Error al solicitar reconteo');
                }
            })
            .catch(error => {
                console.error('Error en la solicitud:', error);
                alert('Error al procesar la solicitud: ' + error.message);
            });
        });
    });

    // Función para obtener el token CSRF
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
});