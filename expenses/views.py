from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum, Count
from calendar import month_name
from .models import Expense, Category, MonthlyClose
from .forms import ExpenseForm, CategoryForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View, TemplateView
import json

class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'expenses/list.html'
    context_object_name = 'expenses'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date = timezone.now()
        
        # Obtener estado del mes
        context['month_status'] = Expense.get_month_status(
            current_date.year,
            current_date.month
        )
        context['current_month'] = current_date.strftime('%B %Y')
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        category = self.request.GET.get('category')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        order = self.request.GET.get('order')

        if category:
            queryset = queryset.filter(category_id=category)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        if order == 'amount':
            queryset = queryset.order_by('-amount')
        elif order == 'amount_asc':
            queryset = queryset.order_by('amount')
        elif order == 'name':
            queryset = queryset.order_by('category__name')
        
        return queryset

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/form.html'
    success_url = reverse_lazy('expenses:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return redirect('expenses:list')

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/form.html'
    success_url = reverse_lazy('expenses:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'expenses/delete.html'
    success_url = reverse_lazy('expenses:list')

    def delete(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('expenses:list')
        
class MonthDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'expenses/month_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs['year']
        month = self.kwargs['month']
        
        # Obtener gastos del mes
        expenses = Expense.objects.filter(
            accounting_year=year,
            accounting_month=month
        ).select_related('category', 'created_by')

        # Verificar si el mes está cerrado
        is_closed = MonthlyClose.objects.filter(year=year, month=month).exists()

        # Cálculos para el resumen
        totals = expenses.aggregate(
            total=Sum('amount'),
            count=Count('id')
        )

        # Datos para el gráfico
        expense_by_category = Expense.objects.filter(
            date__year=year,
            date__month=month
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')

        context.update({
            'year': year,
            'month': month,
            'month_name': month_name[month],
            'expenses': expenses,
            'is_closed': is_closed,
            'total': totals['total'] or 0,
            'count': totals['count'] or 0,
            'iva_total': sum(expense.calculate_tax()['iva'] for expense in expenses),
            'chart_data': json.dumps({
                'labels': [item['category__name'] for item in expense_by_category],
                'values': [item['total'] for item in expense_by_category]
            })
        })

        return context

class MonthlyCloseView(LoginRequiredMixin, View):
    def post(self, request, year, month):
        can_close, message = MonthlyClose.can_close_month(month, year)
        if not can_close:
            messages.error(request, message)
            return redirect('expenses:list')

        # Calcular total del mes
        total = Expense.objects.filter(
            accounting_month=month,
            accounting_year=year
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        MonthlyClose.objects.create(
            month=month,
            year=year,
            closed_by=request.user,
            total_amount=total
        )

        messages.success(request, f'Mes {month}/{year} cerrado correctamente')
        return redirect('expenses:list')

# Vistas de Categorías
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'expenses/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(is_main=False)

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'expenses/category_form.html'
    success_url = reverse_lazy('expenses:category_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'expenses/category_form.html'
    success_url = reverse_lazy('expenses:category_list')

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'expenses/delete.html'
    success_url = reverse_lazy('expenses:category_list')


class HistoricalView(LoginRequiredMixin, TemplateView):
    template_name = 'expenses/historical.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        years_data = []
        
        # Obtener años únicos de los gastos
        years = Expense.objects.dates('date', 'year', order='DESC')
        
        for year in years:
            year_expenses = Expense.objects.filter(date__year=year.year)
            year_total = year_expenses.aggregate(total=Sum('amount'))['total'] or 0
            
            # Datos por mes
            months_data = []
            for month in range(1, 13):
                month_expenses = year_expenses.filter(date__month=month)
                month_total = month_expenses.aggregate(total=Sum('amount'))['total']
                
                if month_total:  # Solo incluir meses con gastos
                    months_data.append({
                        'number': month,
                        'name': month_name[month],
                        'total': month_total,
                        'is_closed': MonthlyClose.objects.filter(
                            year=year.year, 
                            month=month
                        ).exists()
                    })

            # Datos por categoría para el gráfico
            category_totals = year_expenses.values(
                'category__name',
                'category__parent__name'
            ).annotate(
                total=Sum('amount')
            ).order_by('-total')

            # Preparar datos para el gráfico
            chart_data = {
                'labels': [],
                'data': [],
                'colors': [
                    '#4F46E5', '#7C3AED', '#EC4899', '#EF4444', '#F59E0B',
                    '#10B981', '#3B82F6', '#6366F1', '#8B5CF6', '#D946EF'
                ]
            }

            for cat in category_totals:
                parent_name = cat['category__parent__name'] or 'Otros'
                category_name = cat['category__name']
                full_name = f"{parent_name} > {category_name}"
                chart_data['labels'].append(full_name)
                chart_data['data'].append(cat['total'])

            years_data.append({
                'year': year.year,
                'total': year_total,
                'months': months_data,
                'chart_data': chart_data
            })

        context['years'] = years_data
        return context