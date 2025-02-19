// static/js/components/toast.js
class Toast {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'fixed top-4 right-4 z-50 space-y-4';
        document.body.appendChild(this.container);
    }

    show(message, type = 'success', duration = 3000) {
        const toast = document.createElement('div');
        
        // Definir colores según tipo
        const colors = {
            success: 'bg-green-50 border-green-200 text-green-800',
            error: 'bg-red-50 border-red-200 text-red-800',
            warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
            info: 'bg-blue-50 border-blue-200 text-blue-800'
        };

        // Definir iconos según tipo
        const icons = {
            success: '<i class="fas fa-check-circle text-green-500"></i>',
            error: '<i class="fas fa-times-circle text-red-500"></i>',
            warning: '<i class="fas fa-exclamation-circle text-yellow-500"></i>',
            info: '<i class="fas fa-info-circle text-blue-500"></i>'
        };

        // Crear el elemento toast
        toast.className = `transform translate-y-0 opacity-100 transition-all duration-300 ease-in-out 
                          flex items-center p-4 rounded-lg shadow-lg border ${colors[type]}`;
        
        toast.innerHTML = `
            <div class="mr-3">${icons[type]}</div>
            <div class="flex-1">${message}</div>
            <button class="ml-4 hover:opacity-75">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Agregar al contenedor
        this.container.appendChild(toast);

        // Configurar animación de entrada
        requestAnimationFrame(() => {
            toast.style.transform = 'translateY(0)';
            toast.style.opacity = '1';
        });

        // Configurar cierre automático
        const timeout = setTimeout(() => this.close(toast), duration);

        // Configurar botón de cierre
        const closeButton = toast.querySelector('button');
        closeButton.addEventListener('click', () => {
            clearTimeout(timeout);
            this.close(toast);
        });
    }

    close(toast) {
        // Animar salida
        toast.style.transform = 'translateY(-10px)';
        toast.style.opacity = '0';

        // Remover después de la animación
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// Crear instancia global
window.toast = new Toast();