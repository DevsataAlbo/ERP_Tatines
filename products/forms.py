from django import forms
from .models import Product, StockEntry, StockEntryDetail
from suppliers.models import Supplier
from datetime import datetime
from django.forms import inlineformset_factory


class ProductForm(forms.ModelForm):
    initial_batch_number = forms.CharField(
        required=False,
        label='Número de Lote',
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
        })
    )
    expiration_date = forms.DateField(
        required=False,
        label='Fecha de Vencimiento',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
        })
    )
    linked_products = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Product.objects.none(),
        label='Productos que pueden abrirse',
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
        })
    )

    class Meta:
        model = Product
        fields = [
            'name', 'brand', 'category', 'description', 
            'purchase_price', 'is_purchase_with_tax', 
            'sale_price', 'is_sale_with_tax',
            'has_bulk_sales', 'kilos_per_sack', 'bulk_sale_price',  # Campos de granel actuales
            'stock', 'image', 'is_active',
            'requires_expiration',
            'is_bulk', 'linked_products'  # Nuevos campos
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer is_active como True por defecto en creación
        if not self.instance.pk:  # Si es nuevo producto
            self.initial['is_active'] = True
        # Aplicar clases de Tailwind a todos los campos
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select)):
                field.widget.attrs['class'] = 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
                field.widget.attrs['rows'] = 3
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'

        # Configurar los campos de granel
        self.fields['has_bulk_sales'].label = '¿Vende a granel?'
        self.fields['bulk_sale_price'].label = 'Precio de venta por kilo'
        self.fields['requires_expiration'].widget.attrs['class'] = 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        self.fields['requires_expiration'].label = '¿Requiere control de vencimiento?'
        self.fields['requires_expiration'].help_text = 'Marque esta opción si el producto necesita control de fecha de vencimiento'
        # Configuración específica para kilos_per_sack
        self.fields['kilos_per_sack'].label = 'Kilos por saco'
        self.fields['kilos_per_sack'].help_text = 'Indica cuántos kilos contiene cada saco'
        self.fields['kilos_per_sack'].widget.attrs['step'] = '0.01'

        # Configurar linked_products
        base_queryset = Product.objects.filter(is_bulk=False)
        if self.instance.pk:
            # Si estamos editando, excluir el producto actual y filtrar por marca
            self.fields['linked_products'].queryset = base_queryset.filter(
                brand=self.instance.brand
            ).exclude(pk=self.instance.pk)
        else:
            # Si es nuevo producto, mostrar todos los productos no granel
            self.fields['linked_products'].queryset = base_queryset

        # Campos de vencimiento inicialmente ocultos
        self.fields['initial_batch_number'].widget.attrs['class'] += ' expiration-fields'
        self.fields['expiration_date'].widget.attrs['class'] += ' expiration-fields'

    def clean(self):
        cleaned_data = super().clean()
        is_bulk = cleaned_data.get('is_bulk')
        has_bulk_sales = cleaned_data.get('has_bulk_sales')
        kilos_per_sack = cleaned_data.get('kilos_per_sack')
        
        # Validación básica de kilos por saco
        if not is_bulk and has_bulk_sales and not kilos_per_sack:
            raise forms.ValidationError(
                "Debe especificar los kilos por saco para productos que pueden venderse a granel"
            )
        
        if kilos_per_sack and kilos_per_sack <= 0:
            raise forms.ValidationError(
                "Los kilos por saco deben ser mayores a 0"
            )

        if is_bulk:
            # Validaciones para productos a granel
            bulk_sale_price = cleaned_data.get('bulk_sale_price')
            linked_products = cleaned_data.get('linked_products', [])
            
            if not bulk_sale_price:
                raise forms.ValidationError(
                    "Debe especificar un precio de venta por kilo para productos a granel."
                )
            if not linked_products:
                raise forms.ValidationError(
                    "Debe seleccionar al menos un producto para abrir cuando es venta a granel."
                )
                
            # Validar que los productos vinculados sean de la misma marca
            brand = cleaned_data.get('brand')
            invalid_products = linked_products.exclude(brand=brand)
            if invalid_products.exists():
                raise forms.ValidationError(
                    "Solo puede vincular productos de la misma marca."
                )
        else:
            # Validaciones para productos normales
            purchase_price = cleaned_data.get('purchase_price')
            sale_price = cleaned_data.get('sale_price')
            is_purchase_with_tax = cleaned_data.get('is_purchase_with_tax')
            is_sale_with_tax = cleaned_data.get('is_sale_with_tax')
            requires_expiration = cleaned_data.get('requires_expiration')

            # Validar precios normales
            if purchase_price and sale_price:
                purchase_net = int(purchase_price / 1.19) if is_purchase_with_tax else purchase_price
                sale_net = int(sale_price / 1.19) if is_sale_with_tax else sale_price

                if sale_net <= purchase_net:
                    raise forms.ValidationError(
                        "El precio de venta neto debe ser mayor al precio de compra neto."
                    )

            # Validar campos de granel para productos con venta a granel
            if has_bulk_sales:
                if not kilos_per_sack:
                    raise forms.ValidationError(
                        "Debe especificar los kilos por saco para ventas a granel."
                    )
                
                bulk_sale_price = cleaned_data.get('bulk_sale_price')
                if not bulk_sale_price:
                    raise forms.ValidationError(
                        "Debe especificar el precio de venta por kilo para ventas a granel."
                    )

                # Calcular precio por kilo del saco para comparar rentabilidad
                purchase_net = int(purchase_price / 1.19) if is_purchase_with_tax else purchase_price
                kilo_cost = purchase_net / kilos_per_sack
                if bulk_sale_price <= kilo_cost:
                    raise forms.ValidationError(
                        "El precio de venta por kilo debe ser mayor al costo por kilo."
                    )
                
                # Advertencia sobre control de vencimiento
                if requires_expiration:
                    cleaned_data['_warning'] = (
                        "Este producto requiere control de vencimiento y se vende a granel. " 
                        "Asegúrese de mantener un control adecuado de los lotes al abrir sacos."
                    )

            # Limpiar campos de granel si no es producto a granel y no tiene ventas a granel
            if not has_bulk_sales:
                cleaned_data['linked_products'] = []
                cleaned_data['bulk_sale_price'] = None

        # Asegurar que is_active siempre sea True en el frontend
        cleaned_data['is_active'] = True
        return cleaned_data
    

class OpenSackForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        label='Cantidad de sacos a abrir',
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'min': '1'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'rows': '3',
            'placeholder': 'Notas adicionales sobre la apertura de sacos'
        })
    )

    def __init__(self, product, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self.fields['quantity'].widget.attrs['max'] = product.stock

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity > self.product.stock:
            raise forms.ValidationError('No hay suficiente stock disponible')
        return quantity
    
class MermaForm(forms.Form):
    quantity = forms.DecimalField(  # Cambiamos a DecimalField para permitir decimales
        min_value=0.01,
        label='Cantidad',
        widget=forms.NumberInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
            'min': '0.01',
            'step': '0.01'  # Permitir decimales
        })
    )
    reason = forms.ChoiceField(
        choices=[
            ('EXPIRATION', 'Vencimiento'),
            ('DAMAGE', 'Daño/Deterioro'),
            ('LOSS', 'Pérdida'),
            ('OTHER', 'Otro')
        ],
        label='Motivo',
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
            'rows': '3',
            'placeholder': 'Observaciones adicionales'
        })
    )

    def __init__(self, product, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        
        # Ajustar etiqueta según tipo de producto
        if product.is_bulk:
            self.fields['quantity'].label = 'Cantidad (kg)'
            self.fields['quantity'].widget.attrs['max'] = product.bulk_stock
        else:
            self.fields['quantity'].label = 'Cantidad (unidades)'
            self.fields['quantity'].widget.attrs['max'] = product.stock

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if not quantity or quantity <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor a 0')
        
        if self.product.is_bulk:
            if quantity > self.product.bulk_stock:
                raise forms.ValidationError(f'No hay suficiente stock a granel. Stock actual: {self.product.bulk_stock} kg')
        else:
            if quantity > self.product.stock:
                raise forms.ValidationError(f'No hay suficiente stock. Stock actual: {self.product.stock} unidades')
        return quantity
    
class StockEntryForm(forms.ModelForm):
    class Meta:
        model = StockEntry
        fields = ['date', 'supplier', 'document_type', 'document_number', 'notes']
        widgets = {
            'date': forms.DateInput(
                format='%Y-%m-%d',  # Definimos explícitamente el formato que esperamos
                attrs={
                    'type': 'text',  # Usamos type="text" para que Flatpickr funcione correctamente
                    'class': 'w-full p-2 bg-gray-50 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none datepicker',
                    'autocomplete': 'off'  # Evitamos la autocompletación del navegador
                }
            ),
            'supplier': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'document_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'document_number': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            })
        }

    def clean_date(self):
        """
        Método para validar y limpiar el campo de fecha.
        Este método se ejecuta automáticamente durante la validación del formulario.
        """
        date = self.cleaned_data.get('date')
        if not date:
            raise forms.ValidationError('La fecha es requerida')
        
        # Si la fecha viene como string, intentamos convertirla al formato correcto
        if isinstance(date, str):
            try:
                from datetime import datetime
                date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                raise forms.ValidationError('Formato de fecha inválido. Use YYYY-MM-DD')
        return date

class StockEntryDetailForm(forms.ModelForm):
    """
    Formulario para los detalles de cada producto en el ingreso.
    Se usará de manera dinámica en el frontend para agregar múltiples productos.
    """
    class Meta:
        model = StockEntryDetail
        fields = ['product', 'quantity', 'purchase_price', 'is_price_with_tax', 
                 'expiration_date', 'batch_number']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'min': '0'
            }),
            'expiration_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expiration_date'].required = False
        self.fields['batch_number'].required = False

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        expiration_date = cleaned_data.get('expiration_date')

        # Validar fecha de vencimiento si el producto lo requiere
        if product and product.requires_expiration and not expiration_date:
            raise forms.ValidationError(
                'Este producto requiere fecha de vencimiento'
            )

        return cleaned_data
    
