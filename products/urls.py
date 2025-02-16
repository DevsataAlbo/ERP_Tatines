from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('create/', views.ProductCreateView.as_view(), name='create'),
    path('detail/<int:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('update/<int:pk>/', views.ProductUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', views.ProductDeleteView.as_view(), name='delete'),
    path('stock/entries/', views.StockEntryListView.as_view(), name='stock_entry_list'),
    path('stock/entries/create/', views.StockEntryCreateView.as_view(), name='stock_entry_create'),
    path('stock/entries/<int:pk>/', views.StockEntryDetailView.as_view(), name='stock_entry_detail'),

    path('open-sack/<int:pk>/', views.OpenSackView.as_view(), name='open_sack'),  
    path('expiring/', views.ExpiringProductsView.as_view(), name='expiring'),
    path('register-merma/<int:pk>/', views.RegisterMermaView.as_view(), name='register_merma'),
    path('history/<int:pk>/', views.ProductMovementHistoryView.as_view(), name='movement_history'),
]