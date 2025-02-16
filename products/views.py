from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Product, Category, ProductStock, StockEntry, StockEntryDetail
from users.mixins import AdminRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta, datetime
from django.conf import settings
from django.http import JsonResponse, Http404
from .forms import StockEntryForm, StockEntryDetailForm, ProductForm, MermaForm, OpenSackForm
import json
from suppliers.models import Supplier
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = Product.objects.select_related('category').all()
        search = self.request.GET.get('search', '')
        category = self.request.GET.get('category', '')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        if category:
            queryset = queryset.filter(category_id=category)
            
        # Forzar el refresco de los datos
        queryset = queryset.all()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'

    def get_object(self):
        obj = super().get_object()
        obj.refresh_from_db()  # Forzar refresco desde la base de datos
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object.refresh_from_db()  # Asegurar datos actualizados
        context['merma_form'] = MermaForm(self.object)
        return context

class ProductCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_products'] = Product.objects.filter(
            is_bulk=False,
            is_active=True
        ).order_by('brand', 'name')
        if self.request.user.role == 'admin':
            context['show_admin_message'] = True
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # self.object = form.save()
                self.object = form.save(commit=False)
                self.object.is_active = True  # Forzar active en True
                self.object.save()
                form.save_m2m()  # Para las relaciones ManyToMany
                
                # Si tiene stock inicial y requiere vencimiento, crear el registro
                if self.object.requires_expiration and self.object.stock > 0:
                    batch_number = form.cleaned_data.get('initial_batch_number') or ProductStock.generate_batch_number()
                    expiration_date = form.cleaned_data.get('expiration_date')
                    
                    if not expiration_date:
                        form.add_error('expiration_date', 'La fecha de vencimiento es requerida')
                        return self.form_invalid(form)

                    ProductStock.objects.create(
                        product=self.object,
                        batch_number=batch_number,
                        expiration_date=expiration_date,
                        movement_type='IN',
                        quantity=self.object.stock,
                        purchase_price=self.object.purchase_price,
                        remaining_quantity=self.object.stock,
                        created_by=self.request.user,
                        date=timezone.now()
                    )

                messages.success(self.request, 'Producto creado exitosamente.')
                return redirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f'Error al crear el producto: {str(e)}')
            return self.form_invalid(form)

class ProductUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_products'] = Product.objects.filter(
            is_bulk=False,
            is_active=True,
            brand=self.object.brand
        ).exclude(pk=self.object.pk).order_by('name')
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Capturar valores originales antes de cualquier cambio
                fields_to_track = [
                    'purchase_price', 'sale_price', 'is_purchase_with_tax',
                    'is_sale_with_tax', 'has_bulk_sales', 'bulk_sale_price',
                    'requires_expiration', 'is_active', 'is_bulk'
                ]
                
                original_product = Product.objects.get(pk=self.object.pk)
                old_data = {}
                new_data = {}
                
                for field in fields_to_track:
                    if field in form.changed_data:
                        old_data[field] = getattr(original_product, field)
                        new_data[field] = form.cleaned_data[field]
                
                # Guardar el formulario
                self.object = form.save()
                
                # Registrar los cambios si hubo modificaciones
                if old_data:
                    self.object.log_changes(self.request.user, old_data, new_data)
                
                messages.success(self.request, 'Producto actualizado exitosamente.')
                return redirect(self.get_success_url())
                
        except Exception as e:
            messages.error(self.request, f'Error al actualizar el producto: {str(e)}')
            return self.form_invalid(form)

class ProductDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/delete.html'
    success_url = reverse_lazy('products:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Producto eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
    

class OpenSackView(LoginRequiredMixin, FormView):
    template_name = 'products/open_sack.html'
    form_class = OpenSackForm
    success_url = reverse_lazy('products:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.product = get_object_or_404(Product, pk=self.kwargs['pk'])
        kwargs['product'] = self.product
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context

    @transaction.atomic
    def form_valid(self, form):
        try:
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data.get('notes', '')
            product = self.product
            
            # Validaciones previas
            if not product.kilos_per_sack:
                messages.error(self.request, 'El producto no tiene configurados los kilos por saco')
                return self.form_invalid(form)

            bulk_product = product.bulk_products.first()
            if not bulk_product:
                messages.error(self.request, 'No hay un producto a granel vinculado')
                return self.form_invalid(form)

            print(f"Estado inicial - Stock saco: {product.stock}, Stock granel: {bulk_product.bulk_stock}")

            kilos_totales = Decimal(str(quantity)) * Decimal(str(product.kilos_per_sack))
            merma = kilos_totales * Decimal('0.02')  # 2% de merma
            kilos_netos = kilos_totales - merma
            
            current_date = timezone.now()
            batch_base = current_date.strftime('%Y%m%d%H%M%S')

            # 1. Registrar salida de sacos
            sack_movement = ProductStock.objects.create(
                product=product,
                movement_type='OPEN',
                quantity=quantity,
                purchase_price=product.purchase_price,
                remaining_quantity=0,
                notes=notes,
                created_by=self.request.user,
                date=current_date,
                batch_number=f"SACK-{batch_base}"
            )

            # 2. Registrar merma
            ProductStock.objects.create(
                product=bulk_product,
                movement_type='MERMA',
                quantity=merma,
                purchase_price=product.get_purchase_price_without_tax(),
                remaining_quantity=0,
                parent_stock=sack_movement,
                notes=f"Merma por apertura de {quantity} sacos",
                created_by=self.request.user,
                date=current_date,
                batch_number=f"MRMA-{batch_base}"
            )

            # 3. Registrar entrada en producto a granel
            ProductStock.objects.create(
                product=bulk_product,
                movement_type='IN',
                quantity=kilos_netos,
                purchase_price=product.get_purchase_price_without_tax(),
                remaining_quantity=kilos_netos,
                parent_stock=sack_movement,
                notes=f"Apertura de {quantity} sacos de {product.name}",
                created_by=self.request.user,
                date=current_date,
                batch_number=f"BULK-{batch_base}"
            )

            # 4. Actualizar stocks
            product.stock -= quantity
            product.save()

            bulk_product.bulk_stock += kilos_netos
            bulk_product.save()

            # Refrescar instancias desde la base de datos
            product.refresh_from_db()
            bulk_product.refresh_from_db()

            print(f"Estado final - Stock saco: {product.stock}, Stock granel: {bulk_product.bulk_stock}")

            messages.success(
                self.request,
                f'Operación exitosa:\n'
                f'- Se abrieron {quantity} sacos\n'
                f'- Se registró una merma de {merma:.2f} kg\n'
                f'- Se agregaron {kilos_netos:.2f} kg al stock a granel\n'
                f'- Stock actual a granel: {bulk_product.bulk_stock:.2f} kg'
            )

            # Redirigir al detalle del producto para ver los cambios
            return redirect('products:detail', pk=bulk_product.pk)

        except Exception as e:
            messages.error(self.request, f'Error al abrir sacos: {str(e)}')
            return self.form_invalid(form)



class ExpiringProductsView(ListView):
    template_name = 'products/expiring_products.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        today = timezone.now().date()
        warning_date = today + timedelta(days=settings.PRODUCT_EXPIRY_WARNING_DAYS)
        
        # Obtener productos que vencen dentro del rango configurado
        return ProductStock.objects.filter(
            product__requires_expiration=True,
            expiration_date__isnull=False,
            expiration_date__lte=warning_date,
            remaining_quantity__gt=0
        ).select_related('product').order_by('expiration_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        for product in context['products']:
            days_until_expiration = (product.expiration_date - today).days
            
            if days_until_expiration <= settings.PRODUCT_EXPIRY_CRITICAL_DAYS:
                product.expiration_class = 'bg-red-100 text-red-800'
            elif days_until_expiration <= settings.PRODUCT_EXPIRY_WARNING_DAYS:
                product.expiration_class = 'bg-yellow-100 text-yellow-800'
            else:
                product.expiration_class = 'bg-green-100 text-green-800'
            
            product.days_until_expiration = days_until_expiration
            
        return context

class RegisterMermaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = MermaForm(product, request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    quantity = form.cleaned_data['quantity']
                    reason = form.cleaned_data['reason']
                    notes = form.cleaned_data['notes']

                    # Crear registro en ProductStock
                    ProductStock.objects.create(
                        product=product,
                        movement_type='MERMA',
                        quantity=quantity,
                        batch_number=ProductStock.generate_batch_number(),
                        remaining_quantity=0,
                        purchase_price=product.get_weighted_average_purchase_price() if product.is_bulk else product.purchase_price,
                        notes=f"Merma por {reason}: {notes}",
                        created_by=request.user,
                        date=timezone.now()
                    )

                    # Actualizar stock del producto según su tipo
                    if product.is_bulk:
                        product.bulk_stock -= quantity
                    else:
                        product.stock -= quantity
                    product.save()

                    unidad = 'kg' if product.is_bulk else 'unidades'
                    return JsonResponse({
                        'status': 'success',
                        'message': f'Se registró merma de {quantity} {unidad} correctamente'
                    })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error al registrar merma: {str(e)}'
                }, status=400)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Formulario inválido',
                'errors': form.errors
            }, status=400)

# class ProductMovementHistoryView(LoginRequiredMixin, ListView):
#     template_name = 'products/movement_history.html'
#     context_object_name = 'movements'
#     paginate_by = 20

#     def get_queryset(self):
#         self.product = get_object_or_404(Product, pk=self.kwargs['pk'])
#         queryset = ProductStock.objects.filter(product=self.product)

#         # Aplicar filtros
#         movement_type = self.request.GET.get('movement_type')
#         date_from = self.request.GET.get('date_from')
#         date_to = self.request.GET.get('date_to')

#         if movement_type:
#             queryset = queryset.filter(movement_type=movement_type)
        
#         if date_from:
#             queryset = queryset.filter(date__date__gte=date_from)
        
#         if date_to:
#             queryset = queryset.filter(date__date__lte=date_to)

#         return queryset.order_by('-date')

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['product'] = self.product
#         context['movement_types'] = ProductStock.MOVEMENT_TYPES

#         # Asegurar que los movimientos con changes_detail tengan su JSON serializado correctamente
#         for movement in context['movements']:
#             if movement.changes_detail:
#                 print("Cambios encontrados:", movement.changes_detail)  # Debug
#                 if isinstance(movement.changes_detail, dict):  # Convertir si es un diccionario
#                     movement.changes_detail = json.dumps(movement.changes_detail)

#         return context

class ProductMovementHistoryView(LoginRequiredMixin, ListView):
    template_name = 'products/movement_history.html'
    model = ProductStock
    context_object_name = 'movements'
    paginate_by = 20

    def get_queryset(self):
        # Opción 1: Usar pk en lugar de product_id
        self.product = get_object_or_404(Product, pk=self.kwargs.get('pk'))
        
        # Opción 2: Manejar ambos casos
        product_id = self.kwargs.get('pk') or self.kwargs.get('product_id')
        self.product = get_object_or_404(Product, pk=product_id)
        
        queryset = ProductStock.objects.filter(product=self.product)
        
        # Aplicar filtros
        movement_type = self.request.GET.get('tipo')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
            
        date_from = self.request.GET.get('desde')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
            
        date_to = self.request.GET.get('hasta')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset.select_related('product', 'created_by')

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['movement_types'] = ProductStock._meta.get_field('movement_type').choices
    #     context['product'] = self.product  # Aseguramos que el producto esté en el contexto
    #     return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        context['movement_types'] = ProductStock.MOVEMENT_TYPES

        # Asegurar que los movimientos con changes_detail tengan su JSON serializado correctamente
        for movement in context['movements']:
            if movement.changes_detail:
                print("Cambios encontrados:", movement.changes_detail)  # Debug
                if isinstance(movement.changes_detail, dict):  # Convertir si es un diccionario
                    movement.changes_detail = json.dumps(movement.changes_detail)

        return context

class StockEntryListView(LoginRequiredMixin, ListView):
    """Vista para listar todos los ingresos de stock"""
    model = StockEntry
    template_name = 'products/stock_entry_list.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        supplier = self.request.GET.get('supplier')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        
        return queryset.select_related('supplier', 'created_by')

class StockEntryCreateView(LoginRequiredMixin, CreateView):
    model = StockEntry
    form_class = StockEntryForm
    template_name = 'products/stock_entry_form.html'
    success_url = reverse_lazy('products:stock_entry_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['detail_form'] = StockEntryDetailForm()
        context['products'] = Product.objects.filter(is_active=True)
        context['suppliers'] = Supplier.objects.filter(is_active=True)
        return context

    def validate_batch_numbers(self, details_data):
        """Valida que los números de lote no estén duplicados"""
        batch_numbers = [detail.get('batch_number') for detail in details_data 
                        if detail.get('batch_number')]
        
        # Verificar duplicados en los datos actuales
        if len(batch_numbers) != len(set(batch_numbers)):
            raise ValidationError('Hay números de lote duplicados en el ingreso actual')
        
        # Verificar si ya existen en la base de datos
        existing_batches = ProductStock.objects.filter(
            batch_number__in=batch_numbers
        ).values_list('batch_number', 'product__name')
        
        if existing_batches:
            batch_details = [f"'{batch}' (usado en producto: {product})" 
                           for batch, product in existing_batches]
            raise ValidationError(
                'Los siguientes números de lote ya están en uso:\n' + 
                '\n'.join(batch_details)
            )

    @transaction.atomic
    def form_valid(self, form):
        try:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                self.object = form.save(commit=False)
                self.object.created_by = self.request.user
                
                details_data = json.loads(self.request.POST.get('details', '[]'))
                
                if not details_data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Debe agregar al menos un producto'
                    }, status=400)

                # Validar números de lote antes de procesar
                try:
                    self.validate_batch_numbers(details_data)
                except ValidationError as e:
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    }, status=400)

                # Guardar el ingreso principal
                self.object.save()

                # Procesar detalles del ingreso
                for detail in details_data:
                    try:
                        # Convertir y validar la fecha de vencimiento
                        expiration_date = None
                        if detail.get('expiration_date'):
                            try:
                                expiration_date = datetime.strptime(
                                    detail['expiration_date'], 
                                    '%Y-%m-%d'
                                ).date()
                            except ValueError:
                                raise ValidationError(
                                    'El formato de la fecha de vencimiento no es válido'
                                )

                        # Convertir cantidad a decimal
                        try:
                            quantity = Decimal(str(detail['quantity']))
                            if quantity <= 0:
                                raise ValidationError('La cantidad debe ser mayor a 0')
                        except (ValueError, TypeError, InvalidOperation):
                            raise ValidationError('La cantidad ingresada no es válida')

                        # Convertir precio a entero
                        try:
                            purchase_price = int(float(detail['purchase_price']))
                            if purchase_price <= 0:
                                raise ValidationError('El precio debe ser mayor a 0')
                        except (ValueError, TypeError):
                            raise ValidationError('El precio ingresado no es válido')

                        # Validar producto
                        try:
                            product = Product.objects.get(pk=int(detail['product']))
                        except (Product.DoesNotExist, ValueError):
                            raise ValidationError('Producto no válido')

                        # Crear el detalle del ingreso
                        StockEntryDetail.objects.create(
                            stock_entry=self.object,
                            product=product,
                            quantity=quantity,
                            purchase_price=purchase_price,
                            is_price_with_tax=bool(detail.get('is_price_with_tax', True)),
                            expiration_date=expiration_date,
                            batch_number=str(detail.get('batch_number', ''))
                        )

                    except ValidationError as e:
                        # Revertir la transacción si hay error
                        transaction.set_rollback(True)
                        return JsonResponse({
                            'status': 'error',
                            'message': str(e)
                        }, status=400)

                return JsonResponse({
                    'status': 'success',
                    'message': 'Ingreso de stock registrado exitosamente',
                    'redirect_url': self.get_success_url()
                })
            
            return super().form_valid(form)

        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Ocurrió un error inesperado al procesar el ingreso'
            }, status=400)

class StockEntryDetailView(LoginRequiredMixin, DetailView):
    """Vista para mostrar el detalle de un ingreso de stock específico"""
    model = StockEntry
    template_name = 'products/stock_entry_detail.html'
    context_object_name = 'entry'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Incluimos los detalles del ingreso ordenados por producto
        context['details'] = self.object.stockentrydetail_set.all().select_related('product')
        return context
    
def link_bulk_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    available_products = Product.objects.filter(
        brand=product.brand,  # Mismo brand
        is_bulk=False  # No son granel
    )
    if request.method == 'POST':
        selected_products = request.POST.getlist('products')
        product.linked_products.set(selected_products)
        return redirect('products:detail', pk=pk)
    
    return render(request, 'products/link_bulk.html', {
        'product': product,
        'available_products': available_products
    })





