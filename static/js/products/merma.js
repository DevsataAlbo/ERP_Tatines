document.addEventListener('DOMContentLoaded', function() {
    const mermaModal = document.getElementById('mermaModal');
    const openMermaButton = document.getElementById('openMermaModal');
    const closeMermaModal = document.getElementById('closeMermaModal');
    const mermaForm = document.getElementById('mermaForm');

    // Abrir modal
    openMermaButton.addEventListener('click', () => {
        mermaModal.classList.remove('hidden');
    });

    // Cerrar modal
    closeMermaModal.addEventListener('click', () => {
        mermaModal.classList.add('hidden');
    });

    // Procesar formulario
    mermaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        try {
            // Obtener el CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            const formData = new FormData(mermaForm);
            
            const response = await fetch(mermaForm.dataset.url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Error en el servidor');
            }

            const data = await response.json();
            
            if (data.status === 'success') {
                alert(data.message);
                window.location.reload();
            } else {
                if (data.errors) {
                    // Mostrar errores específicos
                    const errorMessages = Object.values(data.errors).flat();
                    alert(errorMessages.join('\n'));
                } else {
                    alert(data.message || 'Error al procesar la solicitud');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'Error al procesar la solicitud');
        }
    });
});