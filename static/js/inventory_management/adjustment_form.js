document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('adjustmentForm');
    const cancelButton = document.querySelector('.cancel-button');

    if (form) {
        form.addEventListener('submit', function(e) {
            const quantityDiff = document.getElementById('id_quantity_difference').value;
            const justification = document.getElementById('id_justification').value;

            if (!quantityDiff || !justification.trim()) {
                e.preventDefault();
                alert('Por favor complete todos los campos requeridos');
                return;
            }

            if (!confirm('¿Está seguro de crear este ajuste?')) {
                e.preventDefault();
            }
        });
    }

    if (cancelButton) {
        cancelButton.addEventListener('click', function() {
            if (confirm('¿Está seguro de cancelar? Se perderán los cambios no guardados.')) {
                window.history.back();
            }
        });
    }
});