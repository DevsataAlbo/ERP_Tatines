from django import forms
from .models import Supplier

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'rut', 'business_name', 
            'contact_name', 'phone', 'alternative_phone',
            'email', 'alternative_email', 'address',
            'city', 'region', 'website', 'notes', 
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Nombre o Razón Social'
            }),
            'rut': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'XX.XXX.XXX-X'
            }),
            'business_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'contact_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': '+56XXXXXXXXX'
            }),
            'alternative_phone': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'alternative_email': forms.EmailInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'region': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            })
        }