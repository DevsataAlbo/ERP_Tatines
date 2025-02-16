document.addEventListener('DOMContentLoaded', function() {
    const isBulkCheckbox = document.getElementById('id_is_bulk');
    const bulkConfigFields = document.querySelectorAll('.bulk-config-field');
    const regularFields = document.querySelectorAll('.regular-fields');
    const requiredFields = document.querySelectorAll('#id_purchase_price, #id_sale_price');

    function toggleFields() {
        const isGranel = isBulkCheckbox.checked;
        
        // Mostrar/ocultar campos
        bulkConfigFields.forEach(field => {
            field.classList.toggle('hidden', !isGranel);
        });
        
        regularFields.forEach(field => {
            field.classList.toggle('hidden', isGranel);
        });

        // Manejar campos requeridos
        requiredFields.forEach(field => {
            field.required = !isGranel;
        });
    }

    if (isBulkCheckbox) {
        isBulkCheckbox.addEventListener('change', toggleFields);
        toggleFields();  // Estado inicial
    }
});