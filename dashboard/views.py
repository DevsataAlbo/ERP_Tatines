from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F, Count, Q, Case, When, FloatField, OuterRef, Subquery, Max
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, SaleDetail
from products.models import Product
from expenses.models import Expense
import json
from django.db import models

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        today = now.date()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Ventas por período
        context['sales_summary'] = {
            'day': Sale.objects.filter(
                date__date=today,
                status='COMPLETED'
            ).aggregate(
                total=Sum('total'),
                count=Count('id')
            ),
            'week': Sale.objects.filter(
                date__date__gte=today - timedelta(days=7),
                status='COMPLETED'
            ).aggregate(
                total=Sum('total'),
                count=Count('id')
            ),
            'month': Sale.objects.filter(
                date__year=now.year,
                date__month=now.month,
                status='COMPLETED'
            ).aggregate(
                total=Sum('total'),
                count=Count('id')
            ),
            'year': Sale.objects.filter(
                date__year=now.year,
                status='COMPLETED'
            ).aggregate(
                total=Sum('total'),
                count=Count('id')
            ),
        }

        # Productos más vendidos por período
        context['top_products'] = {
            'day': self.get_top_products(today),
            'week': self.get_top_products(today - timedelta(days=7)),
            'month': self.get_top_products(today.replace(day=1)),
            'year': self.get_top_products(today.replace(month=1, day=1))
        }

        # Datos financieros del mes
        sales = Sale.objects.filter(
            date__month=now.month,
            status='COMPLETED'
        )
        
        total_sales = sales.aggregate(total=Sum('total'))['total'] or 0
        costs = sales.aggregate(
            total=Sum(F('saledetail__quantity') * F('saledetail__purchase_price'))
        )['total'] or 0
        
        expenses = Expense.objects.filter(
            date__month=now.month
        ).aggregate(total=Sum('amount'))['total'] or 0

        operating_profit = total_sales - costs - expenses
        
        context['financial_data'] = {
            'total_sales': int(total_sales),
            'costs': int(costs),
            'expenses': int(expenses),
            'operating_profit': int(operating_profit),
            'margin': int((operating_profit / total_sales * 100) if total_sales > 0 else 0)
        }

        # Datos del gráfico de ventas diarias
        daily_sales = Sale.objects.filter(
            date__year=now.year,
            date__month=now.month,
            status='COMPLETED'
        ).annotate(
            sale_date=TruncDay('date')
        ).values('sale_date').annotate(
            total=Sum('total')
        ).order_by('sale_date')

        # Generar lista de fechas completa del mes actual
        dates_list = []
        daily_totals = {}

        # Crear diccionario con las ventas existentes
        for sale in daily_sales:
            formatted_date = str(int(sale['sale_date'].strftime('%d')))  # Convertimos a int y luego str para quitar ceros
            daily_totals[formatted_date] = int(sale['total'])

        # Generar lista de todos los días del mes hasta hoy
        current_date = start_of_month
        while current_date.date() <= today:
            formatted_date = str(int(current_date.strftime('%d')))  # Convertimos a int y luego str para quitar ceros
            dates_list.append(formatted_date)
            if formatted_date not in daily_totals:
                daily_totals[formatted_date] = 0
            current_date += timedelta(days=1)

        # Preparar datos para el gráfico
        chart_data = {
            'labels': json.dumps(dates_list),
            'data': json.dumps([daily_totals[day] for day in dates_list])
        }
        context['sales_chart_data'] = chart_data

        # Productos sin movimiento con fecha de última venta
        last_sale_date = SaleDetail.objects.filter(
            product=OuterRef('pk')
        ).values('product').annotate(
            last_sale=Max('sale__date')
        ).values('last_sale')

        context['slow_moving_products'] = Product.objects.filter(
            is_active=True
        ).annotate(
            last_sale_date=Subquery(last_sale_date),
            has_sales=models.Exists(
                SaleDetail.objects.filter(product=OuterRef('pk'))
            )
        ).order_by('last_sale_date', 'created')[:10]

        # Productos más y menos rentables
        products_profitability = Product.objects.filter(
            is_active=True
        ).annotate(
            profit_margin=Case(
                When(sale_price__gt=0, 
                     then=(F('sale_price') - F('purchase_price')) * 100.0 / F('sale_price')),
                default=0,
                output_field=FloatField()
            )
        )

        context['most_profitable_products'] = products_profitability.order_by('-profit_margin')[:10]
        context['least_profitable_products'] = products_profitability.order_by('profit_margin')[:10]

        # Productos con stock crítico
        context['critical_stock_products'] = Product.objects.filter(
            is_active=True,
            stock__gt=0,
            stock__lte=5  # Consideramos crítico menos de 5 unidades
        ).order_by('stock')[:10]

        return context

    def get_top_products(self, start_date):
        """Obtiene el producto más vendido desde una fecha dada"""
        return SaleDetail.objects.filter(
            sale__date__gte=start_date,
            sale__status='COMPLETED'
        ).values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_amount=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total_quantity').first()