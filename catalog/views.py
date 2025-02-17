from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, Http404
from .models import CatalogConfig, CatalogFavorites
from products.models import Product, Category
from .constants import DISPLAY_OPTIONS
import json

from django.contrib import messages
from django.urls import reverse_lazy
from .forms import CatalogConfigForm
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from products.models import Category

class CatalogView(ListView):
    template_name = 'catalog/catalog.html'
    context_object_name = 'products'
    model = Product

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener configuración
        if 'public_url' in self.kwargs:
            # URL pública específica
            catalog_config = get_object_or_404(CatalogConfig, 
                public_url=self.kwargs['public_url'], 
                is_active=True
            )
        else:
            # Si no hay URL pública, buscar una configuración activa
            if self.request.user.is_authenticated:
                # Usuario autenticado - buscar su configuración
                catalog_config = CatalogConfig.objects.filter(user=self.request.user).first()
            else:
                # Usuario no autenticado - usar cualquier configuración activa
                catalog_config = CatalogConfig.objects.filter(is_active=True).first()

            # Si no existe ninguna configuración, crear una por defecto
            if not catalog_config:
                if self.request.user.is_authenticated:
                    # Crear configuración para usuario autenticado
                    catalog_config = CatalogConfig.objects.create(
                        user=self.request.user,
                        theme_color='#3B82F6',
                        display_settings={
                            'show_sku': False,
                            'show_price': True,
                            'show_stock': False,
                            'show_description': True,
                            'show_brand': True,
                            'show_bulk_price': True
                        }
                    )
                else:
                    # Para usuarios no autenticados, mostrar 404 si no hay configuración
                    raise Http404("No hay catálogo disponible")

        context['config'] = catalog_config
        
        # Gestionar favoritos
        if not self.request.session.session_key:
            self.request.session.create()
            
        context['favorites'] = CatalogFavorites.objects.filter(
            session_id=self.request.session.session_key
        ).values_list('product_id', flat=True)
        
        # Agregar categorías al contexto
        context['categories'] = Category.objects.filter(is_active=True)
        
        return context
    

class CatalogConfigView(LoginRequiredMixin, UpdateView):
    model = CatalogConfig
    template_name = 'catalog/config.html'
    fields = ['theme_color', 'logo', 'is_active']
    success_url = '.'

    def get_object(self, queryset=None):
        return CatalogConfig.objects.get_or_create(
            user=self.request.user,
            defaults={
                'theme_color': '#3B82F6',
                'display_settings': {key: option['default'] for key, option in DISPLAY_OPTIONS.items()}
            }
        )[0]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['display_options'] = DISPLAY_OPTIONS
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        if form.is_valid():
            # Guardar configuraciones básicas
            response = self.form_valid(form)
            
            # Actualizar display_settings
            display_settings = {}
            for key in DISPLAY_OPTIONS.keys():
                display_settings[key] = request.POST.get(f'display_{key}') == 'on'
            
            self.object.display_settings = display_settings
            self.object.save()
            
            messages.success(request, 'Configuración guardada exitosamente')
            return response
        else:
            return self.form_invalid(form)
    


@csrf_exempt
@require_http_methods(["POST"])
def add_favorite(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        if not request.session.session_key:
            request.session.create()
            
        CatalogFavorites.objects.get_or_create(
            session_id=request.session.session_key,
            product_id=product_id
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def remove_favorite(request, product_id):
    try:
        if request.session.session_key:
            CatalogFavorites.objects.filter(
                session_id=request.session.session_key,
                product_id=product_id
            ).delete()
            
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    

def product_detail(request, pk):
    try:
        product = Product.objects.select_related('category').get(pk=pk)
        data = {
            'id': product.id,
            'name': product.name,
            'description': product.description or '',
            'price_unit': float(product.sale_price or 0),
            'price_bulk': float(product.bulk_sale_price or 0),
            'is_bulk': product.is_bulk,
            'stock': float(product.stock or 0) if not product.is_bulk else float(product.bulk_stock or 0),
            'sku': product.sku or '',
            'category': product.category.name if product.category else '',
            'images': [
                {
                    'url': product.image.url if product.image else '',
                    'is_primary': True
                }
            ],
            'has_bulk_option': product.has_bulk_sales,
            'unit_type': 'kg' if product.is_bulk else 'unidad'
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    
class FavoritesListView(ListView):
    template_name = 'catalog/favorites.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        if not self.request.session.session_key:
            return Product.objects.none()
        return Product.objects.filter(
            catalogfavorites__session_id=self.request.session.session_key
        )
    
class PublicCatalogView(ListView):
    template_name = 'catalog/public_catalog.html'
    context_object_name = 'products'

    def get_queryset(self):
        self.catalog = get_object_or_404(CatalogConfig, public_url=self.kwargs['public_url'], is_active=True)
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = self.catalog
        if not self.request.session.session_key:
            self.request.session.create()
        context['favorites'] = CatalogFavorites.objects.filter(
            session_id=self.request.session.session_key
        ).values_list('product_id', flat=True)
        return context