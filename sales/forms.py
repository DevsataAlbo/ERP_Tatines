# forms.py
from django import forms
from .models import Sale, SaleDetail
from django.forms import inlineformset_factory

class SaleEditForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['payment_method', 'status']

class SaleDetailEditForm(forms.ModelForm):
    class Meta:
        model = SaleDetail
        fields = ['product', 'quantity', 'unit_price']


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['payment_method', 'status']

SaleDetailFormSet = inlineformset_factory(
    Sale,
    SaleDetail,
    form=SaleDetailEditForm,
    fields=['product', 'quantity'],  
    extra=3,  
    can_delete=True  
)


