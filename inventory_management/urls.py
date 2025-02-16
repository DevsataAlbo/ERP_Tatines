from django.urls import path
from . import views

app_name = 'inventory_management'

urlpatterns = [
    # Vista principal - Lista de inventarios
    path('', views.InventoryCountListView.as_view(), name='list'),
    
    # Creación y gestión de inventarios
    path('create/', views.InventoryCountCreateView.as_view(), name='create'),
    path('<int:pk>/', views.InventoryCountDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.InventoryCountUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.InventoryCountDeleteView.as_view(), name='delete'),
    
    # Conteo de productos
    path('<int:pk>/count/', views.InventoryCountProcessView.as_view(), name='count_process'),
    path('api/save-count/', views.SaveCountView.as_view(), name='save_count'),
    path('api/search-products/', views.SearchProductsView.as_view(), name='search_products'),
    path('api/dashboard-data/', views.DashboardDataView.as_view(), name='dashboard_data'),  
    
    # Ajustes de inventario
    path('<int:pk>/adjustments/', views.InventoryAdjustmentListView.as_view(), name='adjustments'),
    path('<int:pk>/adjustments/create/', views.InventoryAdjustmentCreateView.as_view(), name='create_adjustment'),
    path('adjustments/<int:pk>/approve/', views.ApproveAdjustmentView.as_view(), name='approve_adjustment'),
    
    # Reportes
    path('<int:pk>/report/', views.InventoryReportView.as_view(), name='report'),
    path('dashboard/', views.InventoryDashboardView.as_view(), name='dashboard'),

    path('<int:pk>/start/', views.StartCountView.as_view(), name='start_count'),

    # En inventory_management/urls.py
    path('<int:pk>/pause/', views.PauseInventoryView.as_view(), name='pause_inventory'),
    path('<int:pk>/finish/', views.FinishInventoryView.as_view(), name='finish_inventory'),

    # Agregar estas nuevas URLs
    path('<int:pk>/edit/', views.EditCompleteInventoryView.as_view(), name='edit_inventory'),
    path('detail/<int:detail_id>/edit/', views.EditInventoryDetailView.as_view(), name='edit_detail'),

    path('api/export-problematic-products/', views.ExportProblematicProductsView.as_view(), name='export_problematic'),

    path('<int:pk>/adjustments/process/', views.ProcessInventoryAdjustmentsView.as_view(), name='process_adjustments'),
         
    path('api/apply-adjustments/', views.ApplyAdjustmentsView.as_view(), name='apply_adjustments'),
]