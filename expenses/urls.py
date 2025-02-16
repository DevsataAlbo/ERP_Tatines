from django.urls import path, include
from . import views

app_name = 'expenses'

# expenses/urls.py
urlpatterns = [
    path('', views.ExpenseListView.as_view(), name='list'),
    path('create/', views.ExpenseCreateView.as_view(), name='create'),
    path('update/<int:pk>/', views.ExpenseUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', views.ExpenseDeleteView.as_view(), name='delete'),
    path('historical/', views.HistoricalView.as_view(), name='historical'),
    path('month/<int:year>/<int:month>/', views.MonthDetailView.as_view(), name='month_detail'),
    path('close/<int:year>/<int:month>/', views.MonthlyCloseView.as_view(), name='close_month'),
    path('category/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('category/update/<int:pk>/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('category/delete/<int:pk>/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
]