from django import forms
from .models import CatalogConfig
from .constants import DISPLAY_OPTIONS

class CatalogConfigForm(forms.ModelForm):
    theme_color = forms.CharField(
        widget=forms.TextInput(
            attrs={'type': 'color', 'class': 'h-10 w-20'}
        )
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar el valor inicial de las opciones de visualización
        if self.instance.pk:
            self.initial['display_settings'] = self.instance.display_settings

    class Meta:
        model = CatalogConfig
        fields = ['theme_color', 'logo', 'is_active']

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Recoger todas las opciones de visualización del POST
        display_settings = {}
        for key in DISPLAY_OPTIONS.keys():
            field_name = f'display_{key}'
            display_settings[key] = self.data.get(field_name) == 'on'
        
        instance.display_settings = display_settings
        if commit:
            instance.save()
        return instance