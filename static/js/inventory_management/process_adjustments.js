document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const searchInput = document.getElementById('searchInput');
    const itemsPerPage = document.getElementById('itemsPerPage');
    const selectAll = document.getElementById('selectAll');
    const tableBody = document.getElementById('adjustmentsTableBody');
    const confirmationModal = document.getElementById('confirmationModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const modalConfirm = document.getElementById('modalConfirm');
    const modalCancel = document.getElementById('modalCancel');
    const applySelected = document.getElementById('applySelected');
    const applyAll = document.getElementById('applyAll');

    // Estado
    let currentPage = 1;
    let allRows = Array.from(tableBody.querySelectorAll('tr'));
    let filteredRows = [...allRows];

    // Inicialización
    updatePagination();

    // Manejar cambio en items por página
    itemsPerPage.addEventListener('change', function() {
        currentPage = 1;
        updatePagination();
    });

    // Manejar búsqueda
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        filteredRows = allRows.filter(row => {
            const productName = row.querySelector('.text-gray-900')?.textContent.toLowerCase() || '';
            const category = row.querySelector('.text-gray-500')?.textContent.toLowerCase() || '';
            return productName.includes(searchTerm) || category.includes(searchTerm);
        });
        currentPage = 1;
        updatePagination();
    });

    // Seleccionar todos
    selectAll.addEventListener('change', function() {
        // Obtener solo las filas visibles
        const visibleRows = getVisibleRows();
        
        // Obtener checkboxes de las filas visibles
        const checkboxes = visibleRows
            .map(row => row.querySelector('.product-checkbox'))
            .filter(checkbox => checkbox !== null);
        
        // Actualizar estado de los checkboxes
        checkboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
    });

    // Aplicar ajustes seleccionados
    applySelected.addEventListener('click', function() {
        const selectedDetails = getSelectedDetails();
        if (selectedDetails.length === 0) {
            alert('Por favor seleccione al menos un producto');
            return;
        }
        showConfirmationModal(
            'Confirmar Ajustes',
            `¿Está seguro de aplicar los ajustes a ${selectedDetails.length} producto(s)?`,
            () => processAdjustments(selectedDetails)
        );
    });

    // Aplicar todos los ajustes
    applyAll.addEventListener('click', function() {
        const allDetails = getAllDetails();
        showConfirmationModal(
            'Confirmar Todos los Ajustes',
            `¿Está seguro de aplicar los ajustes a todos los productos (${allDetails.length})?`,
            () => processAdjustments(allDetails)
        );
    });

    // evento para los checkboxes individuales
    tableBody.addEventListener('change', function(e) {
        if (e.target.classList.contains('product-checkbox')) {
            // Verificar si todos los checkboxes visibles están seleccionados
            const visibleRows = getVisibleRows();
            const visibleCheckboxes = visibleRows
                .map(row => row.querySelector('.product-checkbox'))
                .filter(checkbox => checkbox !== null);
            
            const allChecked = visibleCheckboxes.every(checkbox => checkbox.checked);
            selectAll.checked = allChecked;
        }
    });

    // Funciones auxiliares
    function updatePagination() {
        const itemsPerPageValue = parseInt(itemsPerPage.value);
        const totalPages = Math.ceil(filteredRows.length / itemsPerPageValue);
        const startIndex = (currentPage - 1) * itemsPerPageValue;
        const endIndex = Math.min(startIndex + itemsPerPageValue, filteredRows.length);

        // Actualizar filas visibles
        allRows.forEach(row => row.style.display = 'none');
        filteredRows.slice(startIndex, endIndex).forEach(row => row.style.display = '');

        // Actualizar información de paginación
        document.getElementById('itemsShowing').textContent = 
            `${startIndex + 1}-${endIndex}`;
        document.getElementById('totalItems').textContent = 
            filteredRows.length;

        // Generar botones de paginación
        const pagination = document.getElementById('pagination');
        pagination.innerHTML = '';

        // Botón anterior
        if (currentPage > 1) {
            pagination.appendChild(createPaginationButton('Anterior', currentPage - 1));
        }

        // Páginas
        for (let i = 1; i <= totalPages; i++) {
            if (
                i === 1 || 
                i === totalPages || 
                (i >= currentPage - 2 && i <= currentPage + 2)
            ) {
                pagination.appendChild(createPaginationButton(i.toString(), i));
            } else if (
                i === currentPage - 3 || 
                i === currentPage + 3
            ) {
                pagination.appendChild(createPaginationButton('...', i, true));
            }
        }

        // Botón siguiente
        if (currentPage < totalPages) {
            pagination.appendChild(createPaginationButton('Siguiente', currentPage + 1));
        }
    }

    function createPaginationButton(text, page, disabled = false) {
        const button = document.createElement('button');
        button.textContent = text;
        let classes = ['px-3', 'py-1', 'rounded-md', 'text-sm', 'font-medium'];
        if (page === currentPage) {
            classes.push('bg-blue-500', 'text-white');
        } else {
            classes.push('bg-white', 'text-gray-700', 'hover:bg-gray-50');
        }
        button.classList.add(...classes);
        if (!disabled) {
            button.addEventListener('click', () => {
                currentPage = page;
                updatePagination();
            });
        }
        return button;
    }

    function getVisibleRows() {
        return Array.from(tableBody.querySelectorAll('tr'))
            .filter(row => row.style.display !== 'none');
    }

    function getSelectedDetails() {
        return Array.from(tableBody.querySelectorAll('.product-checkbox:checked'))
            .map(checkbox => ({
                id: checkbox.dataset.detailId,
                reason: checkbox.closest('tr').querySelector('.adjustment-reason').value
            }));
    }

    function getAllDetails() {
        return Array.from(tableBody.querySelectorAll('.product-checkbox'))
            .map(checkbox => ({
                id: checkbox.dataset.detailId,
                reason: checkbox.closest('tr').querySelector('.adjustment-reason').value
            }));
    }

    function showConfirmationModal(title, message, onConfirm) {
        modalTitle.textContent = title;
        modalMessage.textContent = message;
        confirmationModal.classList.remove('hidden');

        modalConfirm.onclick = () => {
            onConfirm();
            confirmationModal.classList.add('hidden');
        };

        modalCancel.onclick = () => {
            confirmationModal.classList.add('hidden');
        };
    }

    // Modificar la función processAdjustments:
    function processAdjustments(details) {
        if (!details || details.length === 0) {
            alert('No hay productos seleccionados para ajustar');
            return;
        }
    
        fetch('/inventory/api/apply-adjustments/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                detail_ids: details.map(d => d.id)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Ajustes aplicados correctamente');
                window.location.reload();
            } else {
                throw new Error(data.message || 'Error al aplicar los ajustes');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al aplicar ajustes: ' + error.message);
        });
    }

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