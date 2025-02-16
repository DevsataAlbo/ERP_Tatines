from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, ProductStock
from django.core.exceptions import ValidationError
from django.utils import timezone
import decimal
from decimal import Decimal
from django.utils.timezone import now
from django.db import transaction, models
from payment_providers.models import PaymentProvider
from .utils import round_money
from customers.models import Customer


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('CASH', 'Efectivo'),
        ('TRANSFER', 'Transferencia'),
        ('DEBIT', 'Tarjeta Débito'),
        ('CREDIT', 'Tarjeta Crédito'),
    ]

    SALE_STATUS = [
        ('COMPLETED', 'Completada'),
        ('PENDING', 'Pendiente de Pago'),
        ('CANCELLED', 'Anulada'),
    ]

    number = models.CharField(max_length=10, unique=True, verbose_name="Número de venta")
    
    date = models.DateTimeField(
        verbose_name="Fecha y hora",
        default=now,  # Fecha actual por defecto
        help_text="Fecha y hora de la venta. Si no se especifica, se usará la fecha actual."
    )

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_sale_number()
        if not self.date:
            self.date = timezone.now()
        super().save(*args, **kwargs)

    payment_method = models.CharField(
        max_length=10, 
        choices=PAYMENT_CHOICES,
        verbose_name="Método de pago"
    )
    total = models.IntegerField(default=0, verbose_name="Total")
    status = models.CharField(
        max_length=10,
        choices=SALE_STATUS,
        default='COMPLETED',
        verbose_name="Estado"
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        verbose_name="Usuario"
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Cliente"
    )

    is_stock_deducted = models.BooleanField(default=False, verbose_name="Stock descontado")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    is_modified = models.BooleanField(default=False, verbose_name="Modificada")

    payment_provider = models.ForeignKey(
        'payment_providers.PaymentProvider',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Proveedor de pago"
    )
    installments = models.IntegerField(
        choices=PaymentProvider.INSTALLMENT_CHOICES,
        null=True, 
        blank=True,
        verbose_name="Cuotas cliente"
    )
    provider_installments = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Cuotas a recibir",
        help_text="Número de cuotas en que el proveedor realizará el pago"
    )

    commission_amount = models.IntegerField(
        default=0,
        verbose_name="Monto comisión"
    )
    
    commission_tax = models.IntegerField(
        default=0,
        verbose_name="IVA comisión"
    )

    def get_neto_venta(self):
        """Retorna el monto neto de la venta (sin IVA)"""
        return int(round(self.total / Decimal('1.19')))

    def get_iva_venta(self):
        """Retorna el IVA de la venta"""
        return self.total - self.get_neto_venta()

    def get_desglose_completo(self):
        """Retorna un diccionario con todos los montos desglosados"""
        neto_venta = self.get_neto_venta()
        iva_venta = self.get_iva_venta()
        comision_total = self.get_total_commission()
        rentabilidad = self.calculate_net_profit()
        
        return {
            'neto_venta': neto_venta,
            'iva_venta': iva_venta,
            'comision_base': self.commission_amount,
            'iva_comision': self.commission_tax,
            'comision_total': comision_total,
            'rentabilidad': rentabilidad,
            'total': self.total
        }

    def calculate_commission(self):
        """Calcula y guarda la comisión de la venta"""
        if self.payment_method in ['DEBIT', 'CREDIT'] and self.payment_provider:
            is_credit = self.payment_method == 'CREDIT'
            commission_data = self.payment_provider.calculate_commission(self.total, is_credit)
            
            self.commission_amount = commission_data['commission']
            self.commission_tax = commission_data['tax']
            self.save()
            
            # print(f"""
            #     Debug - Comisiones:
            #     Monto venta: {self.total}
            #     Tasa: {commission_data['rate']}%
            #     Comisión base: {self.commission_amount}
            #     IVA comisión: {self.commission_tax}
            #     Total comisión: {self.get_total_commission()}
            # """)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-date']

    def __str__(self):
        return f"Venta #{self.number}"
    
    def get_total_commission(self):
        """Calcula el total de la comisión incluyendo IVA"""
        # Ya están redondeados individualmente, solo sumar
        return self.commission_amount + self.commission_tax

    def calculate_net_profit(self):
        """Calcula la rentabilidad neta después de comisiones"""
        gross_profit = self.calculate_profit()
        total_commission = self.get_total_commission()
        # Redondear a entero
        return int(round(gross_profit - total_commission))

    def get_commission_percentage(self):
        """Calcula el porcentaje que representa la comisión sobre la venta"""
        if self.total > 0:
            total_commission = self.get_total_commission()
            return round((total_commission / self.total) * 100, 2)
        return 0

    def get_total_items(self):
        return self.saledetail_set.count()

    def calculate_total(self):
        return sum(detail.subtotal for detail in self.saledetail_set.all())

    def calculate_profit(self):
        """Calcula la ganancia total de la venta"""
        total_profit = sum(detail.calculate_profit() for detail in self.saledetail_set.all())
        return int(round(total_profit))

    @staticmethod
    def generate_sale_number():
        """Genera un número único para la venta de forma segura"""
        with transaction.atomic():
            # Obtenemos el último número de venta
            last_sale = Sale.objects.order_by('-number').first()
            if not last_sale:
                return 'VTA-00001'
        
            # Extraer el número y generar el siguiente
            last_number = int(last_sale.number.split('-')[1])
            new_number = last_number + 1
            return f'VTA-{str(new_number).zfill(5)}'

    def clean(self):
        if self.date > now():
            raise ValidationError("La fecha no puede ser futura.")

    def save(self, *args, **kwargs):
        if not self.number:
            with transaction.atomic():
                self.number = self.generate_sale_number()
                # Verificar que el número generado no exista
                while Sale.objects.filter(number=self.number).exists():
                    self.number = self.generate_sale_number()

        if self.installments is not None and self.payment_method == 'CREDIT':
            self.provider_installments = self.installments

        super().save(*args, **kwargs)
    
    def has_commission(self):
        """Verifica si la venta tiene comisiones aplicables"""
        return self.payment_method in ['DEBIT', 'CREDIT'] and self.payment_provider_id is not None

    def mark_as_modified(self):
        self.is_modified = True
        self.save()

class SaleDetail(models.Model):
    sale = models.ForeignKey(
        Sale, 
        on_delete=models.CASCADE, 
        verbose_name="Venta"
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        verbose_name="Producto"
    )
    
    # Campos para manejar cantidades normales y a granel
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Cantidad",
        help_text="Cantidad vendida (en sacos o kilos)"
    )
    is_bulk = models.BooleanField(
        default=False,
        verbose_name="Venta a granel",
        help_text="Indica si es una venta a granel"
    )
    
    # Precios y subtotales
    unit_price = models.IntegerField(
        verbose_name="Precio unitario",
        help_text="Precio por unidad o por kilo en caso de granel"
    )

    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio de compra",
        help_text="Precio de compra del producto en el momento de la venta"
    )
    
    subtotal = models.IntegerField(verbose_name="Subtotal")
    
    # Control de IVA
    is_tax_included = models.BooleanField(
        default=True, 
        verbose_name="Incluye IVA"
    )
    
    # Relación con los movimientos de stock (FIFO)
    stock_movements = models.ManyToManyField(
        'products.ProductStock',
        through='SaleStockMovement',
        verbose_name="Movimientos de stock",
        related_name='sale_details'
    )

    iva_debito = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="IVA Débito")
    iva_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="IVA Crédito")
    iva_a_pagar = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="IVA a Pagar")

    class Meta:
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"

    def __str__(self):
        return f"{self.product.name} - {self.quantity} {'kg' if self.is_bulk else 'unidades'}"

    def calculate_profit(self):
        try:
            quantity = Decimal(str(self.quantity))
            
            if self.is_bulk:
                # Para productos a granel, usamos los precios por kilo directamente
                if self.product.is_bulk:
                    # Producto que es exclusivamente a granel
                    precio_compra = self.purchase_price
                    precio_venta = self.unit_price
                else:
                    # Producto regular que se vende a granel (desde saco)
                    precio_compra_saco = round_money(self.product.purchase_price / Decimal('1.19'))
                    precio_compra = round_money(precio_compra_saco / self.product.kilos_per_sack)
                    precio_venta = self.unit_price

                # Cálculo de ganancia para granel
                ganancia_por_kilo = precio_venta - precio_compra
                ganancia_total = round_money(ganancia_por_kilo * quantity)
                
                return ganancia_total
            else:
                # Para productos por unidad
                precio_compra_con_iva = Decimal(str(self.purchase_price))
                precio_compra_sin_iva = (precio_compra_con_iva / Decimal('1.19')).quantize(Decimal('0.01'))
                self.iva_credito = (precio_compra_con_iva - precio_compra_sin_iva).quantize(Decimal('0.01'))
                
                # Precio de venta sin IVA
                precio_venta_con_iva = Decimal(str(self.unit_price))
                precio_venta_sin_iva = (precio_venta_con_iva / Decimal('1.19')).quantize(Decimal('0.01'))
                
                # IVA débito
                self.iva_debito = (precio_venta_con_iva - precio_venta_sin_iva).quantize(Decimal('0.01'))
                
                # IVA a pagar
                self.iva_a_pagar = (self.iva_debito - self.iva_credito).quantize(Decimal('0.01'))
                
                # Rentabilidad
                rentabilidad_unitaria = precio_venta_sin_iva - precio_compra_sin_iva
                rentabilidad_total = rentabilidad_unitaria * quantity
                
                self.save()
                return int(round(rentabilidad_total))

        except Exception as e:
            print(f"Error calculando ganancia para {self.product.name}: {str(e)}")
            return 0


    def save(self, *args, **kwargs):
        if self.is_bulk:
            # Para ventas a granel, mantener el subtotal exacto que viene del frontend
            self.subtotal = int(self.quantity * self.unit_price)
            if hasattr(self, '_original_subtotal'):
                self.subtotal = self._original_subtotal
        else:
            self.subtotal = int(self.quantity * self.unit_price)
        super().save(*args, **kwargs)

    def clean(self):
        if not self.pk:  # Solo para nuevos registros
            if self.is_bulk and not self.product.has_bulk_sales:
                raise ValidationError('Este producto no permite ventas a granel')
            
            if self.is_bulk and self.product.bulk_stock < self.quantity:
                raise ValidationError('Stock insuficiente para venta a granel')
            elif not self.is_bulk and self.product.stock < self.quantity:
                raise ValidationError('Stock insuficiente')

class SaleStockMovement(models.Model):
    sale_detail = models.ForeignKey(
        SaleDetail, 
        on_delete=models.CASCADE,
        verbose_name="Detalle de venta"
    )
    stock_movement = models.ForeignKey(
        'products.ProductStock',
        on_delete=models.CASCADE,
        verbose_name="Movimiento de stock"
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Cantidad",
        help_text="Cantidad tomada de este lote"
    )

    class Meta:
        verbose_name = "Movimiento de Stock en Venta"
        verbose_name_plural = "Movimientos de Stock en Ventas"

    def __str__(self):
        return f"Venta {self.sale_detail.sale.number} - {self.stock_movement.batch_number}"
    




