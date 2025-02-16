# payment_providers/urls.py
from django.urls import path
from . import views

app_name = 'payment_providers'

urlpatterns = [
    path('', views.PaymentProviderListView.as_view(), name='list'),
    path('create/', views.PaymentProviderCreateView.as_view(), name='create'),
    path('update/<int:pk>/', views.PaymentProviderUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', views.PaymentProviderDeleteView.as_view(), name='delete'),
]