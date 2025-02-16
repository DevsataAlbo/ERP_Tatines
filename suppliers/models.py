from django.db import models
from django.core.validators import RegexValidator
from django.urls import reverse

class Supplier(models.Model):
    """
    Modelo para gestionar la información de proveedores.
    Mantiene los datos básicos y de contacto de cada proveedor.
    """
    # Información básica
    name = models.CharField('Nombre o Razón Social', max_length=200)
    rut = models.CharField(
        'RUT', 
        max_length=12,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{1,2}\.\d{3}\.\d{3}[-][0-9kK]{1}$',
                message='RUT debe tener formato XX.XXX.XXX-X'
            )
        ]
    )
    business_name = models.CharField('Nombre de Fantasía', max_length=200, blank=True)
    
    # Información de contacto
    contact_name = models.CharField('Nombre de Contacto', max_length=100, blank=True)
    phone = models.CharField(
        'Teléfono Principal',
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Número de teléfono debe estar en formato +56XXXXXXXXX'
            )
        ]
    )
    alternative_phone = models.CharField('Teléfono Alternativo', max_length=15, blank=True)
    email = models.EmailField('Email Principal')
    alternative_email = models.EmailField('Email Alternativo', blank=True)
    
    # Dirección
    address = models.CharField('Dirección', max_length=255)
    city = models.CharField('Ciudad', max_length=100)
    region = models.CharField('Región', max_length=100)
    
    # Información adicional
    website = models.URLField('Sitio Web', blank=True)
    notes = models.TextField('Notas', blank=True)
    
    # Control
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rut})"

    def get_absolute_url(self):
        return reverse('suppliers:detail', kwargs={'pk': self.pk})

    @property
    def full_address(self):
        """Retorna la dirección completa formateada"""
        return f"{self.address}, {self.city}, {self.region}"