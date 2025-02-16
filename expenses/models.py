from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum
from django.urls import reverse

class Category(models.Model):
    """
    Categorías de gastos con soporte para estructura jerárquica.
    Las categorías principales son fijas y las subcategorías son gestionables.
    """
    name = models.CharField('Nombre', max_length=100)
    description = models.TextField('Descripción', blank=True, null=True)
    order = models.IntegerField('Orden', default=0)
    is_main = models.BooleanField('Es categoría principal', default=False)
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        verbose_name='Categoría padre'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Creado por'
    )
    is_active = models.BooleanField('Activa', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['order', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def clean(self):
        if self.is_main and self.parent:
            raise ValidationError('Una categoría principal no puede tener padre')
        if not self.is_main and not self.parent:
            raise ValidationError('Una subcategoría debe tener una categoría padre')

    def get_absolute_url(self):
        return reverse('expenses:category_detail', args=[self.pk])

class Expense(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name='Categoría'
    )
    amount = models.IntegerField('Monto')
    description = models.TextField('Descripción', blank=True, null=True)
    date = models.DateField('Fecha')
    accounting_month = models.IntegerField('Mes Contable')
    accounting_year = models.IntegerField('Año Contable')
    is_tax_included = models.BooleanField('IVA Incluido', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['accounting_year', 'accounting_month']),
        ]

    def __str__(self):
        return f"{self.category} - ${self.amount:,}"

    def save(self, *args, **kwargs):
        # Asignar mes y año contable automáticamente si no están establecidos
        if not self.accounting_month or not self.accounting_year:
            self.accounting_month = self.date.month
            self.accounting_year = self.date.year
        
        # Verificar estado del mes - si está cerrado o debe estarlo
        month_status = self.get_month_status(self.date.year, self.date.month)
        if month_status == 'CLOSED':
            raise ValidationError("No se pueden modificar gastos en meses cerrados")
            
        # Verificar si el mes está explícitamente cerrado
        if MonthlyClose.objects.filter(
            month=self.accounting_month,
            year=self.accounting_year
        ).exists():
            raise ValidationError('No se pueden modificar gastos de un mes cerrado')
                
        super().save(*args, **kwargs)

    def calculate_tax(self):
        """Calcula el IVA del gasto"""
        if self.is_tax_included:
            neto = round(self.amount / 1.19)
            iva = self.amount - neto
            return {'neto': neto, 'iva': iva}
        return {'neto': self.amount, 'iva': 0}
    
    @classmethod
    def get_month_status(cls, year, month):
        """Verifica si un mes debe estar cerrado"""
        today = timezone.now()
        check_date = datetime(year, month, 1).date()
        
        # Si el mes es anterior al actual, debe estar cerrado
        if (check_date.year < today.year) or \
           (check_date.year == today.year and check_date.month < today.month):
            
            # Intentar cerrar si no lo está
            MonthlyClose.objects.get_or_create(
                year=year,
                month=month,
                defaults={
                    'closed_at': timezone.now(),
                    'total_amount': cls.objects.filter(
                        date__year=year,
                        date__month=month
                    ).aggregate(Sum('amount'))['amount__sum'] or 0
                }
            )
            return 'CLOSED'
            
        return 'OPEN'

class MonthlyClose(models.Model):
    """
    Control de cierres mensuales.
    Una vez cerrado el mes, los gastos no pueden modificarse.
    """
    month = models.IntegerField('Mes')
    year = models.IntegerField('Año')
    closed_at = models.DateTimeField('Fecha de Cierre', auto_now_add=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Cerrado por'
    )
    total_amount = models.IntegerField('Monto Total')
    notes = models.TextField('Notas', blank=True, null=True)

    class Meta:
        verbose_name = 'Cierre Mensual'
        verbose_name_plural = 'Cierres Mensuales'
        unique_together = ['month', 'year']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"Cierre {self.month}/{self.year}"

    def clean(self):
        # Validar que no exista un mes posterior cerrado
        if MonthlyClose.objects.filter(
            models.Q(year__gt=self.year) |
            models.Q(year=self.year, month__gt=self.month)
        ).exists():
            raise ValidationError('Existen meses posteriores cerrados')

    @classmethod
    def can_close_month(cls, month, year):
        """Verifica si un mes puede ser cerrado"""
        # Verificar que no esté cerrado
        if cls.objects.filter(month=month, year=year).exists():
            return False, 'El mes ya está cerrado'
        
        # Verificar que existan gastos
        if not Expense.objects.filter(
            accounting_month=month,
            accounting_year=year
        ).exists():
            return False, 'No hay gastos registrados en el mes'
            
        return True, ''