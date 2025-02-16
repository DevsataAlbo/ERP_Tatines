from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from .models import Sale, SaleDetail
from products.models import Product, ProductStock
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.views import View
from django.utils import timezone
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal, ROUND_HALF_UP
from django.utils.timezone import now, make_aware
import decimal
import logging
from payment_providers.models import PaymentProvider
from .utils import round_money, calculate_bulk_quantity

# def round_money(value):
#     """
#     Redondea valores monetarios a enteros:
#     - Si el decimal es >= 0.5, redondea hacia arriba
#     - Si el decimal es < 0.5, redondea hacia abajo
#     """
#     return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

# # Funciones auxiliares para cálculos
# def calculate_bulk_quantity(amount, price_per_kilo):
#     """
#     Calcula la cantidad en kilos basada en el monto a vender.
#     Asegura que el monto final sea exactamente el solicitado.
#     """
#     amount = Decimal(str(amount))
#     price_per_kilo = Decimal(str(price_per_kilo))
#     quantity = (amount / price_per_kilo).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
#     return quantity, amount

def format_decimal(value):
    """Formatea un valor decimal para mostrar solo 3 decimales."""
    return Decimal(str(value)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

def format_currency(value):
    """Formatea un valor monetario para mostrar solo 0 decimales."""
    return Decimal(str(value)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)

class SaleListView(LoginRequiredMixin, ListView):
    """Vista para listar todas las ventas con filtros"""
    model = Sale
    template_name = 'sales/list.html'
    context_object_name = 'sales'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Aplicar filtros desde la URL
        date = self.request.GET.get('date')
        status = self.request.GET.get('status')
        payment_method = self.request.GET.get('payment_method')
        
        if date:
            queryset = queryset.filter(date__date=date)
        if status:
            queryset = queryset.filter(status=status)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sale_status'] = Sale.SALE_STATUS
        context['payment_methods'] = Sale.PAYMENT_CHOICES
        return context

class SaleCreateView(LoginRequiredMixin, View):
    """Vista para crear una nueva venta"""
    
    def get(self, request, *args, **kwargs):
        return render(request, 'sales/create.html', {
            'payment_methods': Sale.PAYMENT_CHOICES,
            'sale_status': Sale.SALE_STATUS,
            'payment_providers': PaymentProvider.objects.all(),
            'installment_choices': PaymentProvider.INSTALLMENT_CHOICES,
            'default_provider': PaymentProvider.objects.filter(is_default=True).first()
        })
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            print("Datos recibidos para crear venta:", json.dumps(data, indent=2))

            # Procesar la fecha de venta
            sale_date = data.get('date')
            if not sale_date:
                sale_date = timezone.now()
            try:
                sale_date = datetime.fromisoformat(sale_date)
                if timezone.is_naive(sale_date):
                    sale_date = timezone.make_aware(sale_date, timezone.get_current_timezone())
            except ValueError as e:
                return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)

            # Validar carrito
            cart = data.get('cart', [])
            if not cart:
                return JsonResponse({'error': 'Carrito vacío'}, status=400)

            # Obtener datos de pago
            payment_method = data.get('payment_method')
            payment_provider_id = data.get('payment_provider')
            installments = data.get('installments') if payment_method == 'CREDIT' else None
           
           
           # Crear venta con cliente (solo una vez)
            customer_id = data.get('customer')
            print(f"ID del cliente seleccionado: {customer_id}")

            sale = Sale.objects.create(
                user=request.user,
                payment_method=payment_method,
                payment_provider_id=payment_provider_id if payment_method in ['DEBIT', 'CREDIT'] else None,
                installments=installments,
                status=data['status'],
                date=sale_date,
                total=0,
                commission_amount=0,
                commission_tax=0,
                customer_id=customer_id
            )

            # Procesar productos y calcular total
            total = Decimal('0')
            for item in cart:
                product = Product.objects.get(id=item['product_id'])
                is_bulk = item.get('is_bulk', False)

                if is_bulk:
                    # Calcular cantidad exacta para ventas a granel
                    amount = Decimal(str(item['subtotal']))
                    price_per_kilo = Decimal(str(item['price']))
                    quantity, final_amount = calculate_bulk_quantity(amount, price_per_kilo)
                    
                    # Validar stock
                    if product.bulk_stock < quantity:
                        raise ValidationError(f'Stock insuficiente para {product.name} (Granel)')
                    
                    # Obtener el precio de compra correcto para productos a granel
                    if product.is_bulk:
                        purchase_price = product.get_weighted_average_purchase_price()
                        if purchase_price == 0:
                            raise ValidationError(f'No se puede determinar el precio de compra para {product.name}')
                    else:
                        # Cálculo correcto del precio de compra por kilo
                        precio_compra_saco = round_money(product.purchase_price / Decimal('1.19'))  # Precio saco sin IVA
                        precio_compra_kilo = round_money(precio_compra_saco / product.kilos_per_sack)  # Precio por kilo sin IVA
                        purchase_price = precio_compra_kilo

                    subtotal = int(amount)
                    product.bulk_stock -= quantity

                else:
                    # Venta normal
                    quantity = int(item['quantity'])
                    if product.stock < quantity:
                        raise ValidationError(f'Stock insuficiente para {product.name}')
                    purchase_price = product.purchase_price
                    subtotal = int(Decimal(str(quantity)) * Decimal(str(item['price'])))
                    product.stock -= quantity

                # Crear detalle de venta
                detail = SaleDetail.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=item['price'],
                    is_bulk=is_bulk,
                    purchase_price=purchase_price,
                    subtotal=subtotal
                )
                
                product.save()
                
                # Registrar movimiento en ProductStock
                ProductStock.objects.create(
                    product=product,
                    movement_type='OUT',
                    quantity=quantity,
                    batch_number=ProductStock.generate_batch_number(),
                    purchase_price=purchase_price,
                    remaining_quantity=0,
                    notes=f"Venta {'a granel' if is_bulk else ''} #{sale.id}",
                    created_by=request.user,
                    date=sale_date
                )
                
                total += Decimal(str(subtotal))

            # Actualizar total y marcar stock como descontado
            sale.total = int(total)
            sale.is_stock_deducted = True
            sale.save()

            # Calcular comisión si aplica
            if payment_method in ['DEBIT', 'CREDIT'] and payment_provider_id:
                provider = PaymentProvider.objects.get(id=payment_provider_id)
                commission_data = provider.calculate_commission(sale.total, payment_method == 'CREDIT')
                
                sale.commission_amount = commission_data['commission']
                sale.commission_tax = commission_data['tax']
                sale.save()

            request.session['cart'] = []
            return JsonResponse({'success': True, 'redirect_url': '/sales/'})

        except Exception as e:
            print(f"Error en la venta: {str(e)}")  # Debug
            return JsonResponse({'error': str(e)}, status=400)


class SaleDetailView(LoginRequiredMixin, DetailView):
    """Vista para mostrar los detalles de una venta específica"""
    model = Sale
    template_name = 'sales/detail.html'
    context_object_name = 'sale'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class SaleUpdateStatusView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar el estado de una venta"""
    model = Sale
    fields = ['status']
    template_name = 'sales/detail.html'
    http_method_names = ['post']

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        sale = self.get_object()
        old_status = sale.status
        new_status = request.POST.get('status')

        # Validar que el nuevo estado sea válido
        if new_status not in dict(Sale.SALE_STATUS):
            messages.error(self.request, f'Estado inválido: {new_status}')
            return redirect('sales:detail', pk=sale.pk)

        # Actualizar y verificar el cambio de estado
        sale.status = new_status
        sale.save()
        sale.refresh_from_db()
        
        if sale.status != new_status:
            messages.error(self.request, 'Error al actualizar el estado de la venta.')
            return redirect('sales:detail', pk=sale.pk)
        
        messages.success(self.request, f'El estado de la venta ha sido actualizado a {new_status}.')
        return redirect('sales:detail', pk=sale.pk)

class SaleCancelConfirmationView(LoginRequiredMixin, TemplateView):
    """Vista para manejar la cancelación de una venta"""
    template_name = 'sales/cancel_confirmation.html'
    model = Sale

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sale = Sale.objects.get(pk=self.kwargs['pk'])
        context['sale'] = sale
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        sale = Sale.objects.get(pk=self.kwargs['pk'])
        
        if sale.status == 'CANCELLED':
            messages.error(request, "Esta venta ya está cancelada.")
            return redirect('sales:detail', pk=sale.pk)
        
        # Restaurar stock si fue descontado
        if sale.is_stock_deducted:
            for detail in sale.saledetail_set.all():
                product = detail.product
                
                # Restaurar stock según tipo de producto (granel o normal)
                if detail.is_bulk:
                    product.bulk_stock += Decimal(str(detail.quantity))
                else:
                    product.stock += int(detail.quantity)
                product.save()

                # Registrar movimiento de entrada por cancelación
                ProductStock.objects.create(
                    product=product,
                    movement_type='IN',
                    quantity=detail.quantity,
                    batch_number=ProductStock.generate_batch_number(),
                    purchase_price=product.purchase_price,
                    remaining_quantity=detail.quantity,
                    notes=f"Restauración por cancelación de venta #{sale.id}",
                    created_by=request.user,
                    date=timezone.now()
                )
                
            sale.is_stock_deducted = False
        
        # Actualizar estado de la venta
        sale.status = 'CANCELLED'
        sale.save()
        
        messages.success(request, "La venta ha sido cancelada y el stock ha sido restaurado.")
        return redirect('sales:detail', pk=sale.pk)

@method_decorator(csrf_exempt, name='dispatch')
class SaleEditView(LoginRequiredMixin, UpdateView):
    """Vista para editar una venta existente"""
    model = Sale
    template_name = 'sales/edit.html'
    fields = ['payment_method', 'status']

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                cart = data.get('cart', [])
                payment_method = data.get('payment_method')
                status = data.get('status')

                if not cart:
                    return JsonResponse({'error': "No hay productos en la venta"}, status=400)

                # Restaurar stock anterior si fue descontado
                if self.object.is_stock_deducted:
                    for detail in self.object.saledetail_set.all():
                        product = detail.product
                        if detail.is_bulk:
                            product.bulk_stock += decimal.Decimal(str(detail.quantity))
                        else:
                            product.stock += int(detail.quantity)
                        product.save()

                # Eliminar detalles anteriores
                self.object.saledetail_set.all().delete()

                # Actualizar la venta
                self.object.payment_method = payment_method
                self.object.status = status
                total_venta = 0
                self.object.customer_id = data.get('customer')

                # Procesar nuevos productos
                for item in cart:
                    product = Product.objects.get(id=item['product_id'])
                    is_bulk = item.get('is_bulk', False)
                    quantity = decimal.Decimal(str(item['quantity']))

                    # Manejar productos a granel
                    if is_bulk:
                        if quantity > product.bulk_stock:
                            raise ValidationError(f'Stock insuficiente para {product.name} (Granel)')
                        product.bulk_stock -= quantity
                        purchase_price = product.purchase_price / product.kilos_per_sack
                        final_amount = decimal.Decimal(str(item['subtotal']))
                    else:
                        if int(quantity) > product.stock:
                            raise ValidationError(f'Stock insuficiente para {product.name}')
                        product.stock -= int(quantity)
                        purchase_price = product.purchase_price
                        final_amount = quantity * decimal.Decimal(str(item['price']))
                    
                    product.save()

                    # Registrar movimiento en ProductStock
                    ProductStock.objects.create(
                        product=product,
                        movement_type='OUT',
                        quantity=quantity,
                        batch_number=ProductStock.generate_batch_number(),
                        purchase_price=purchase_price,
                        remaining_quantity=0,
                        notes=f"Venta #{self.object.id} (Editada)",
                        created_by=request.user,
                        date=timezone.now()
                    )

                    # Crear nuevo detalle de venta
                    SaleDetail.objects.create(
                        sale=self.object,
                        product=product,
                        quantity=quantity,
                        unit_price=item['price'],
                        purchase_price=purchase_price,
                        is_bulk=is_bulk,
                        is_tax_included=product.is_sale_with_tax,
                        subtotal=final_amount
                    )

                    total_venta += final_amount

                self.object.total = total_venta
                self.object.is_modified = True
                self.object.save()

                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('sales:detail', kwargs={'pk': self.object.pk})
                })

            except json.JSONDecodeError:
                return JsonResponse({'error': 'Datos inválidos'}, status=400)
            except ValidationError as e:
                return JsonResponse({'error': str(e)}, status=400)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial_cart = []
        for detail in self.object.saledetail_set.all():
            initial_cart.append({
                'product_id': detail.product.id,
                'name': detail.product.name + (' (Granel)' if detail.is_bulk else ''),
                'quantity': float(detail.quantity),
                'price': float(detail.unit_price),
                'is_bulk': detail.is_bulk,
                'subtotal': float(detail.subtotal)
            })
        
        if self.object.customer:
            context['initial_customer'] = {
                'id': self.object.customer.id,
                'text': self.object.customer.get_full_name(),
                'rut': self.object.customer.rut
            }

        # Filtrar estados excluyendo 'CANCELLED'
        estados_permitidos = [status for status in Sale.SALE_STATUS if status[0] != 'CANCELLED']

        context.update({
            'products': Product.objects.filter(is_active=True),
            'payment_methods': Sale.PAYMENT_CHOICES,
            'sale_status': estados_permitidos,
            'initial_cart': initial_cart
        })
        return context