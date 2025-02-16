from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.SupplierListView.as_view(), name='list'),
    path('create/', views.SupplierCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SupplierDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.SupplierUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='delete'),
]