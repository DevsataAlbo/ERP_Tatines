from django.db import models
from decimal import Decimal
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP

class PaymentProvider(models.Model):
    INSTALLMENT_CHOICES = [
        (0, 'Sin cuotas (Pago único)'),
        (3, '3 cuotas'),
        (6, '6 cuotas'),
        (12, '12 cuotas'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nombre")
    debit_commission_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        verbose_name="Comisión Débito (%)"
    )
    credit_commission_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        verbose_name="Comisión Crédito (%)"
    )
    max_installments = models.IntegerField(  
        verbose_name="Máximo de cuotas",
        help_text="Número máximo de cuotas permitidas",
        null=True,  # Permitir nulos temporalmente
        blank=True  # Permitir blancos en formularios
    )
    is_default = models.BooleanField(  
        default=False,
        verbose_name="Proveedor por defecto"
    )
    commission_includes_tax = models.BooleanField(
        default=True, 
        verbose_name="Comisión incluye IVA"
    )
    deposit_delay_days = models.IntegerField(verbose_name="Días para depósito")
    machine_rental = models.BooleanField(
        default=False,
        verbose_name="Arriendo de máquina"
    )
    machine_rental_cost = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Costo arriendo mensual"
    )
    electronic_billing = models.BooleanField(
        default=False,
        verbose_name="Emisión boletas electrónicas"
    )
    electronic_billing_cost = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Costo mensual boletas"
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name="Proveedor por defecto"
    )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_default and not self._state.adding:  # Si se está actualizando
                # Desmarcar otros proveedores por defecto
                PaymentProvider.objects.exclude(pk=self.pk).filter(is_default=True).update(is_default=False)
            elif self.is_default and self._state.adding:  # Si es nuevo
                # Desmarcar todos los proveedores por defecto
                PaymentProvider.objects.filter(is_default=True).update(is_default=False)
            super().save(*args, **kwargs)

    def calculate_commission(self, amount, is_credit=False):
        """
        Calcula la comisión basada en el monto de venta
        """
        amount = Decimal(str(amount))
        rate = (self.credit_commission_rate if is_credit else self.debit_commission_rate)
        
        # Calcular comisión base y redondear a entero
        commission = (amount * rate / Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

        # Calcular IVA de la comisión
        commission_tax = (commission * Decimal('0.19')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

        print(f"""
            Cálculo detallado comisión:
            Monto venta: ${amount}
            Tasa: {rate}%
            Comisión base calculada: ${commission}
            IVA comisión calculado: ${commission_tax}
            Total comisión: ${commission + commission_tax}
        """)

        return {
            'commission': commission,
            'tax': commission_tax,
            'total': commission + commission_tax,
            'rate': rate
        }

    class Meta:
        verbose_name = "Proveedor de Medios de Pago"
        verbose_name_plural = "Proveedores de Medios de Pago"

    def __str__(self):
        return self.name