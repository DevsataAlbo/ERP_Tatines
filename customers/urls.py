from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.CustomerListView.as_view(), name='list'),
    path('create/', views.CustomerCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='edit'),
    path('api/search/', views.search_customers, name='search_customers'),
    path('api/customer/<int:pk>/', views.get_customer_by_id, name='get_customer_by_id'),
]


