from django.contrib import admin
from .models import CatalogConfig, CatalogFavorites

@admin.register(CatalogConfig)
class CatalogConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'subdomain', 'is_active')
    search_fields = ('user__username', 'subdomain')
    list_filter = ('is_active',)

@admin.register(CatalogFavorites)
class CatalogFavoritesAdmin(admin.ModelAdmin):
    list_display = ('product', 'session_id', 'added_at')
    search_fields = ('product__name', 'session_id')
    list_filter = ('added_at',)