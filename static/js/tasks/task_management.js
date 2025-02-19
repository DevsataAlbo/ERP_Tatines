// Inicializar Sortable
document.addEventListener('DOMContentLoaded', function() {
    const taskList = document.getElementById('taskList');
    if (taskList) {
        new Sortable(taskList, {
            animation: 150,
            ghostClass: 'bg-gray-100',
            onEnd: function(evt) {
                const taskId = evt.item.dataset.taskId;
                const newIndex = evt.newIndex;
                
                updateTaskPosition(taskId, newIndex);
            }
        });
    }
});

// Función para actualizar la posición
async function updateTaskPosition(taskId, newPosition) {
    try {
        const response = await fetch(`/tasks/${taskId}/update-position/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                position: newPosition
            })
        });

        if (!response.ok) {
            throw new Error('Error al actualizar la posición');
        }

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        // Opcional: recargar la página si hay un error para restaurar el orden
        // location.reload();
    }
}


// Manejo del modal
function openNewTaskModal(selectedDate = null) {
    document.getElementById('modalTitle').textContent = 'Nueva Tarea';
    document.getElementById('taskForm').reset();
    document.getElementById('taskForm').setAttribute('data-mode', 'create');
    
    // Si hay una fecha seleccionada, establecerla en el input
    if (selectedDate) {
        const formattedDate = new Date(selectedDate).toISOString().slice(0, 16);
        document.getElementById('taskDueDate').value = formattedDate;
    }
    
    document.getElementById('taskModal').classList.remove('hidden');
}

function openEditTaskModal(taskId) {
    document.getElementById('modalTitle').textContent = 'Editar Tarea';
    document.getElementById('taskForm').setAttribute('data-mode', 'edit');
    document.getElementById('taskForm').setAttribute('data-task-id', taskId);
    
    fetch(`/tasks/${taskId}/`)
        .then(response => {
            if (!response.ok) throw new Error('Error al cargar la tarea');
            return response.json();
        })
        .then(task => {
            document.getElementById('taskTitle').value = task.title;
            document.getElementById('taskDescription').value = task.description || '';
            if (task.due_date) {
                // Formatear la fecha para el input datetime-local
                const date = new Date(task.due_date);
                const formattedDate = date.toISOString().slice(0, 16);
                document.getElementById('taskDueDate').value = formattedDate;
            } else {
                document.getElementById('taskDueDate').value = '';
            }
            document.getElementById('taskPriority').value = task.priority;
            document.getElementById('taskModal').classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cargar los datos de la tarea');
        });
}

function closeTaskModal() {
    document.getElementById('taskModal').classList.add('hidden');
}

// Manejo de formulario
document.getElementById('taskForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const mode = this.getAttribute('data-mode');
    const taskId = this.getAttribute('data-task-id');
    
    let url = '/tasks/create/';
    let method = 'POST';
    
    if (mode === 'edit') {
        url = `/tasks/${taskId}/update/`;
    }

    // Convertir FormData a un objeto
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.errors || 'Error al guardar la tarea');
        }
        
        const result = await response.json();
        if (result.success) {
            alert(result.message);
            location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'Error al guardar la tarea');
    }
});

// Cambiar estado de tarea
async function toggleTaskStatus(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}/toggle-status/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        if (!response.ok) throw new Error('Network response was not ok');
        
        location.reload();
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cambiar el estado de la tarea');
    }
}

// Eliminar tarea
async function deleteTask(taskId) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta tarea?')) return;
    
    try {
        const response = await fetch(`/tasks/${taskId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        if (!response.ok) throw new Error('Network response was not ok');
        
        location.reload();
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar la tarea');
    }
}

// Utilidad para obtener el token CSRF
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

// Cerrar modal al hacer clic fuera
document.getElementById('taskModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeTaskModal();
    }
});