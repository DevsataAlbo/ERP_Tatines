from django.contrib import admin
from .models import Sale, SaleDetail

class SaleDetailInline(admin.TabularInline):
    model = SaleDetail
    extra = 0
    readonly_fields = ['product', 'quantity', 'unit_price', 'subtotal', 'is_tax_included']
    can_delete = False

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['number', 'date', 'user', 'total', 'status', 'payment_method', 'is_stock_deducted']
    list_filter = ['status', 'payment_method', 'date']
    search_fields = ['number', 'user__username']
    readonly_fields = ['number', 'date', 'total', 'user', 'is_stock_deducted']
    inlines = [SaleDetailInline]  

@admin.register(SaleDetail)
class SaleDetailAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'unit_price', 'subtotal']
    search_fields = ['sale__number', 'product__name']
    readonly_fields = ['sale', 'product', 'quantity', 'unit_price', 'subtotal', 'is_tax_included']
