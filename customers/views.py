from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, Avg
from .models import Customer
from .forms import CustomerForm
from sales.models import Sale
from django.db.models.functions import ExtractDay
from django.utils import timezone

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/list.html'
    context_object_name = 'customers'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(rut__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(company_name__icontains=search)
            )
        return queryset

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/form.html'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/form.html'
    
    def get_success_url(self):
        return reverse_lazy('customers:detail', kwargs={'pk': self.object.pk})

class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales = Sale.objects.filter(customer=self.object)
        
        # Estadísticas generales
        stats = sales.aggregate(
            total_spent=Sum('total'),
            total_sales=Count('id'),
            avg_ticket=Avg('total')
        )
        
        # Calcular frecuencia de compra
        purchase_frequency = 0
        if sales.count() >= 2:
            first_sale = sales.earliest('date')
            last_sale = sales.latest('date')
            days_diff = (last_sale.date - first_sale.date).days
            purchase_frequency = round(days_diff / sales.count(), 1)
        
        context.update({
            'total_spent': stats['total_spent'] or 0,
            'total_sales': stats['total_sales'] or 0,
            'avg_ticket': stats['avg_ticket'] or 0,
            'purchase_frequency': purchase_frequency,
            'recent_sales': sales.order_by('-date')
        })
        
        return context

def search_customers(request):
    print("Vista search_customers alcanzada")
    term = request.GET.get('term', '')
    print(f"Término de búsqueda de clientes: {term}")
    
    customers = Customer.objects.filter(is_active=True)
    print(f"Clientes encontrados (pre-filtro): {customers.count()}")
    
    if term:
        customers = customers.filter(
            Q(rut__icontains=term) |
            Q(first_name__icontains=term) |
            Q(last_name__icontains=term) |
            Q(company_name__icontains=term)
        )
        print(f"Clientes encontrados (post-filtro): {customers.count()}")
    
    customers = customers[:10]
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'text': str(customer),
            'rut': customer.rut
        })
    
    print(f"Resultados finales: {results}")
    return JsonResponse(results, safe=False)

def customer_history_api(request, pk):
    customer = Customer.objects.get(pk=pk)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    sales_query = Sale.objects.filter(customer=customer)
    
    if date_from:
        sales_query = sales_query.filter(date__gte=date_from)
    if date_to:
        sales_query = sales_query.filter(date__lte=date_to)
    
    # Calcular métricas
    metrics = {
        'total_sales': sales_query.count(),
        'total_spent': sales_query.aggregate(total=Sum('total'))['total'] or 0,
        'avg_ticket': sales_query.aggregate(avg=Avg('total'))['avg'] or 0,
    }
    
    # Calcular frecuencia de compra
    if sales_query.count() >= 2:
        first_sale = sales_query.earliest('date')
        last_sale = sales_query.latest('date')
        days_diff = (last_sale.date - first_sale.date).days
        metrics['purchase_frequency'] = round(days_diff / sales_query.count(), 1)
    else:
        metrics['purchase_frequency'] = 0
    
    # Preparar datos de ventas
    sales_data = []
    for sale in sales_query.order_by('-date'):
        sales_data.append({
            'id': sale.id,
            'date': sale.date,
            'number': sale.number,
            'items': sale.get_total_items(),
            'total': sale.total,
            'status': sale.status,
            'status_display': sale.get_status_display()
        })
    
    return JsonResponse({
        'metrics': metrics,
        'sales': sales_data
    })

def get_customer_by_id(request, pk):
    try:
        customer = Customer.objects.get(pk=pk, is_active=True)
        return JsonResponse({
            'id': customer.id,
            'text': str(customer),
            'rut': customer.rut
        })
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)

















