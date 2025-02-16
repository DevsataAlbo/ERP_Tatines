document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('supplierForm');
    
    if (form) {
        // Formateo automático del RUT
        const rutInput = form.querySelector('input[name="rut"]');
        if (rutInput) {
            rutInput.addEventListener('input', function(e) {
                let value = e.target.value;
                
                // Eliminar todo excepto números y K
                value = value.replace(/[^\dK]/gi, '');
                
                // Formatear el RUT
                if (value.length > 1) {
                    let result = value.slice(-1); // Obtener dígito verificador
                    let rut = value.slice(0, -1); // Obtener el resto del RUT
                    
                    // Agregar puntos
                    while (rut.length > 3) {
                        result = '.' + rut.slice(-3) + result;
                        rut = rut.slice(0, -3);
                    }
                    if (rut.length > 0) {
                        result = rut + result;
                    }
                    
                    // Agregar guión antes del dígito verificador
                    if (value.length > 1) {
                        result = result.slice(0, -1) + '-' + result.slice(-1);
                    }
                    
                    e.target.value = result;
                }
            });
        }

        // Formateo del teléfono
        const phoneInputs = form.querySelectorAll('input[name="phone"], input[name="alternative_phone"]');
        phoneInputs.forEach(input => {
            input.addEventListener('input', function(e) {
                let value = e.target.value;
                
                // Eliminar todo excepto números y +
                value = value.replace(/[^\d+]/g, '');
                
                // Asegurar que comience con +56
                if (!value.startsWith('+')) {
                    value = '+' + value;
                }
                if (!value.startsWith('+56') && value.length > 1) {
                    value = '+56' + value.substring(1);
                }
                
                e.target.value = value;
            });
        });

        // Validación antes de enviar
        form.addEventListener('submit', function(e) {
            const requiredFields = ['name', 'rut', 'phone', 'email', 'address', 'city', 'region'];
            let hasError = false;

            requiredFields.forEach(field => {
                const input = form.querySelector(`[name="${field}"]`);
                if (!input.value.trim()) {
                    const errorDiv = input.parentElement.querySelector('.text-red-500');
                    if (!errorDiv) {
                        const error = document.createElement('p');
                        error.className = 'text-red-500 text-xs mt-1';
                        error.textContent = 'Este campo es requerido';
                        input.parentElement.appendChild(error);
                    }
                    hasError = true;
                }
            });

            if (hasError) {
                e.preventDefault();
                window.scrollTo(0, 0);
            }
        });
    }
});