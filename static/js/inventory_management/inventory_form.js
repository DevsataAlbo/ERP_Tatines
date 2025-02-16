document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('inventoryForm');
    const cancelButton = document.querySelector('.cancel-button');

    // Manejar envío del formulario
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validar nombre
            const nameInput = document.getElementById('id_name');
            if (!nameInput.value.trim()) {
                showError(nameInput, 'El nombre del inventario es requerido');
                return;
            }

            // Confirmar antes de enviar
            if (confirm('¿Está seguro de crear este inventario? Una vez creado, comenzará el proceso de conteo.')) {
                this.submit();
            }
        });
    }

    // Manejar botón cancelar
    if (cancelButton) {
        cancelButton.addEventListener('click', function() {
            if (confirm('¿Está seguro de cancelar? Se perderán los cambios no guardados.')) {
                window.location.href = document.querySelector('a[href*="inventory_management:list"]').href;
            }
        });
    }

    // Función para mostrar errores de validación
    function showError(inputElement, message) {
        // Remover mensaje de error anterior si existe
        const existingError = inputElement.parentElement.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        // Crear y mostrar nuevo mensaje de error
        const errorDiv = document.createElement('p');
        errorDiv.className = 'error-message mt-1 text-sm text-red-600';
        errorDiv.textContent = message;
        inputElement.parentElement.appendChild(errorDiv);

        // Resaltar input con error
        inputElement.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        
        // Enfocar el input con error
        inputElement.focus();
    }

    // Manejar selección de categorías
    const categoryCheckboxes = document.querySelectorAll('input[name="categories"]');
    if (categoryCheckboxes.length > 0) {
        // Contador de categorías seleccionadas
        function updateSelectedCount() {
            const selectedCount = document.querySelectorAll('input[name="categories"]:checked').length;
            const totalCount = categoryCheckboxes.length;
            const categoryLabel = document.querySelector('label[for^="category_"]').closest('div').previousElementSibling;
            
            if (categoryLabel) {
                categoryLabel.textContent = `Categorías (${selectedCount} de ${totalCount} seleccionadas)`;
            }
        }

        // Agregar listener a cada checkbox
        categoryCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateSelectedCount);
        });

        // Inicializar contador
        updateSelectedCount();
    }
});