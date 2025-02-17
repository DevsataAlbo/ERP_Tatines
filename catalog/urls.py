from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.CatalogView.as_view(), name='list'),
    path('config/', views.CatalogConfigView.as_view(), name='config'),
    path('favorites/', views.FavoritesListView.as_view(), name='favorites'),
    path('p/<str:public_url>/', views.CatalogView.as_view(), name='public'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('favorites/add/', views.add_favorite, name='add_favorite'),
    path('favorites/remove/<int:product_id>/', views.remove_favorite, name='remove_favorite'),
]