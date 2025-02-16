from django.urls import path
from . import views

app_name = 'financial_reports'

urlpatterns = [
    path('', views.FinancialDashboardView.as_view(), name='dashboard'),
    path('trends/', views.TrendsView.as_view(), name='trends'),
    path('kpis/', views.KPIsView.as_view(), name='kpis'),
    path('comparisons/', views.ComparisonView.as_view(), name='comparisons'),
    path('export/', views.ReportExportView.as_view(), name='export'),
]