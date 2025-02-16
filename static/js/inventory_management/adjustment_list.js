document.addEventListener('DOMContentLoaded', function() {
    // Manejar aprobación de ajustes
    const approveButtons = document.querySelectorAll('.approve-button');
    
    approveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const adjustmentId = this.dataset.adjustmentId;
            
            if (confirm('¿Está seguro de que desea aprobar este ajuste?')) {
                approveAdjustment(adjustmentId);
            }
        });
    });

    function approveAdjustment(adjustmentId) {
        fetch(`/inventory/adjustments/${adjustmentId}/approve/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                location.reload();
            } else {
                alert(data.message || 'Error al aprobar el ajuste');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al procesar la solicitud');
        });
    }

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