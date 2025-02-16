from django.contrib import admin
from .models import Product, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'stock', 'sale_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'brand']
    list_editable = ['stock', 'is_active']
    readonly_fields = ['created', 'updated']