from django.db import models
from django.conf import settings
from decimal import Decimal

class InventoryCount(models.Model):
    """Modelo principal para el control de inventarios"""
    
    INVENTORY_STATUS = [
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('pending_review', 'Pendiente de Revisión'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    name = models.CharField('Nombre', max_length=100)
    date_started = models.DateTimeField('Fecha de inicio', auto_now_add=True)
    date_finished = models.DateTimeField('Fecha de finalización', null=True, blank=True)
    status = models.CharField(
        'Estado', 
        max_length=20, 
        choices=INVENTORY_STATUS, 
        default='draft'
    )
    notes = models.TextField('Notas', blank=True)
    
    # Responsables
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='inventory_counts_created',
        verbose_name='Creado por'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='inventory_counts_reviewed',
        null=True,
        blank=True,
        verbose_name='Revisado por'
    )

    # Filtros opcionales
    categories = models.ManyToManyField(
        'products.Category',
        blank=True,
        verbose_name='Categorías'
    )

    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conteo de Inventario'
        verbose_name_plural = 'Conteos de Inventario'
        ordering = ['-date_started']

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

    @property
    def progress_percentage(self):
        """Calcula el porcentaje de avance del conteo"""
        total_products = self.details.count()
        if total_products == 0:
            return 0
        counted_products = self.details.exclude(actual_quantity=None).count()
        return int((counted_products / total_products) * 100)

    @property
    def total_difference_amount(self):
        """Calcula la diferencia total en valor monetario"""
        total = Decimal('0.0')
        for detail in self.details.all():
            total += detail.difference_amount
        return total

class InventoryCountDetail(models.Model):
    """Detalle de cada producto en el conteo de inventario"""
    
    inventory_count = models.ForeignKey(
        InventoryCount,
        on_delete=models.CASCADE,
        related_name='details'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT
    )
    expected_quantity = models.DecimalField(
        'Cantidad esperada',
        max_digits=10,
        decimal_places=2
    )
    actual_quantity = models.DecimalField(
        'Cantidad real',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Responsable del conteo
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='product_counts',
        null=True,
        blank=True,
        verbose_name='Contado por'
    )
    
    last_counted_at = models.DateTimeField(
        'Último conteo',
        null=True,
        blank=True
    )

    notes = models.TextField('Observaciones', blank=True)

    # Campos nuevos para reconteo
    recount_requested = models.BooleanField(
        'Reconteo solicitado',
        default=False
    )

    recount_reason = models.TextField(
        'Motivo de reconteo',
        blank=True
    )

    recount_requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recount_requests',
        null=True,
        blank=True,
        verbose_name='Solicitado por'
    )

    recount_count = models.IntegerField(
        'Número de reconteos',
        default=0
    )
    
    previous_counts = models.JSONField(
        'Conteos anteriores',
        default=dict,
        blank=True
    )

    class Meta:
        verbose_name = 'Detalle de Conteo'
        verbose_name_plural = 'Detalles de Conteo'
        unique_together = ['inventory_count', 'product']

    def __str__(self):
        return f"{self.product.name} - {self.inventory_count.name}"

    @property
    def difference_quantity(self):
        """Calcula la diferencia entre cantidad esperada y real"""
        if self.actual_quantity is None:
            return None
        return self.actual_quantity - self.expected_quantity

    @property
    def difference_percentage(self):
        """Calcula el porcentaje de diferencia"""
        if self.actual_quantity is None or self.expected_quantity == 0:
            return None
        return ((self.actual_quantity - self.expected_quantity) / self.expected_quantity) * 100

    @property
    def difference_amount(self):
        """Calcula la diferencia en valor monetario"""
        if self.difference_quantity is None:
            return Decimal('0.0')
        return self.difference_quantity * self.product.weighted_average_price

class InventoryAdjustment(models.Model):
    """Registro de ajustes de inventario"""
    
    ADJUSTMENT_STATUS = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]

    inventory_count = models.ForeignKey(
        InventoryCount,
        on_delete=models.CASCADE,
        related_name='adjustments'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT
    )
    quantity_difference = models.DecimalField(
        'Diferencia de cantidad',
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=ADJUSTMENT_STATUS,
        default='pending'
    )
    
    # Montos
    amount = models.DecimalField(
        'Monto del ajuste',
        max_digits=10,
        decimal_places=2
    )
    
    # Responsables
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='adjustments_created'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='adjustments_approved',
        null=True,
        blank=True
    )

    inventory_count_detail = models.ForeignKey(
        'InventoryCountDetail',
        on_delete=models.PROTECT,
        related_name='adjustments',
        null=True,
        blank=True,
        verbose_name='Detalle de inventario origen'
    )
    
    applied = models.BooleanField(
        default=False,
        verbose_name='Ajuste aplicado'
    )
    
    justification = models.TextField('Justificación')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ajuste de Inventario'
        verbose_name_plural = 'Ajustes de Inventario'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ajuste {self.product.name} - {self.get_status_display()}"