// static/js/tasks/calendar_view.js

document.addEventListener('DOMContentLoaded', function() {
    let calendar;
    
    // Inicializar el calendario
    initializeCalendar();
    
    // Inicializar botones de vista
    initializeViewButtons();

    function initializeCalendar() {
        const calendarEl = document.getElementById('calendar');
        if (!calendarEl) return;

        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'es',
            firstDay: 1, // Lunes como primer día
            selectable: true,
            editable: true,
            dayMaxEvents: true,
            height: 'auto',
            
            // Eventos del calendario
            events: '/tasks/calendar-events/',
            
            // Personalización de eventos
            eventDidMount: function(info) {
                // Añadir clase según prioridad
                info.el.classList.add(`priority-${info.event.extendedProps.priority}`);
                
                // Marcar tareas completadas
                if (info.event.extendedProps.status === 'completed') {
                    info.el.classList.add('task-completed');
                }
            },
            
            // Handlers de interacción
            dateClick: function(info) {
                handleDateClick(info);
            },
            
            eventClick: function(info) {
                handleEventClick(info);
            },
            
            eventDrop: function(info) {
                handleEventDrop(info);
            },
            
            select: function(info) {
                handleDateSelect(info);
            }
        });

        calendar.render();

        // Cargar tareas del día actual al iniciar
        updateSelectedDayTasks(new Date());
    }

    function initializeViewButtons() {
        // Botones de navegación
        document.getElementById('prevButton')?.addEventListener('click', () => {
            calendar.prev();
            updateSelectedDayTasks();
        });

        document.getElementById('nextButton')?.addEventListener('click', () => {
            calendar.next();
            updateSelectedDayTasks();
        });

        document.getElementById('todayButton')?.addEventListener('click', () => {
            calendar.today();
            updateSelectedDayTasks();
        });

        // Botones de vista
        document.getElementById('monthView')?.addEventListener('click', () => {
            toggleViewButton('monthView');
            calendar.changeView('dayGridMonth');
        });

        document.getElementById('weekView')?.addEventListener('click', () => {
            toggleViewButton('weekView');
            calendar.changeView('timeGridWeek');
        });
    }

    function toggleViewButton(activeId) {
        const buttons = ['monthView', 'weekView'];
        buttons.forEach(id => {
            const button = document.getElementById(id);
            if (button) {
                if (id === activeId) {
                    button.classList.add('bg-white', 'shadow');
                    button.classList.remove('hover:bg-white');
                } else {
                    button.classList.remove('bg-white', 'shadow');
                    button.classList.add('hover:bg-white');
                }
            }
        });
    }

    // Manejadores de eventos
    function handleDateClick(info) {
        const date = info.date;
        openNewTaskModal(date);
        updateSelectedDayTasks(date);
    }

    function handleEventClick(info) {
        const taskId = info.event.id;
        openEditTaskModal(taskId);
    }

    async function handleEventDrop(info) {
        const taskId = info.event.id;
        const newDate = info.event.start;

        try {
            const response = await fetch(`/tasks/${taskId}/update-date/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    due_date: newDate.toISOString()
                })
            });

            if (!response.ok) {
                throw new Error('Error al actualizar la fecha');
            }

            alert('Fecha actualizada correctamente');
            updateSelectedDayTasks();
        } catch (error) {
            console.error('Error:', error);
            info.revert();
            alert('Error al actualizar la fecha');
        }
    }

    function handleDateSelect(info) {
        const startDate = info.start;
        const endDate = info.end;
        
        // Si la selección es en el mismo día, abrir modal de nueva tarea
        if (startDate.toDateString() === endDate.toDateString()) {
            openNewTaskModal(startDate);
        }
        // Si es un rango, abrir modal con fechas preseleccionadas
        else {
            openNewTaskModal(startDate, endDate);
        }
    }

    // Actualizar panel lateral
    async function updateSelectedDayTasks(date = null) {
        const selectedDate = date || calendar.getDate();
        const container = document.getElementById('selectedDayTasks');
        if (!container) return;
        
        try {
            const response = await fetch(`/tasks/day-tasks/?date=${selectedDate.toISOString()}`);
            if (!response.ok) throw new Error('Error al cargar las tareas');
            
            const tasks = await response.json();
            renderDayTasks(tasks);
        } catch (error) {
            console.error('Error:', error);
            container.innerHTML = '<p class="text-gray-500">Error al cargar las tareas</p>';
        }
    }

    function renderDayTasks(tasks) {
        const container = document.getElementById('selectedDayTasks');
        if (!container) return;
        
        if (tasks.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No hay tareas para este día</p>';
            return;
        }

        container.innerHTML = tasks.map(task => `
            <div class="task-item p-3 bg-gray-50 rounded-lg border-l-4" 
                 style="border-left-color: ${getPriorityColor(task.priority)}">
                <div class="flex items-start justify-between">
                    <div class="flex items-center">
                        <button onclick="toggleTaskStatus('${task.id}')" 
                                class="text-gray-400 hover:text-green-500 mr-2">
                            <i class="fas fa-check-circle ${task.status === 'completed' ? 'text-green-500' : ''}"></i>
                        </button>
                        <div>
                            <h4 class="font-medium ${task.status === 'completed' ? 'line-through text-gray-500' : ''}">${task.title}</h4>
                            <p class="text-sm text-gray-600">${formatTime(task.due_date)}</p>
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="openEditTaskModal('${task.id}')" 
                                class="text-gray-400 hover:text-blue-500">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Funciones auxiliares
    function getPriorityColor(priority) {
        return {
            'high': '#EF4444',
            'medium': '#F59E0B',
            'low': '#22C55E'
        }[priority] || '#3B82F6';
    }

    function formatTime(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
    }
});

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