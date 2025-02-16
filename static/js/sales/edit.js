import { initializeCustomerSelect } from '../customers/selector.js';
import { recalculateCommission } from './commission.js';
import { updateTotals } from './ui.js';

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchProduct');
    const searchResults = document.getElementById('searchResults');
    const searchResultsBody = document.getElementById('searchResultsBody');
    const cartItems = document.getElementById('cartItems');
    const updateSaleButton = document.getElementById('updateSale');
    const saleForm = document.getElementById('saleForm');
    let cart = [];

    // Inicializar selector de clientes
    const customerSelect = document.querySelector('#customer-select');
    if (customerSelect) {
        initializeCustomerSelect(customerSelect);
    }

    // Función para obtener el token CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Inicializar el carrito con los productos existentes
    try {
        const initialCart = JSON.parse(document.getElementById('initial-cart-data').textContent);
        cart = initialCart;
        
        // Inicializar el carrito en la sesión
        fetch('/sales/api/cart/init/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ cart: initialCart })
        }).then(() => {
            updateCartDisplay(cart);
        }).catch(error => {
            console.error('Error al inicializar el carrito:', error);
        });
    } catch (error) {
        console.error('Error al cargar el carrito inicial:', error);
    }

    // Búsqueda de productos
    searchInput.addEventListener('input', debounce(async function(e) {
        const searchTerm = e.target.value.trim();

        if (searchTerm.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        try {
            const response = await fetch(`/sales/api/products/search/?term=${encodeURIComponent(searchTerm)}`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            displaySearchResults(data);
            searchResults.classList.remove('hidden');
        } catch (error) {
            console.error('Error:', error);
        }
    }, 300));

    function displaySearchResults(products) {
        searchResultsBody.innerHTML = '';
        
        if (products.length === 0) {
            searchResultsBody.innerHTML = `
                <tr>
                    <td colspan="4" class="px-6 py-4 text-center text-gray-500">
                        No se encontraron productos
                    </td>
                </tr>
            `;
            return;
        }

        products.forEach(product => {
            searchResultsBody.innerHTML += `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-medium text-gray-900">${product.name}</div>
                        <div class="text-sm text-gray-500">${product.brand || ''}</div>
                        ${product.is_bulk ? '<span class="text-xs text-blue-600">(Venta a granel)</span>' : ''}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${product.is_bulk ? 
                            `${product.bulk_stock.toFixed(2)} kg` : 
                            `${product.stock} un`}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        $ ${product.sale_price.toLocaleString()}${product.is_bulk ? '/kg' : ''}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button onclick='window.editModule.addToCart(${JSON.stringify(product)})' 
                                class="text-blue-600 hover:text-blue-900">
                            Agregar
                        </button>
                    </td>
                </tr>
            `;
        });
    }

    // Función para agregar al carrito
    async function addToCart(product) {
        try {
            let quantity = 1;
            if (product.is_bulk) {
                const amount = prompt(`Ingrese el monto a vender de ${product.name} (precio por kilo: $${product.sale_price})`);
                if (!amount) return;

                const amountValue = parseFloat(amount);
                if (isNaN(amountValue) || amountValue <= 0) {
                    alert('Por favor ingrese un monto válido');
                    return;
                }

                quantity = amountValue / product.sale_price;
                if (quantity > product.bulk_stock) {
                    alert(`Stock insuficiente. Stock disponible: ${product.bulk_stock.toFixed(2)} kg`);
                    return;
                }
            }

            const response = await fetch('/sales/api/cart/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    product_id: product.id,
                    quantity: quantity,
                    is_bulk: product.is_bulk
                })
            });

            const data = await response.json();
            if (data.success) {
                cart = data.cart;
                updateCartDisplay(data.cart);
            } else {
                alert(data.error || 'Error al agregar al carrito');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al agregar al carrito');
        }
    }

    // Función para actualizar cantidad
    async function updateQuantity(productId, newValue, isBulk) {
        try {
            if (isBulk) {
                const editType = confirm('¿Desea editar por monto? (Aceptar para monto, Cancelar para peso)');
                if (editType) {
                    const price = cart.find(item => item.product_id === productId).price;
                    const amount = parseFloat(prompt('Ingrese el monto de la venta:'));
                    if (isNaN(amount) || amount <= 0) {
                        alert('Por favor ingrese un monto válido');
                        return;
                    }
                    newValue = amount / price;
                }
            }

            const response = await fetch('/sales/api/cart/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: parseFloat(newValue),
                    is_bulk: isBulk
                })
            });

            const data = await response.json();
            if (data.success) {
                cart = data.cart;
                updateCartDisplay(data.cart);
            } else {
                alert(data.error || 'Error al actualizar cantidad');
                updateCartDisplay(cart);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al actualizar cantidad');
            updateCartDisplay(cart);
        }
    }

    // Función para remover del carrito
    async function removeFromCart(productId) {
        try {
            const response = await fetch(`/sales/api/cart/remove/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            const data = await response.json();
            if (data.success) {
                cart = data.cart;
                updateCartDisplay(data.cart);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al eliminar del carrito');
        }
    }

    // Función para actualizar la visualización del carrito
    function updateCartDisplay(cart) {
        if (!cartItems) return;
        
        cartItems.innerHTML = '';
        let totalVenta = 0;

        cart.forEach(item => {
            const subtotal = item.price * item.quantity;
            totalVenta += subtotal;

            cartItems.innerHTML += `
                <tr>
                    <td class="px-6 py-4">
                        ${item.name}
                        ${item.is_bulk ? '<span class="text-xs text-blue-600">(Granel)</span>' : ''}
                    </td>
                    <td class="px-6 py-4">
                        <input type="number" 
                               value="${item.is_bulk ? parseFloat(item.quantity).toFixed(3) : item.quantity}"
                               min="${item.is_bulk ? '0.001' : '1'}"
                               step="${item.is_bulk ? '0.001' : '1'}"
                               class="w-20 rounded border-gray-300"
                               onchange="window.editModule.updateQuantity(${item.product_id}, this.value, ${item.is_bulk})">
                        ${item.is_bulk ? 'kg' : 'un'}
                    </td>
                    <td class="px-6 py-4">$ ${item.price.toLocaleString()}</td>
                    <td class="px-6 py-4">$ ${subtotal.toLocaleString()}</td>
                    <td class="px-6 py-4">
                        <button onclick="window.editModule.removeFromCart(${item.product_id})"
                                class="text-red-600 hover:text-red-900">
                            Eliminar
                        </button>
                    </td>
                </tr>
            `;
        });

        // Actualizar totales
        const total = totalVenta;
        const iva = Math.round(total * 19/119);
        const subtotal = total - iva;

        document.getElementById('subtotal').textContent = subtotal.toLocaleString();
        document.getElementById('tax').textContent = iva.toLocaleString();
        document.getElementById('total').textContent = total.toLocaleString();

        if (updateSaleButton) {
            updateSaleButton.disabled = cart.length === 0;
        }

        // Recalcular comisión si es necesario
        recalculateCommission();
    }

    // Manejar el envío del formulario de venta
    if (saleForm) {
        saleForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(saleForm);
            const paymentMethod = formData.get('payment_method');
            const status = formData.get('status');
            const customerId = customerSelect ? customerSelect.value : null;

            if (!paymentMethod) {
                alert('Seleccione un método de pago');
                return;
            }

            try {
                updateSaleButton.disabled = true;
                updateSaleButton.textContent = 'Procesando...';
                
                const cartData = cart.map(item => ({
                    ...item,
                    quantity: parseFloat(item.quantity),
                    price: parseFloat(item.price)
                }));

                const response = await fetch(saleForm.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        payment_method: paymentMethod,
                        status: status,
                        customer: customerId,
                        cart: cartData
                    })
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Error al procesar la venta');
                }

                if (data.success && data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    throw new Error('Error al procesar la venta: respuesta inválida del servidor');
                }

            } catch (error) {
                console.error('Error:', error);
                alert(error.message || 'Error al procesar la venta');
            } finally {
                updateSaleButton.disabled = false;
                updateSaleButton.textContent = 'Guardar Cambios';
            }
        });
    }

    // Función debounce para la búsqueda
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Inicializar estado inicial
    updateTotals();
    recalculateCommission();

    // Exponer funciones necesarias para el HTML
    window.editModule = {
        addToCart,
        updateQuantity,
        removeFromCart
    };
});