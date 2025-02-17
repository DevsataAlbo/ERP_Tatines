import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from .constants import DISPLAY_OPTIONS

class CatalogConfig(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subdomain = models.CharField(max_length=100, unique=True)
    theme_color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    logo = models.ImageField(upload_to='catalogs/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_settings = models.JSONField(default=dict)
    public_url = models.CharField(max_length=100, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.public_url:
            self.public_url = f'catalog-{uuid.uuid4().hex[:8]}'
        if not self.subdomain:
            self.subdomain = self.public_url
        if not self.created_at:
            self.created_at = timezone.now()

        # Inicializar display_settings si está vacío
        if not self.display_settings:
            self.display_settings = {
                'show_sku': False,
                'show_price': True,
                'show_stock': False,
                'show_description': True,
                'show_brand': True,
                'show_bulk_price': True
            }
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Configuración de Catálogo'
        verbose_name_plural = 'Configuraciones de Catálogo'

    def __str__(self):
        return f"Catálogo de {self.user.username}"

class CatalogFavorites(models.Model):
    session_id = models.CharField(max_length=100)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session_id', 'product']
        indexes = [
            models.Index(fields=['session_id', 'added_at'])
        ]
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'

    def __str__(self):
        return f"Favorito: {self.product.name}"