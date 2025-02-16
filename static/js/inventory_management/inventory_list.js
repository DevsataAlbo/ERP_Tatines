document.addEventListener('DOMContentLoaded', function() {
    // Función para inicializar las barras de progreso
    function initializeProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar-fill');
        progressBars.forEach(bar => {
            const percentage = bar.dataset.progress || 0;
            // Usamos requestAnimationFrame para una animación suave
            requestAnimationFrame(() => {
                bar.style.transition = 'width 0.5s ease-out';
                bar.style.width = `${percentage}%`;
            });
        });
    }

    // Resto de funciones del archivo...
    function updatePaginationLinks() {
        const searchParams = new URLSearchParams(window.location.search);
        const paginationLinks = document.querySelectorAll('.pagination-container a');
        
        paginationLinks.forEach(link => {
            const url = new URL(link.href);
            searchParams.forEach((value, key) => {
                if (key !== 'page') {
                    url.searchParams.set(key, value);
                }
            });
            link.href = url.toString();
        });
    }

    function initializeFilters() {
        const filterForm = document.querySelector('.filter-form');
        if (filterForm) {
            filterForm.addEventListener('submit', function(e) {
                const pageInput = document.querySelector('input[name="page"]');
                if (pageInput) {
                    pageInput.value = '1';
                }
            });
        }
    }

    // Inicialización de todas las funcionalidades
    initializeProgressBars();
    updatePaginationLinks();
    initializeFilters();
});