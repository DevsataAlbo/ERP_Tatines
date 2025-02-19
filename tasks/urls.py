from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # URLs existentes
    path('', views.TaskListView.as_view(), name='task_list'),
    path('create/', views.TaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/update/', views.TaskUpdateView.as_view(), name='task_update'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('<int:pk>/toggle-status/', views.toggle_task_status, name='toggle_status'),
    path('<int:pk>/', views.get_task_detail, name='task_detail'),
    path('<int:pk>/update-position/', views.update_task_position, name='update_position'),
    
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('calendar-events/', views.CalendarEventsView.as_view(), name='calendar_events'),
    path('day-tasks/', views.DayTasksView.as_view(), name='day_tasks'),
    path('<int:pk>/update-date/', views.UpdateTaskDateView.as_view(), name='update_date'),
]