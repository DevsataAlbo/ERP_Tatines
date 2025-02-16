from django.db import models
from django.db.models import Sum, F, Q
from django.db.models.functions import TruncMonth, TruncYear
from decimal import Decimal
from django.db.models import Count, Avg
from django.utils import timezone
from sales.models import Sale
from expenses.models import Expense

class FinancialReport:
    """Clase de servicio para generar reportes"""
    
    @staticmethod
    def get_income_statement(date_from=None, date_to=None):
        """Estado de Resultados"""
        # Ventas
        sales_data = Sale.objects.filter(status='COMPLETED')
        if date_from:
            sales_data = sales_data.filter(date__gte=date_from)
        if date_to:
            sales_data = sales_data.filter(date__lte=date_to)
            
        # Ingresos
        income = {
            'total_sales': sales_data.aggregate(total=Sum('total'))['total'] or 0,
            'net_sales': sales_data.aggregate(total=Sum('get_neto_venta'))['total'] or 0,
            'sales_tax': sales_data.aggregate(total=Sum('get_iva_venta'))['total'] or 0,
            'sales_by_method': sales_data.values('payment_method').annotate(
                total=Sum('total'),
                count=Count('id')
            ),
        }

        # Costos de Venta
        costs = {
            'products_cost': sales_data.aggregate(
                total=Sum(F('saledetail__quantity') * F('saledetail__product__purchase_price'))
            )['total'] or 0,
            'commissions': sales_data.aggregate(
                total=Sum('get_total_commission')
            )['total'] or 0,
        }

        # Gastos Operacionales
        expenses_data = Expense.objects.all()
        if date_from:
            expenses_data = expenses_data.filter(date__gte=date_from)
        if date_to:
            expenses_data = expenses_data.filter(date__lte=date_to)

        expenses = {
            'total': expenses_data.aggregate(total=Sum('amount'))['total'] or 0,
            'by_category': expenses_data.values('category__name').annotate(
                total=Sum('amount'),
                count=Count('id')
            ),
            'monthly': expenses_data.annotate(
                month=TruncMonth('date')
            ).values('month').annotate(
                total=Sum('amount')
            ).order_by('month')
        }

        # Cálculos de Rentabilidad
        gross_profit = income['net_sales'] - costs['products_cost']
        operating_profit = gross_profit - expenses['total'] - costs['commissions']

        profitability = {
            'gross_profit': gross_profit,
            'gross_margin': (gross_profit / income['net_sales'] * 100) if income['net_sales'] > 0 else 0,
            'operating_profit': operating_profit,
            'operating_margin': (operating_profit / income['net_sales'] * 100) if income['net_sales'] > 0 else 0
        }

        return {
            'income': income,
            'costs': costs,
            'expenses': expenses,
            'profitability': profitability
        }

    @staticmethod
    def get_sales_trends():
        """Tendencias de Ventas"""
        return Sale.objects.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total_sales=Sum('total'),
            average_ticket=Avg('total'),
            total_items=Sum('saledetail__quantity'),
            profit=Sum('calculate_net_profit')
        ).order_by('month')

    @staticmethod
    def get_expense_analysis():
        """Análisis de Gastos"""
        current_year = timezone.now().year
        
        return {
            'by_category': Expense.objects.values('category__name').annotate(
                total=Sum('amount'),
                avg_monthly=Avg('amount'),
                count=Count('id')
            ),
            'trends': Expense.objects.annotate(
                month=TruncMonth('date')
            ).values('month').annotate(
                total=Sum('amount')
            ).order_by('month'),
            'yoy_comparison': Expense.objects.annotate(
                year=TruncYear('date')
            ).values('year').annotate(
                total=Sum('amount')
            ).order_by('year')
        }
    
class TrendAnalysis(FinancialReport):
    """Extiende FinancialReport con análisis específicos de tendencias"""
    
    @classmethod
    def get_detailed_sales_trends(cls, date_from=None, date_to=None):
        """Agrega análisis más detallado a get_sales_trends"""
        base_trends = super().get_sales_trends()
        # Agregar análisis adicionales...
        return base_trends
