from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import render
from .reports import ReportGenerator
from calendar import month_name
from sales.models import Sale  
from expenses.models import Expense  
from django.db.models import Sum, F, Count, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate
from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from products.models import Product

class ReportExportView(LoginRequiredMixin, View):
    def get(self, request):
        # Vista para mostrar el formulario de exportación
        months = [(str(i), month_name[i]) for i in range(1, 13)]
        years = range(timezone.now().year - 2, timezone.now().year + 1)
        
        context = {
            'months': months,
            'years': years
        }
        return render(request, 'financial_reports/export.html', context)

    def post(self, request):
        # Procesar la exportación
        report_type = request.POST.get('report_type')
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        export_format = request.POST.get('format', 'pdf')

        generator = ReportGenerator()
        data = generator.get_report_data(report_type, date_from, date_to)

        if export_format == 'pdf':
            buffer = generator.generate_pdf(data, report_type, date_from, date_to)
            response = HttpResponse(buffer, content_type='application/pdf')
            filename = f'reporte_{report_type}_{timezone.now().strftime("%Y%m%d")}.pdf'
        else:
            buffer = generator.generate_excel(data, report_type, date_from, date_to)
            response = HttpResponse(
                buffer,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            filename = f'reporte_{report_type}_{timezone.now().strftime("%Y%m%d")}.xlsx'

        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

class FinancialDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'financial_reports/dashboard.html'

    def get_period_dates(self, period):
        today = datetime.now().date()
        if period == '1M':
            start_date = today - relativedelta(months=1)
            period_display = 'Último mes'
        elif period == '3M':
            start_date = today - relativedelta(months=3)
            period_display = 'Últimos 3 meses'
        elif period == '6M':
            start_date = today - relativedelta(months=6)
            period_display = 'Últimos 6 meses'
        elif period == '12M':
            start_date = today - relativedelta(months=12)
            period_display = 'Último año'
        else:  # MAX
            start_date = None
            period_display = 'Todo el período'
        
        return start_date, today, period_display

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        # Obtener período seleccionado
        period = self.request.GET.get('period', '1M')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if not (date_from and date_to):
            start_date, end_date, period_display = self.get_period_dates(period)
        else:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            period_display = f'{start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}'

        # Obtener las ventas
        sales_query = Sale.objects.filter(status='COMPLETED')
        if date_from:
            sales_query = sales_query.filter(date__gte=date_from)
        if date_to:
            sales_query = sales_query.filter(date__lte=date_to)

        # Ventas totales y neto
        ventas_totales = sales_query.aggregate(
            total=Sum('total'),
            comisiones=Sum('commission_amount')
        )
        total_ventas = Decimal(str(ventas_totales['total'] or 0))
        neto_ventas = round(total_ventas / Decimal('1.19'))
        iva_total = total_ventas - neto_ventas

        # Cálculo de costos y utilidad
        costo_total = Decimal('0')
        utilidad_total = Decimal('0')
        for sale in sales_query:
            utilidad_total += Decimal(str(sale.calculate_net_profit()))
            for detail in sale.saledetail_set.all():
                product = detail.product
                if hasattr(detail, 'is_bulk') and detail.is_bulk:
                    # Para ventas a granel
                    if product.has_bulk_sales:
                        # Usar el costo promedio ponderado si está disponible
                        weighted_cost = product.calculate_weighted_average_cost()
                        costo_unitario = weighted_cost if weighted_cost > 0 else product.current_purchase_price
                    else:
                        costo_unitario = detail.purchase_price
                else:
                    # Para ventas normales por unidad
                    costo_unitario = detail.purchase_price

                # Sumar al costo total
                if costo_unitario:
                    costo_total += Decimal(str(detail.quantity)) * Decimal(str(costo_unitario))

        # Gastos operacionales
        gastos_query = Expense.objects.all()
        if date_from:
            gastos_query = gastos_query.filter(date__gte=date_from)
        if date_to:
            gastos_query = gastos_query.filter(date__lte=date_to)
        gastos_operacionales = gastos_query.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Utilidad operacional
        utilidad_operacional = utilidad_total - gastos_operacionales
        margen_operacional = round((utilidad_operacional / neto_ventas * 100), 1) if neto_ventas > 0 else Decimal('0')

        # Calcular ganancias brutas de las ventas
        ganancias_brutas = Decimal('0')
        for sale in sales_query:
            ganancias_brutas += Decimal(str(sale.calculate_net_profit()))

        # Calcular margen de ganancia bruta
        margen_ganancias = round((ganancias_brutas / neto_ventas * 100), 1) if neto_ventas > 0 else Decimal('0')

        # Cálculo separado del IVA de ventas
        iva_total = sum(Decimal(str(sale.get_iva_venta())) for sale in sales_query)

         # Obtener las comisiones totales incluyendo IVA
        comisiones_netas = Decimal(str(ventas_totales['comisiones'] or 0))
        comisiones_totales = round(comisiones_netas * Decimal('1.19'))

        # Cálculos para Costo de Ventas con neto
        costo_bruto = costo_total  # el que ya teníamos
        costo_neto = round(costo_bruto / Decimal('1.19'))

        # Cálculos de IVA
        iva_debito = round(total_ventas - neto_ventas)
        iva_credito = round(costo_bruto - costo_neto)
        iva_pagar = round(iva_debito - iva_credito)

        # Obtener todos los productos activos
        products = Product.objects.filter(is_active=True)
        
        # Calcular valorizaciones totales
        total_sale_gross = sum(p.get_stock_valuation_sale_gross() for p in products)
        total_sale_net = sum(p.get_stock_valuation_sale_net() for p in products)
        total_purchase_gross = sum(p.get_stock_valuation_purchase_gross() for p in products)
        total_purchase_net = sum(p.get_stock_valuation_purchase_net() for p in products)
        
        # Calcular ganancia proyectada
        ganancia_proyectada = total_sale_net - total_purchase_net
        margen_proyectado = int((ganancia_proyectada / total_sale_net * 100) if total_sale_net > 0 else 0)
        
        context['inventory_valuation'] = {
            'sale_gross': total_sale_gross,
            'sale_net': total_sale_net,
            'purchase_gross': total_purchase_gross,
            'purchase_net': total_purchase_net,
            'ganancia_proyectada': ganancia_proyectada,
            'margen_proyectado': margen_proyectado
        }
        
        context.update({
            'current_period': period,
            'period_display': period_display,
            'income_statement': {
                'income': {
                    'total_sales': int(total_ventas),
                    'net_sales': int(neto_ventas),
                },
                'costs': {
                    'products_cost': int(costo_bruto),
                    'products_cost_net': int(costo_neto),
                    'commissions': int(ventas_totales['comisiones'] or 0),
                },
                'expenses': {
                    'total': int(gastos_operacionales),
                },
                'profitability': {
                    'operating_profit': int(utilidad_operacional),
                    'operating_margin': float(margen_operacional),
                    'gross_profit': int(ganancias_brutas),
                    'gross_margin': float(margen_ganancias)
                },
                'tax_info': {
                    'iva_debito': int(iva_debito),
                    'iva_credito': int(iva_credito),
                    'iva_pagar': int(iva_pagar),
                    'comisiones_total': int(comisiones_totales)
                },
                'profitability': {
                    'operating_profit': int(utilidad_operacional),  # Esta es utilidad operacional (con gastos)
                    'operating_margin': float(margen_operacional),
                    'gross_profit': int(ganancias_brutas),     # Esta es la ganancia bruta (sin gastos)
                    'gross_margin': float(margen_ganancias)
                }
            },
            'sales_trends': list(sales_query.annotate(
                fecha=TruncDate('date')
            ).values('fecha').annotate(
                total_ventas=Sum('total')
            ).order_by('fecha')),
            'expense_analysis': list(gastos_query.values('category__name').annotate(
                total=Sum('amount')
            ).order_by('-total')),
            'sales_by_user': list(sales_query.values(
                'user__username'
            ).annotate(
                total_ventas=Sum('total'),
                cantidad_ventas=Count('id')
            ).order_by('-total_ventas'))
        })

        return context

class TrendsView(LoginRequiredMixin, TemplateView):
    template_name = 'financial_reports/trends.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        generator = ReportGenerator()
        context['detailed_trends'] = {
            'sales': generator.get_report_data('sales_detail', date_from, date_to),
            'expenses': generator.get_report_data('expense_detail', date_from, date_to),
            'profitability': generator.get_report_data('profitability', date_from, date_to)
        }

        return context
    
class KPIsView(LoginRequiredMixin, TemplateView):
    template_name = 'financial_reports/kpis.html'  # Asegúrate de crear este template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        generator = ReportGenerator()

        # Obtener datos para los KPIs
        context.update({
            'sales_kpi': generator.get_report_data('sales_kpi', date_from, date_to),
            'expense_kpi': generator.get_report_data('expense_kpi', date_from, date_to),
            'profit_kpi': generator.get_report_data('profit_kpi', date_from, date_to),
            'customer_satisfaction_kpi': generator.get_report_data('customer_satisfaction_kpi', date_from, date_to),
        })

        return context
    
class ComparisonView(LoginRequiredMixin, TemplateView):
    template_name = 'financial_reports/comparisons.html'  # Asegúrate de crear este template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        generator = ReportGenerator()

        # Obtener datos para las comparaciones
        context.update({
            'sales_comparison': generator.get_report_data('sales_comparison', date_from, date_to),
            'expense_comparison': generator.get_report_data('expense_comparison', date_from, date_to),
            'profit_comparison': generator.get_report_data('profit_comparison', date_from, date_to),
        })

        return context
    




