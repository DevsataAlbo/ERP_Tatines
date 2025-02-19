from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Task
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from django.views import View
from django.db.models import Q
from django.utils import timezone

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        queryset = Task.objects.filter(created_by=self.request.user)

        # Filtro de búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )

        # Filtro de estado
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filtro de prioridad
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Filtro de fechas
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            queryset = queryset.filter(due_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(due_date__lte=date_to)

        # Ordenamiento
        sort_order = self.request.GET.get('sort', 'created_desc')
        sort_mapping = {
            'created_desc': '-created_at',
            'created_asc': 'created_at',
            'due_date_asc': 'due_date',
            'due_date_desc': '-due_date',
            'priority_desc': '-priority',
            'priority_asc': 'priority'
        }
        
        order_by = sort_mapping.get(sort_order, '-created_at')
        queryset = queryset.order_by(order_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'current_filters': {
                'search': self.request.GET.get('search', ''),
                'status': self.request.GET.get('status', ''),
                'priority': self.request.GET.get('priority', ''),
                'date_from': self.request.GET.get('date_from', ''),
                'date_to': self.request.GET.get('date_to', ''),
                'sort': self.request.GET.get('sort', 'created_desc')
            }
        })
        return context

@method_decorator(csrf_exempt, name='dispatch')
class TaskCreateView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            task = Task.objects.create(
                title=data.get('title'),
                description=data.get('description', ''),
                due_date=data.get('due_date'),
                priority=data.get('priority'),
                created_by=request.user
            )
            return JsonResponse({
                'success': True,
                'message': 'Tarea creada correctamente',
                'id': task.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class TaskUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            task = get_object_or_404(Task, pk=pk, created_by=request.user)
            data = json.loads(request.body)
            
            # Actualizar campos
            task.title = data.get('title', task.title)
            task.description = data.get('description', task.description)
            task.due_date = data.get('due_date', task.due_date)
            task.priority = data.get('priority', task.priority)
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Tarea actualizada correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class TaskDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            task = get_object_or_404(Task, pk=pk, created_by=request.user)
            task.delete()
            return JsonResponse({
                'success': True,
                'message': 'Tarea eliminada correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

@login_required
def toggle_task_status(request, pk):
    try:
        task = get_object_or_404(Task, pk=pk, created_by=request.user)
        # Simplificar el toggle: solo entre pending y completed
        task.status = 'completed' if task.status == 'pending' else 'pending'
        task.save()
        return JsonResponse({
            'success': True,
            'status': task.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
@login_required
def get_task_detail(request, pk):
    try:
        task = get_object_or_404(Task, pk=pk, created_by=request.user)
        data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'due_date': task.due_date.isoformat() if task.due_date else None
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
@login_required
def update_task_position(request, pk):
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        
        data = json.loads(request.body)
        new_position = data.get('position')
        
        if new_position is None:
            return JsonResponse({'error': 'Posición no proporcionada'}, status=400)
        
        task = get_object_or_404(Task, pk=pk, created_by=request.user)
        task.position = new_position
        task.save()
        
        # Reordenar todas las tareas para mantener posiciones consecutivas
        tasks = Task.objects.filter(created_by=request.user).order_by('position')
        for index, task in enumerate(tasks):
            if task.position != index:
                task.position = index
                task.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/calendar_view.html'

class CalendarEventsView(LoginRequiredMixin, View):
    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        view_type = request.GET.get('view_type', 'dayGridMonth')

        try:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))

            tasks = Task.objects.filter(
                created_by=request.user,
                due_date__range=(start_date, end_date)
            ).select_related('created_by')

            events = []
            for task in tasks:
                event = {
                    'id': str(task.id),
                    'title': task.title,
                    'start': task.due_date.isoformat(),
                    'end': (task.due_date + timedelta(hours=1)).isoformat(),
                    'allDay': False,
                    'extendedProps': {
                        'description': task.description,
                        'priority': task.priority,
                        'status': task.status
                    }
                }
                events.append(event)

            return JsonResponse(events, safe=False)
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

class DayTasksView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            date_str = request.GET.get('date')
            if not date_str:
                date = timezone.now()
            else:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

            # Obtener el inicio y fin del día
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)

            tasks = Task.objects.filter(
                created_by=request.user,
                due_date__range=(start_date, end_date)
            ).order_by('due_date')

            tasks_data = []
            for task in tasks:
                task_data = {
                    'id': str(task.id),
                    'title': task.title,
                    'description': task.description,
                    'priority': task.priority,
                    'status': task.status,
                    'due_date': task.due_date.isoformat() if task.due_date else None
                }
                tasks_data.append(task_data)

            return JsonResponse(tasks_data, safe=False)
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

class UpdateTaskDateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            task = get_object_or_404(Task, pk=pk, created_by=request.user)
            data = json.loads(request.body)
            
            new_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            task.due_date = new_date
            task.save()

            return JsonResponse({
                'success': True,
                'message': 'Fecha actualizada correctamente'
            })
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)