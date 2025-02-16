from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from suppliers.models import Supplier
import decimal


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    brand = models.CharField(max_length=100, verbose_name="Marca")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Categoría")
    description = models.TextField(verbose_name="Descripción", blank=True)
    
    # Campos de precios base
    purchase_price = models.IntegerField(verbose_name="Precio de compra")
    is_purchase_with_tax = models.BooleanField(default=True, verbose_name="Precio de compra incluye IVA")
    sale_price = models.IntegerField(verbose_name="Precio de venta")
    is_sale_with_tax = models.BooleanField(default=True, verbose_name="Precio de venta incluye IVA")
    
    # Campos nuevos para manejo de granel
    has_bulk_sales = models.BooleanField(default=False, verbose_name="¿Vende a granel?")
    kilos_per_sack = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Kilos por saco",
        help_text="Cantidad de kilos que contiene cada saco"
    )
    bulk_sale_price = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Precio de venta por kilo",
        help_text="Precio de venta por kilo para ventas a granel"
    )
    
    # Control de vencimiento
    requires_expiration = models.BooleanField(
        default=False,
        verbose_name="Requiere fecha de vencimiento",
        help_text="Indica si el producto necesita control de fecha de vencimiento"
    )
    
    # Campos existentes
    stock = models.IntegerField(default=0, verbose_name="Stock en sacos")
    bulk_stock = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Stock a granel (kg)",
        help_text="Stock disponible para venta a granel en kilos"
    )
    image = models.ImageField(upload_to='products/', verbose_name="Imagen", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    # Manejo de producto a granel
    is_bulk = models.BooleanField(
        default=False, 
        verbose_name="Es producto a granel",
        help_text="Indica si este producto se vende a granel"
    )
    linked_products = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='bulk_products',
        verbose_name="Productos vinculados",
        help_text="Productos que pueden abrirse para venta a granel",
        blank=True
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-created']

    def __str__(self):
        return self.name

    def get_purchase_price_without_tax(self):
        if self.is_purchase_with_tax:
            return int(self.purchase_price / 1.19)
        return self.purchase_price

    def get_sale_price_without_tax(self):
        if self.is_sale_with_tax:
            return int(self.sale_price / 1.19)
        return self.sale_price

    def calculate_profit_percentage(self):
        purchase_net = self.get_purchase_price_without_tax()
        sale_net = self.get_sale_price_without_tax()
        
        if purchase_net > 0:
            profit = ((sale_net - purchase_net) / purchase_net) * 100
            return int(profit)
        return 0

    def calculate_bulk_kilo_cost(self):
        """Calcula el costo por kilo basado en el precio de compra del saco"""
        if self.has_bulk_sales and self.kilos_per_sack:
            return int(self.purchase_price / self.kilos_per_sack)
        return 0
    
    def get_stock_valuation_sale_gross(self):
        """Valor total del stock a precio de venta con IVA"""
        # Valorización de stock en unidades/sacos
        regular_stock = self.stock * self.sale_price if self.stock and self.sale_price else 0
        
        # Valorización de stock a granel
        bulk_value = 0
        if self.has_bulk_sales and self.bulk_stock and self.bulk_sale_price:
            # Multiplicamos los kilos por el precio por kilo y redondeamos
            bulk_value = round(float(self.bulk_stock) * self.bulk_sale_price)
        
        return int(regular_stock + bulk_value)

    def get_stock_valuation_sale_net(self):
        """Valor total del stock a precio de venta sin IVA"""
        # Valorización de stock en unidades/sacos
        if self.is_sale_with_tax:
            regular_stock = int(self.stock * (self.sale_price / Decimal('1.19'))) if self.stock and self.sale_price else 0
        else:
            regular_stock = self.stock * self.sale_price if self.stock and self.sale_price else 0
        
        # Valorización de stock a granel
        bulk_value = 0
        if self.has_bulk_sales and self.bulk_stock and self.bulk_sale_price:
            if self.is_sale_with_tax:
                price_without_tax = int(self.bulk_sale_price / Decimal('1.19'))
            else:
                price_without_tax = self.bulk_sale_price
            bulk_value = round(float(self.bulk_stock) * price_without_tax)
        
        return int(regular_stock + bulk_value)

    def get_stock_valuation_purchase_gross(self):
        """Valor total del stock a precio de compra con IVA"""
        # Valorización de stock en unidades/sacos
        regular_stock = self.stock * self.purchase_price if self.stock and self.purchase_price else 0
        
        # Valorización de stock a granel
        bulk_value = 0
        if self.has_bulk_sales and self.bulk_stock:
            kilo_cost = self.calculate_bulk_kilo_cost()
            if kilo_cost:
                bulk_value = round(float(self.bulk_stock) * kilo_cost)
        
        return int(regular_stock + bulk_value)

    def get_stock_valuation_purchase_net(self):
        """Valor total del stock a precio de compra sin IVA"""
        # Valorización de stock en unidades/sacos
        if self.is_purchase_with_tax:
            regular_stock = int(self.stock * (self.purchase_price / Decimal('1.19'))) if self.stock and self.purchase_price else 0
        else:
            regular_stock = self.stock * self.purchase_price if self.stock and self.purchase_price else 0
        
        # Valorización de stock a granel
        bulk_value = 0
        if self.has_bulk_sales and self.bulk_stock:
            kilo_cost = self.calculate_bulk_kilo_cost()
            if kilo_cost:
                if self.is_purchase_with_tax:
                    kilo_cost = int(kilo_cost / Decimal('1.19'))
                bulk_value = round(float(self.bulk_stock) * kilo_cost)
        
        return int(regular_stock + bulk_value)
        
    def calculate_unit_profit(self):
        """Calcula la ganancia bruta por unidad"""
        venta_neta = self.get_sale_price_without_tax()
        compra_neta = self.get_purchase_price_without_tax()
        return venta_neta - compra_neta
    
    def calculate_bulk_unit_profit(self):
        """Calcula la ganancia bruta por kilo en venta a granel"""
        if not self.is_bulk or not self.bulk_sale_price:
            return 0
            
        try:
            # Precio de venta neto por kilo
            venta_neta = self.bulk_sale_price
            if self.is_sale_with_tax:
                venta_neta = int(venta_neta / Decimal('1.19'))
                
            # Obtener costo promedio por kilo
            kilo_cost = self.calculate_weighted_average_cost()
            if not kilo_cost:
                return 0
                
            return venta_neta - kilo_cost
            
        except (TypeError, decimal.InvalidOperation):
            return 0

    def calculate_bulk_profit_percentage(self):
        """Calcula el porcentaje de rentabilidad para ventas a granel"""
        if self.has_bulk_sales:
            compra_neta = self.calculate_bulk_kilo_cost()
            if compra_neta > 0:
                ganancia = self.calculate_bulk_unit_profit()
                return int((ganancia / compra_neta) * 100)
        return 0
    
    def get_weighted_average_purchase_price(self):
        """Calcula el precio de compra promedio ponderado por kilo para productos a granel"""
        if not self.is_bulk:
            return 0

        # Obtener todos los movimientos de entrada a granel
        bulk_movements = ProductStock.objects.filter(
            product=self,
            movement_type='IN',
            remaining_quantity__gt=0  # Solo considerar stock disponible
        ).select_related('parent_stock')

        total_kilos = Decimal('0')
        total_cost = Decimal('0')

        for movement in bulk_movements:
            kilos = movement.quantity
            # Si viene de apertura de saco, usar el precio del saco
            if movement.parent_stock:
                costo_kilo = movement.parent_stock.product.get_purchase_price_without_tax() / movement.parent_stock.product.kilos_per_sack
            else:
                costo_kilo = movement.purchase_price

            total_kilos += kilos
            total_cost += kilos * costo_kilo

        if total_kilos > 0:
            return int(total_cost / total_kilos)
        return 0

    def get_granel_purchase_price(self):
        """Retorna el precio de compra para productos a granel"""
        if self.is_bulk:
            return self.get_weighted_average_purchase_price()
        return self.purchase_price

    def get_granel_sale_price(self):
        """Retorna el precio de venta para productos a granel"""
        if self.is_bulk:
            return self.bulk_sale_price or 0
        return self.sale_price

    def calculate_granel_profit_percentage(self):
        """Calcula el porcentaje de rentabilidad para productos a granel"""
        if not self.is_bulk:
            return self.calculate_profit_percentage()

        purchase_price = self.get_weighted_average_purchase_price()
        if not purchase_price:
            return 0

        sale_price = self.bulk_sale_price
        if self.is_sale_with_tax:
            sale_price = int(sale_price / Decimal('1.19'))

        if purchase_price > 0:
            return int(((sale_price - purchase_price) / purchase_price) * 100)
        return 0
    
    @property
    def current_purchase_price(self):
        """Retorna el precio de compra actual basado en el último ingreso"""
        last_entry = ProductStock.objects.filter(
            product=self,
            movement_type='IN',
            remaining_quantity__gt=0
        ).order_by('-date').first()
        
        return last_entry.purchase_price if last_entry else self.purchase_price

    @property
    def weighted_average_price(self):
        """Calcula el precio promedio ponderado basado en el stock actual"""
        active_stock = ProductStock.objects.filter(
            product=self,
            movement_type='IN',
            remaining_quantity__gt=0
        )
        
        total_value = sum(stock.remaining_quantity * stock.purchase_price for stock in active_stock)
        total_quantity = sum(stock.remaining_quantity for stock in active_stock)
        
        return round(total_value / total_quantity) if total_quantity > 0 else self.purchase_price

    def calculate_profit_percentage(self):
        """Calcula el porcentaje de rentabilidad basado en el precio promedio"""
        purchase_net = self.weighted_average_price / 1.19 if self.is_purchase_with_tax else self.weighted_average_price
        sale_net = self.get_sale_price_without_tax()
        
        if purchase_net > 0:
            profit = ((sale_net - purchase_net) / purchase_net) * 100
            return int(profit)
        return 0
    
    # Registra los cambios realizados al producto
    def log_changes(self, user, old_data, new_data):
        """
        Registra los cambios realizados al producto
        """
        changes = {}
        fields_to_track = {
            'purchase_price': 'Precio de compra',
            'sale_price': 'Precio de venta',
            'is_purchase_with_tax': 'Incluye IVA en compra',
            'is_sale_with_tax': 'Incluye IVA en venta',
            'has_bulk_sales': 'Venta a granel',
            'bulk_sale_price': 'Precio venta granel',
            'requires_expiration': 'Control de vencimiento',
            'is_active': 'Estado activo'
        }

        # Debug para ver todos los datos que llegan
        print("Datos antiguos recibidos:", old_data)
        print("Datos nuevos recibidos:", new_data)

        for field, display_name in fields_to_track.items():
            if field in old_data or field in new_data:
                old_value = old_data.get(field)
                new_value = new_data.get(field)
                
                # Solo registrar si los valores son diferentes
                if old_value != new_value:
                    # Formatear valores booleanos
                    if isinstance(old_value, bool):
                        old_value = 'Sí' if old_value else 'No'
                    if isinstance(new_value, bool):
                        new_value = 'Sí' if new_value else 'No'
                    
                    # Formatear valores numéricos
                    if isinstance(old_value, (int, float)):
                        old_value = f"${old_value:,}"
                    if isinstance(new_value, (int, float)):
                        new_value = f"${new_value:,}"
                    
                    # Registrar el cambio
                    changes[display_name] = {
                        'old': str(old_value),
                        'new': str(new_value)
                    }
                    print(f"Cambio registrado en {display_name}: {old_value} -> {new_value}")

        if changes:
            ProductStock.objects.create(
                product=self,
                movement_type='EDIT',
                quantity=0,
                remaining_quantity=0,
                purchase_price=self.purchase_price,
                batch_number=ProductStock.generate_batch_number(),
                created_by=user,
                date=timezone.now(),
                changes_detail=changes,
                notes=f"Edición de {len(changes)} campos del producto"
            )

    sku = models.CharField(
        max_length=7,
        unique=True,
        verbose_name="SKU",
        null=True,  # Para permitir productos existentes sin SKU
        blank=True,
        help_text="Código único del producto"
    )
    
    def save(self, *args, **kwargs):
        if not self.sku:
            last_sku = Product.objects.order_by('-sku').first()
            if last_sku and last_sku.sku:
                next_number = int(last_sku.sku) + 1
            else:
                next_number = 1
            self.sku = str(next_number).zfill(7)
        super().save(*args, **kwargs)

    def calculate_weighted_average_cost(self):
        """Calcula el costo promedio ponderado por kilo para productos a granel"""
        if not self.is_bulk:
            return 0
            
        movements = ProductStock.objects.filter(
            product=self,
            movement_type='IN',
            is_bulk=True
        ).select_related('source_product')
        
        total_kilos = sum(m.quantity for m in movements)
        total_cost = sum(m.quantity * m.source_price for m in movements if m.source_price)
        
        return int(total_cost / total_kilos) if total_kilos > 0 else 0

    def get_available_source_products(self):
        """Retorna los productos vinculados que tienen stock disponible"""
        return self.linked_products.filter(stock__gt=0)

class ProductStock(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Entrada'),
        ('OUT', 'Salida'),
        ('OPEN', 'Apertura Saco'),
        ('ADJ', 'Ajuste Inv'),  
        ('MERMA', 'Merma'),
        ('EDIT', 'Edición'),
    ]

    # Para almacenar detalles de los cambios
    changes_detail = models.JSONField(
        'Detalles de cambios',
        null=True,
        blank=True,
        help_text='Almacena los detalles de los cambios en formato JSON'
    )

    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        verbose_name="Producto"
    )
    
    # Información del lote
    batch_number = models.CharField(
        max_length=50, 
        verbose_name="Número de lote",
        unique=True
    )
    expiration_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Fecha de vencimiento"
    )
    
    # Información del movimiento
    movement_type = models.CharField(
        max_length=10,
        choices=MOVEMENT_TYPES,
        verbose_name="Tipo de movimiento"
    )
    date = models.DateTimeField(
        verbose_name="Fecha del movimiento",
        help_text="Fecha y hora en que se realizó el movimiento"
    )
    
    # Cantidades y precios
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Cantidad",
        help_text="Cantidad en la unidad correspondiente (sacos o kilos)"
    )
    purchase_price = models.IntegerField(
        verbose_name="Precio de compra",
        help_text="Precio de compra por unidad al momento del movimiento"
    )
    
    # Control FIFO
    remaining_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Cantidad restante",
        help_text="Cantidad que queda disponible de este lote"
    )
    
    # Trazabilidad
    parent_stock = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Stock origen",
        help_text="Para producto a granel, referencia al saco del que proviene"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
        help_text="Notas adicionales sobre el movimiento"
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        verbose_name="Creado por"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Control de producto a granel
    source_product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='source_movements',
        verbose_name="Producto origen",
        help_text="Producto del cual proviene el movimiento (para aperturas de sacos)"
    )
    source_price = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Precio origen",
        help_text="Precio de compra del producto origen"
    )

    reference_type = models.CharField(
        max_length=10, 
        choices=[
            ('SALE', 'Venta'),
            ('PURCHASE', 'Compra'),
            ('INV', 'Inventario'),
            ('ADJ', 'Ajuste'),
            ('BULK', 'Apertura Granel')
        ],
        null=True,
        blank=True
    )
    reference_id = models.CharField(max_length=50, null=True, blank=True)

    # Agregar el método reference_detail
    @property
    def reference_detail(self):
        """Obtiene los detalles del documento relacionado"""
        if not self.reference_type or not self.reference_id:
            return None
            
        try:
            if self.reference_type == 'SALE':
                from sales.models import Sale
                sale = Sale.objects.get(number=self.reference_id)
                return {
                    'tipo': 'Venta',
                    'numero': sale.number,
                    'fecha': sale.date,
                    'url': reverse('sales:detail', kwargs={'pk': sale.id})
                }
            elif self.reference_type == 'INV':
                from inventory_management.models import InventoryCount
                inventory = InventoryCount.objects.get(id=self.reference_id)
                return {
                    'tipo': 'Inventario',
                    'numero': inventory.name,
                    'fecha': inventory.date_started,
                    'responsable': inventory.created_by.get_full_name(),
                    'url': reverse('inventory_management:detail', kwargs={'pk': inventory.id})
                }
        except Exception as e:
            print(f"Error obteniendo referencia: {str(e)}")
            return None

    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ['-date', 'product']
        indexes = [
            models.Index(fields=['product', 'date']),
            models.Index(fields=['batch_number']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} - {self.batch_number}"

    def save(self, *args, **kwargs):
        # Si es un nuevo registro
        if not self.pk:
            # Si es una entrada, la cantidad restante es igual a la cantidad inicial
            if self.movement_type == 'IN':
                self.remaining_quantity = self.quantity
            # Si es una salida o apertura, no afecta remaining_quantity (se maneja en el view)
            elif self.movement_type in ['OUT', 'OPEN']:
                self.remaining_quantity = 0

        super().save(*args, **kwargs)

    def clean(self):
        # Validaciones
        if self.product.requires_expiration and not self.expiration_date and self.movement_type == 'IN':
            raise ValidationError('Este producto requiere fecha de vencimiento')
        
        if self.is_bulk and not self.product.has_bulk_sales:
            raise ValidationError('Este producto no permite ventas a granel')
            
        if self.movement_type == 'OPEN' and not self.product.has_bulk_sales:
            raise ValidationError('No se puede abrir un saco de un producto que no permite venta a granel')
        
    def get_kilo_cost(self):
        """Calcula el costo por kilo del movimiento"""
        if self.parent_stock:
            # Si viene de apertura de saco
            sack_product = self.parent_stock.product
            return sack_product.get_purchase_price_without_tax() / sack_product.kilos_per_sack
        return self.purchase_price

    @staticmethod
    def generate_batch_number():
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        last_movement = ProductStock.objects.order_by('-id').first()
        if not last_movement:
            return f'LOT-{timestamp}-0001'
        
        try:
            last_number = int(last_movement.batch_number.split('-')[-1])
            new_number = f'LOT-{timestamp}-{str(last_number + 1).zfill(4)}'
        except (IndexError, ValueError):
            new_number = f'LOT-{timestamp}-0001'
        
        return new_number
    
    @classmethod
    def consume_stock(cls, product, quantity_needed):
        """
        Consume el stock usando método FIFO.
        Retorna una lista de tuplas (cantidad_consumida, precio_compra) por cada lote usado.
        """
        available_stock = cls.objects.filter(
            product=product,
            movement_type='IN',
            remaining_quantity__gt=0
        ).order_by('date')  # FIFO: ordenar por fecha más antigua primero
        
        consumed = []
        remaining_to_consume = quantity_needed
        
        for stock in available_stock:
            if remaining_to_consume <= 0:
                break
                
            quantity_from_this_stock = min(stock.remaining_quantity, remaining_to_consume)
            if quantity_from_this_stock > 0:
                consumed.append({
                    'stock': stock,
                    'quantity': quantity_from_this_stock,
                    'purchase_price': stock.purchase_price
                })
                remaining_to_consume -= quantity_from_this_stock
        
        if remaining_to_consume > 0:
            raise ValidationError(f'No hay suficiente stock disponible. Faltante: {remaining_to_consume}')
            
        return consumed

    def update_remaining_quantity(self, quantity_consumed):
        """Actualiza la cantidad restante después de un consumo"""
        if self.remaining_quantity >= quantity_consumed:
            self.remaining_quantity -= quantity_consumed
            self.save()
        else:
            raise ValidationError('No hay suficiente stock en este lote')
        
    def calculate_weighted_average_cost(self):
        """Calcula el costo promedio ponderado por kilo para productos a granel"""
        if not self.is_bulk:
            return 0
            
        movements = ProductStock.objects.filter(
            product=self,
            movement_type='IN',
            is_bulk=True
        ).select_related('source_product')
        
        total_kilos = sum(m.quantity for m in movements)
        total_cost = sum(m.quantity * m.source_price for m in movements if m.source_price)
        
        return int(total_cost / total_kilos) if total_kilos > 0 else 0

    def get_available_source_products(self):
        """Retorna los productos vinculados que tienen stock disponible"""
        return self.linked_products.filter(stock__gt=0)

class StockEntry(models.Model):
    date = models.DateField('Fecha de ingreso',
        help_text='Fecha en formato YYYY-MM-DD')
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.PROTECT, verbose_name='Proveedor')
    document_type = models.CharField('Tipo de documento', max_length=20, choices=[
        ('INVOICE', 'Factura'),
        ('GUIDE', 'Guía de despacho'),
        ('OTHER', 'Otro')
    ])
    document_number = models.CharField('Número de documento', max_length=50)
    notes = models.TextField('Notas', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ingreso de Stock'
        verbose_name_plural = 'Ingresos de Stock'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Ingreso {self.document_type} #{self.document_number} - {self.date}"


class StockEntryDetail(models.Model):
    stock_entry = models.ForeignKey(StockEntry, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField('Cantidad', max_digits=10, decimal_places=2)
    purchase_price = models.IntegerField('Precio de compra')
    is_price_with_tax = models.BooleanField('Precio incluye IVA', default=True)
    expiration_date = models.DateField('Fecha de vencimiento', null=True, blank=True)
    batch_number = models.CharField('Número de lote', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Detalle de Ingreso'
        verbose_name_plural = 'Detalles de Ingreso'

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)

        if is_new:
            # Crear movimiento en ProductStock
            ProductStock.objects.create(
                product=self.product,
                movement_type='IN',
                quantity=self.quantity,
                purchase_price=self.purchase_price,
                batch_number=self.batch_number or ProductStock.generate_batch_number(),
                expiration_date=self.expiration_date,
                remaining_quantity=self.quantity,
                notes=f"Ingreso desde {self.stock_entry.document_type} #{self.stock_entry.document_number}",
                created_by=self.stock_entry.created_by,
                date=self.stock_entry.date
            )

            # Actualizar stock del producto - SIEMPRE en sacos/unidades
            self.product.stock += int(self.quantity)
            self.product.save()

