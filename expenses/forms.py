from django import forms
from .models import Expense, Category

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'category', 
            'date', 
            'amount',
            'description', 
            'is_tax_included'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full p-2 bg-gray-50 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none'
            }),
            'date': forms.DateInput(attrs={
                'type': 'text',  # Para Flatpickr
                'class': 'w-full p-2 bg-gray-50 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none datepicker'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full pl-7 p-2 bg-gray-50 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none',
                'placeholder': 'Ingrese el monto'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 bg-gray-50 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none',
                'rows': 3,
                'placeholder': 'Descripción del gasto'
            }),
            'is_tax_included': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Remover user antes de llamar a super()
        super().__init__(*args, **kwargs)
        
        # Agrupar categorías
        categories = Category.objects.filter(is_main=False).select_related('parent')
        choices = []
        for cat in categories:
            group_name = cat.parent.name if cat.parent else "Otras"
            choices.append((cat.id, f"{cat.parent.name} > {cat.name}" if cat.parent else cat.name))
        
        self.fields['category'].choices = choices

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg p-2 bg-gray-100 border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Nombre de la categoría'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-lg p-2 bg-gray-100 border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Descripción de la categoría'
            }),
            'parent': forms.Select(attrs={
                'class': 'w-full rounded-lg p-2 bg-gray-100 border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar categorías principales
        self.fields['parent'].queryset = Category.objects.filter(is_main=True)
        self.fields['parent'].empty_label = "Seleccione una categoría principal"
        self.fields['parent'].label = "Categoría Principal"