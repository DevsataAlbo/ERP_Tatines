from django.contrib import admin
from .models import PaymentProvider

@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
   list_display = [
       'name', 
       'debit_commission_rate', 
       'credit_commission_rate',
       'commission_includes_tax',
       'deposit_delay_days',
       'is_default'
   ]
   list_editable = ['is_default']
   list_filter = ['is_default', 'commission_includes_tax', 'machine_rental']
   search_fields = ['name']

   def save_model(self, request, obj, form, change):
       # Si este proveedor se marca como default, quitar el default de los otros
       if obj.is_default:
           PaymentProvider.objects.exclude(pk=obj.pk).update(is_default=False)
       super().save_model(request, obj, form, change)