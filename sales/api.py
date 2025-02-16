from django.http import JsonResponse
from django.db.models import Q
from products.models import Product
import json
from django.views.decorators.http import require_http_methods
from .views import calculate_bulk_quantity
from decimal import Decimal
import decimal

def search_products(request):
    term = request.GET.get('term', '').strip()
    print(f"Término de búsqueda: {term}")

    if len(term) < 2:
        return JsonResponse([], safe=False)

    products = Product.objects.filter(
        Q(name__icontains=term) | Q(brand__icontains=term),
        is_active=True
    ).order_by('name')

    product_list = []
    for product in products:
        # Productos a granel
        if product.is_bulk and product.bulk_stock > 0:
            product_list.append({
                'id': product.id,
                'name': f"{product.name} (Granel)",
                'brand': product.brand if product.brand else '',
                'is_bulk': True,
                'bulk_stock': float(product.bulk_stock),
                'price_per_kilo': product.bulk_sale_price,
                'unit': 'kg',
                'sale_price': product.bulk_sale_price
            })
        # Productos normales que pueden venderse a granel
        elif product.has_bulk_sales and product.bulk_stock > 0:
            product_list.append({
                'id': product.id,
                'name': product.name,
                'brand': product.brand if product.brand else '',
                'is_bulk': True,
                'bulk_stock': float(product.bulk_stock),
                'price_per_kilo': product.bulk_sale_price,
                'unit': 'kg',
                'sale_price': product.bulk_sale_price
            })
        # Productos con stock en unidades
        if not product.is_bulk and product.stock > 0:
            product_list.append({
                'id': product.id,
                'name': f"{product.name} {'(Unidad)' if product.has_bulk_sales else ''}",
                'brand': product.brand if product.brand else '',
                'is_bulk': False,
                'stock': product.stock,
                'unit': 'un',
                'sale_price': product.sale_price
            })

    print(f"Productos encontrados: {product_list}")
    return JsonResponse(product_list, safe=False)

@require_http_methods(["POST"])
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        product = Product.objects.get(id=product_id)
        is_bulk = data.get('is_bulk', False)

        if is_bulk:
            amount = Decimal(str(data.get('amount', 0)))
            if amount <= 0:
                return JsonResponse({'error': 'Ingrese un monto válido'}, status=400)
            quantity, final_amount = calculate_bulk_quantity(amount, product.bulk_sale_price)
            subtotal = final_amount
        else:
            quantity = float(data.get('quantity', 1))
            if not quantity.is_integer():
                return JsonResponse({'error': 'Solo cantidades enteras para productos por unidad'}, status=400)
            quantity = int(quantity)
            subtotal = quantity * product.sale_price

        # Validar stock
        stock_disponible = product.bulk_stock if is_bulk else product.stock
        if quantity > stock_disponible:
            return JsonResponse({
                'error': f'Stock insuficiente. Disponible: {stock_disponible}'
                + (' kg' if is_bulk else ' unidades')
            }, status=400)

        cart_item = {
            'product_id': product_id,
            'name': f"{product.name}{' (Granel)' if is_bulk else ''}",
            'quantity': float(quantity),
            'price': float(product.bulk_sale_price if is_bulk else product.sale_price),
            'is_bulk': is_bulk,
            'subtotal': float(subtotal)
        }

        cart = request.session.get('cart', [])
        cart.append(cart_item)
        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({'success': True, 'cart': cart})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def update_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = decimal.Decimal(str(data.get('quantity', 1)))
        is_bulk = data.get('is_bulk', False)

        if quantity <= 0:
            return JsonResponse({'error': 'La cantidad debe ser mayor a 0'}, status=400)

        # Validar que los productos por unidad no tengan decimales
        if not is_bulk and quantity % 1 != 0:
            return JsonResponse({'error': 'Solo se permiten cantidades enteras para productos por unidad.'}, status=400)


        product = Product.objects.get(id=product_id)
        cart = request.session.get('cart', [])

        # Verificar stock y actualizar
        for item in cart:
            if item['product_id'] == product_id:
                if is_bulk and quantity > product.bulk_stock:
                    return JsonResponse({
                        'error': f'Stock insuficiente. Stock disponible: {product.bulk_stock} kg'
                    }, status=400)
                elif not is_bulk and quantity > product.stock:
                    return JsonResponse({
                        'error': f'Stock insuficiente. Stock disponible: {product.stock}'
                    }, status=400)

                item['quantity'] = float(quantity)
                item['subtotal'] = float(quantity * decimal.Decimal(str(item['price'])))
                break

        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'cart': cart,
            'total': sum(float(item['subtotal']) for item in cart)
        })

    except Product.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    except decimal.InvalidOperation:
        return JsonResponse({'error': 'Cantidad inválida'}, status=400)
    except Exception as e:
        print(f"Error en update_cart: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


def remove_from_cart(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    cart = request.session.get('cart', [])
    cart = [item for item in cart if item['product_id'] != product_id]
    request.session['cart'] = cart
    
    return JsonResponse({
        'success': True,
        'cart': cart,
        'total': sum(item['price'] * item['quantity'] for item in cart)
    })

@require_http_methods(["POST"])
def init_cart(request):
    try:
        data = json.loads(request.body)
        cart = data.get('cart', [])
        request.session['cart'] = cart
        return JsonResponse({'success': True, 'cart': cart})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)