document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const saveAllBtn = document.getElementById('saveAllBtn');
    const rows = document.querySelectorAll('.inventory-row');

    // Función de búsqueda
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            rows.forEach(row => {
                const productName = row.querySelector('.text-gray-900').textContent.toLowerCase();
                row.style.display = productName.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Validación de cantidades
    rows.forEach(row => {
        const quantityInput = row.querySelector('.new-quantity');
        if (quantityInput) {
            quantityInput.addEventListener('change', function() {
                const step = this.getAttribute('step');
                if (step === '1') {
                    // Para productos por unidad, forzar números enteros
                    this.value = Math.round(this.value);
                }
            });
        }
    });

    // Guardar cambios
    if (saveAllBtn) {
        saveAllBtn.addEventListener('click', function() {
            const updates = [];
            let hasChanges = false;

            rows.forEach(row => {
                const detailId = row.dataset.detailId;
                const quantityInput = row.querySelector('.new-quantity');
                const reasonInput = row.querySelector('.change-reason');
                const currentQuantity = row.querySelector('td:nth-child(3)').textContent.trim();

                // Validar y limpiar el valor de cantidad
                let newQuantity = quantityInput.value.trim();
                if (newQuantity === '') {
                    newQuantity = currentQuantity;
                }

                // Verificar si hay cambios
                if (newQuantity !== currentQuantity || reasonInput.value.trim()) {
                    hasChanges = true;
                    
                    // Convertir a número y validar
                    const numericQuantity = parseFloat(newQuantity);
                    if (isNaN(numericQuantity)) {
                        alert(`Cantidad inválida para el producto en la fila ${row.rowIndex}`);
                        return;
                    }

                    updates.push({
                        detail_id: detailId,
                        quantity: numericQuantity,
                        reason: reasonInput.value.trim(),
                        modified: true
                    });
                }
            });

            if (!hasChanges) {
                alert('No se han realizado cambios');
                return;
            }

            if (!confirm('¿Está seguro de guardar los cambios?')) {
                return;
            }

            // Obtener inventoryId de la URL
            const pathParts = window.location.pathname.split('/');
            const inventoryId = pathParts[pathParts.indexOf('inventory') + 1];

            console.log('Enviando actualizaciones:', updates); // Debug

            fetch(`/inventory/${inventoryId}/edit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ updates: updates })
            })
            .then(response => {
                console.log('Respuesta recibida:', response); // Debug
                return response.json();
            })
            .then(data => {
                console.log('Datos recibidos:', data); // Debug
                if (data.status === 'success') {
                    alert('Cambios guardados exitosamente');
                    window.location.href = `/inventory/${inventoryId}/`;
                } else {
                    throw new Error(data.message || 'Error al guardar los cambios');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al guardar los cambios: ' + error.message);
            });
        });
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
});