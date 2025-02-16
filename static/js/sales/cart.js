

import { calculateCommission } from './commission.js';
import { updateTotals } from './ui.js';

let cart = [];

export function getCart() {
    return cart;
}

export function setCart(newCart) {
    cart = newCart;
}

export function addToCart(productId, isBulk) {
    if (isBulk) {
        showAmountModal(productId);
        return;
    }

    const quantityInput = document.getElementById(`quantity-${productId}`);
    const quantity = quantityInput ? parseFloat(quantityInput.value) : 1;

    if (!quantity || quantity <= 0) {
        alert('Por favor ingrese una cantidad válida.');
        return;
    }

    submitCartAddition(productId, quantity, isBulk);
}

export function showAmountModal(productId) {
    const modal = document.getElementById('amountModal');
    const productRow = document.querySelector(`button[onclick*="${productId}"]`).closest('tr');
    const productName = productRow.querySelector('td:first-child').textContent.trim();
    
    document.getElementById('modalProductName').textContent = productName;
    modal.classList.remove('hidden');

    document.getElementById('confirmAmount').onclick = () => {
        const amount = parseFloat(document.getElementById('amountInput').value);
        if (!amount || amount <= 0) {
            alert('Por favor ingrese un monto válido');
            return;
        }
        submitCartAddition(productId, amount, true, true);
        modal.classList.add('hidden');
        document.getElementById('amountInput').value = '';
    };

    document.getElementById('cancelAmount').onclick = () => {
        modal.classList.add('hidden');
        document.getElementById('amountInput').value = '';
    };
}

export function updateCartDisplay() {
    const cartContainer = document.querySelector('.overflow-x-auto');
    if (!cartContainer) return;
 
    if (cart.length === 0) {
        cartContainer.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                No hay productos en el carrito
            </div>
        `;
        updateTotals();
        return;
    }

    cartContainer.innerHTML = generateCartHTML();

    // Actualizar totales y recalcular comisión
    updateTotals();
    window.salesModule.recalculateCommission();
}

export function recalculateCommissionIfNeeded() {
    const providerSelect = document.querySelector('select[name="payment_provider"]');
    const paymentMethodSelect = document.querySelector('select[name="payment_method"]');
    
    if (providerSelect.value && ['DEBIT', 'CREDIT'].includes(paymentMethodSelect.value)) {
        const selectedOption = providerSelect.options[providerSelect.selectedIndex];
        const isCredit = paymentMethodSelect.value === 'CREDIT';
        const rate = isCredit ? 
            selectedOption.dataset.creditRate : 
            selectedOption.dataset.debitRate;
            
        calculateCommission(rate);
    }
}

function generateCartHTML() {
    let html = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cantidad</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subtotal</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
    `;

    cart.forEach((item, index) => {
        html += generateCartItemHTML(item, index);
    });

    html += '</tbody></table>';
    return html;
}

function generateCartItemHTML(item, index) {
    const quantityStep = item.is_bulk ? '0.001' : '1';
    return `
        <tr>
            <td class="px-6 py-4 text-sm text-gray-900">${item.name}</td>
            <td class="px-6 py-4">
                <input type="number" 
                       value="${item.quantity}" 
                       min="${item.is_bulk ? '0.001' : '1'}" 
                       step="${quantityStep}"
                       class="w-20 px-2 py-1 border rounded"
                       onchange="window.cartModule.updateQuantity(${index}, this.value)">
                ${item.is_bulk ? 'kg' : ''}
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">$ ${item.price.toLocaleString()}</td>
            <td class="px-6 py-4 text-sm text-gray-500">$ ${item.subtotal.toLocaleString()}</td>
            <td class="px-6 py-4">
                <button onclick="window.cartModule.removeFromCart(${index})"
                        class="text-red-600 hover:text-red-900">
                    Eliminar
                </button>
            </td>
        </tr>
    `;
}

export function updateQuantity(index, newQuantity) {
    newQuantity = parseFloat(newQuantity);

    if (newQuantity <= 0) {
        return removeFromCart(index);
    }

    const item = cart[index];

    if (!item.is_bulk && !Number.isInteger(newQuantity)) {
        alert('Solo se permiten cantidades enteras para productos por unidad.');
        return;
    }

    fetch('/sales/api/cart/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            product_id: item.product_id,
            quantity: newQuantity,
            is_bulk: item.is_bulk
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            alert(result.error);
            return;
        }
        cart = result.cart;
        updateCartDisplay();
        updateTotals();
    })
    .catch(error => {
        console.error('Error al actualizar la cantidad:', error);
        alert('Error al actualizar la cantidad.');
    });
}

export function removeFromCart(index) {
    const item = cart[index];

    fetch(`/sales/api/cart/remove/${item.product_id}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            alert(result.error);
            return;
        }
        cart = result.cart;
        updateCartDisplay();
        updateTotals();
    })
    .catch(error => {
        console.error('Error al eliminar del carrito:', error);
        alert('Error al eliminar el producto.');
    });
}

export function submitCartAddition(productId, quantity, isBulk, isAmount = false) {
    const payload = {
        product_id: productId,
        is_bulk: isBulk
    };

    if (isAmount) {
        payload.amount = quantity;
    } else {
        payload.quantity = quantity;
    }

    fetch('/sales/api/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            alert(result.error);
            return;
        }
        cart = result.cart;
        updateCartDisplay();
        updateTotals();
    })
    .catch(error => {
        console.error('Error al agregar al carrito:', error);
        alert('Error al agregar al carrito.');
    });
}

// Exponer funciones necesarias para el HTML
window.cartModule = {
    updateQuantity,
    removeFromCart
};
