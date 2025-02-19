// static/js/tasks/task_filters.js

document.addEventListener('DOMContentLoaded', function() {
    // Obtener referencias a los elementos de filtro
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const sortOrder = document.getElementById('sortOrder');
    const dateFrom = document.getElementById('dateFrom');
    const dateTo = document.getElementById('dateTo');

    // Restaurar valores de filtros desde localStorage
    restoreFilters();

    // Debounce para la búsqueda
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            saveFilters();
            applyFilters();
        }, 300);
    });

    // Eventos para filtros de selección
    [statusFilter, priorityFilter, sortOrder, dateFrom, dateTo].forEach(filter => {
        filter.addEventListener('change', () => {
            saveFilters();
            applyFilters();
        });
    });

    // Función principal de filtrado
    function applyFilters() {
        const tasks = document.querySelectorAll('.task-item');
        const searchTerm = searchInput.value.toLowerCase();
        const status = statusFilter.value;
        const priority = priorityFilter.value;
        const from = dateFrom.value;
        const to = dateTo.value;

        let visibleCount = 0;

        tasks.forEach(task => {
            let visible = true;

            // Filtro de búsqueda
            if (searchTerm) {
                const title = task.querySelector('h3').textContent.toLowerCase();
                const description = task.querySelector('p')?.textContent.toLowerCase() || '';
                visible = visible && (title.includes(searchTerm) || description.includes(searchTerm));
            }

            // Filtro de estado
            if (status) {
                visible = visible && task.dataset.status === status;
            }

            // Filtro de prioridad
            if (priority) {
                visible = visible && task.dataset.priority === priority;
            }

            // Filtro de fechas
            if (from || to) {
                const taskDate = task.dataset.dueDate;
                if (taskDate) {
                    if (from && taskDate < from) visible = false;
                    if (to && taskDate > to) visible = false;
                }
            }

            // Aplicar visibilidad
            task.classList.toggle('hidden', !visible);
            if (visible) visibleCount++;
        });

        // Ordenar tareas visibles
        const taskList = document.getElementById('taskList');
        const tasksArray = Array.from(tasks).filter(task => !task.classList.contains('hidden'));
        
        tasksArray.sort((a, b) => {
            switch (sortOrder.value) {
                case 'created_desc':
                    return new Date(b.dataset.created) - new Date(a.dataset.created);
                case 'created_asc':
                    return new Date(a.dataset.created) - new Date(b.dataset.created);
                case 'due_date_asc':
                    const dateA = a.dataset.dueDate || '9999-12-31';
                    const dateB = b.dataset.dueDate || '9999-12-31';
                    return new Date(dateA) - new Date(dateB);
                case 'due_date_desc':
                    const dateC = a.dataset.dueDate || '0000-01-01';
                    const dateD = b.dataset.dueDate || '0000-01-01';
                    return new Date(dateD) - new Date(dateC);
                case 'priority_desc':
                    return getPriorityWeight(b.dataset.priority) - getPriorityWeight(a.dataset.priority);
                case 'priority_asc':
                    return getPriorityWeight(a.dataset.priority) - getPriorityWeight(b.dataset.priority);
                default:
                    return 0;
            }
        });

        // Reordenar el DOM
        tasksArray.forEach(task => taskList.appendChild(task));

        // Mostrar/ocultar mensaje de no resultados
        const noResultsMessage = document.querySelector('.text-center.py-12');
        if (noResultsMessage) {
            if (visibleCount === 0) {
                noResultsMessage.classList.remove('hidden');
            } else {
                noResultsMessage.classList.add('hidden');
            }
        }
    }

    // Función auxiliar para el peso de las prioridades
    function getPriorityWeight(priority) {
        return {
            'high': 3,
            'medium': 2,
            'low': 1
        }[priority] || 0;
    }

    // Función para guardar filtros en localStorage
    function saveFilters() {
        const filters = {
            search: searchInput.value,
            status: statusFilter.value,
            priority: priorityFilter.value,
            sortOrder: sortOrder.value,
            dateFrom: dateFrom.value,
            dateTo: dateTo.value
        };
        localStorage.setItem('taskFilters', JSON.stringify(filters));
    }

    // Función para restaurar filtros desde localStorage
    function restoreFilters() {
        try {
            const savedFilters = JSON.parse(localStorage.getItem('taskFilters'));
            if (savedFilters) {
                searchInput.value = savedFilters.search || '';
                statusFilter.value = savedFilters.status || '';
                priorityFilter.value = savedFilters.priority || '';
                sortOrder.value = savedFilters.sortOrder || 'created_desc';
                dateFrom.value = savedFilters.dateFrom || '';
                dateTo.value = savedFilters.dateTo || '';
                
                if (savedFilters.search || savedFilters.status || 
                    savedFilters.priority || savedFilters.dateFrom || 
                    savedFilters.dateTo) {
                    applyFilters();
                }
            }
        } catch (error) {
            console.error('Error al restaurar filtros:', error);
            localStorage.removeItem('taskFilters');
        }
    }

    // Aplicar filtros iniciales
    applyFilters();
});