# sales/urls.py
from django.urls import path, include
from . import views, api
from .views import SaleCancelConfirmationView, SaleEditView

app_name = 'sales'

urlpatterns = [
    path('', views.SaleListView.as_view(), name='list'),
    path('create/', views.SaleCreateView.as_view(), name='create'),
    path('detail/<int:pk>/', views.SaleDetailView.as_view(), name='detail'),
    path('update-status/<int:pk>/', views.SaleUpdateStatusView.as_view(), name='update_status'),
    path('cancel/<int:pk>/confirm/', views.SaleCancelConfirmationView.as_view(), name='cancel_confirmation'),
    path('edit/<int:pk>/', views.SaleEditView.as_view(), name='edit'),

    
    path('api/products/search/', api.search_products, name='search_products'),
    path('api/cart/add/', api.add_to_cart, name='add_to_cart'),
    path('api/cart/update/', api.update_cart, name='update_cart'),
    path('api/cart/remove/<int:product_id>/', api.remove_from_cart, name='remove_from_cart'),
    path('api/cart/init/', api.init_cart, name='init_cart'),
]