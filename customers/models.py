from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model

class Customer(models.Model):
    CUSTOMER_TYPES = [
        ('PERSON', 'Persona Natural'),
        ('COMPANY', 'Empresa'),
    ]

    # Campos básicos
    customer_type = models.CharField(
        max_length=10, 
        choices=CUSTOMER_TYPES,
        verbose_name="Tipo de Cliente"
    )
    
    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{1,2}\.\d{3}\.\d{3}[-][0-9kK]{1}$',
                message='RUT debe tener formato XX.XXX.XXX-X'
            )
        ],
        verbose_name="RUT"
    )
    
    # Campos para ambos tipos
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email"
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    address = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Dirección"
    )
    comuna = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Comuna"
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Región"
    )
    
    # Campos específicos según tipo
    # Para personas naturales
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nombres"
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Apellidos"
    )
    
    # Para empresas
    company_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nombre Empresa"
    )
    
    # Campos adicionales
    comments = models.TextField(
        blank=True,
        null=True,
        verbose_name="Comentarios"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Cliente Activo"
    )
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        verbose_name="Creado por"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['rut']

    def __str__(self):
        if self.customer_type == 'PERSON':
            return f"{self.first_name} {self.last_name} ({self.rut})"
        return f"{self.company_name} ({self.rut})"

    def get_full_name(self):
        if self.customer_type == 'PERSON':
            return f"{self.first_name} {self.last_name}"
        return self.company_name
    


    