// ui.js
export const TAX_RATE = 0.19;

// Variable de estado para el proceso de venta
let isSubmitting = false;

export function updateTotals() {
    const cart = window.salesModule.getCart();
    const total = cart.reduce((sum, item) => sum + item.subtotal, 0);
    const subtotal = total / (1 + TAX_RATE);
    const tax = total - subtotal;

    document.getElementById('subtotal').textContent = Math.round(subtotal).toLocaleString();
    document.getElementById('tax').textContent = Math.round(tax).toLocaleString();
    document.getElementById('total').textContent = Math.round(total).toLocaleString();
}

export function completeSale() {
    if (isSubmitting) {
        console.log('Ya hay una venta en proceso');
        return;
    }

    const cart = window.salesModule.getCart();
    if (cart.length === 0) {
        alert('Agregue productos antes de completar la venta.');
        return;
    }

    const paymentMethodSelect = document.querySelector('select[name="payment_method"]');
    const statusSelect = document.querySelector('select[name="status"]');
    const dateInput = document.querySelector('input[name="date"]');
    const providerSelect = document.querySelector('select[name="payment_provider"]');
    const installmentsSelect = document.querySelector('select[name="installments"]');
    const customerSelect = document.querySelector('#customer-select');

    if (!paymentMethodSelect || !paymentMethodSelect.value) {
        alert('Por favor seleccione un método de pago.');
        return;
    }

    if (!statusSelect || !statusSelect.value) {
        alert('Por favor seleccione un estado.');
        return;
    }

    const isCredit = paymentMethodSelect.value === 'CREDIT';
    if (isCredit && (!installmentsSelect || !installmentsSelect.value)) {
        alert('Por favor seleccione el número de cuotas.');
        return;
    }

    const currentDate = new Date().toISOString().slice(0, 19);
    const dateValue = dateInput && dateInput.value ? dateInput.value : currentDate;

    try {
        isSubmitting = true;
        console.log('Iniciando proceso de venta');

        const saleData = {
            cart: cart,
            payment_method: paymentMethodSelect.value,
            payment_provider: ['DEBIT', 'CREDIT'].includes(paymentMethodSelect.value) ? 
                providerSelect.value : null,
            installments: isCredit ? parseInt(installmentsSelect.value) : null,
            status: statusSelect.value,
            date: dateValue,
            customer: customerSelect ? customerSelect.value : null
        };

        console.log('Datos de venta a enviar:', saleData);

        fetch('/sales/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(saleData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error al procesar la solicitud.');
                }).catch(() => {
                    throw new Error('Error inesperado del servidor.');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.redirect_url) {
                window.salesModule.setCart([]);
                window.location.href = data.redirect_url;
            } else {
                throw new Error('No se pudo completar la venta.');
            }
        })
        .catch(error => {
            console.error('Error al completar la venta:', error);
            alert('Error al completar la venta: ' + error.message);
        })
        .finally(() => {
            console.log('Finalizando proceso de venta');
            isSubmitting = false;
        });

    } catch (error) {
        console.error('Error en el proceso de venta:', error);
        alert('Error inesperado al procesar la venta.');
        isSubmitting = false;
    }
}

export function resetSubmitState() {
    completeSale.isSubmitting = false;
}