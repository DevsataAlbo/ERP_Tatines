from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_type', 'rut', 'email', 'phone',
            'address', 'comuna', 'region', 'first_name',
            'last_name', 'company_name', 'comments'
        ]
        widgets = {
            'customer_type': forms.Select(attrs={'class': 'form-select block w-full rounded-lg border-gray-300'}),
            'rut': forms.TextInput(attrs={'class': 'form-input block w-full rounded-lg border-gray-300', 'placeholder': '12.345.678-9'}),
            'email': forms.EmailInput(attrs={'class': 'form-input block w-full rounded-lg border-gray-300'}),
            'phone': forms.TextInput(attrs={'class': 'form-input block w-full rounded-lg border-gray-300'}),
            'address': forms.TextInput(attrs={'class': 'form-input block w-full rounded-lg border-gray-300'}),
            'comuna': forms.TextInput(attrs={'class': 'form-input block w-full rounded-lg border-gray-300'}),
            'region': forms.TextInput(attrs={'class': 'form-input block w-full rounded-lg border-gray-300'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input block w-full rounded-lg border-gray-300'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input block w-full rounded-lg border-gray-300'}),
            'company_name': forms.TextInput(attrs={'class': 'form-input block w-full rounded-lg border-gray-300'}),
            'comments': forms.Textarea(attrs={'class': 'form-textarea block w-full rounded-lg border-gray-300', 'rows': 3}),
        }


        