document.addEventListener('DOMContentLoaded', function() {
    // ========= CONFIGURACIÓN DEL DATEPICKER =========
    const dateInput = document.querySelector('input[name="date"]');
    if (dateInput) {
        const flatpickrInstance = flatpickr(dateInput, {
            locale: 'es',
            dateFormat: 'Y-m-d',
            altInput: true,
            altFormat: 'd/m/Y',
            allowInput: false,
            disableMobile: true,
            defaultDate: new Date(),
            onChange: function(selectedDates, dateStr, instance) {
                if (selectedDates[0]) {
                    const formattedDate = selectedDates[0].toISOString().split('T')[0];
                    instance._input.value = formattedDate;
                }
            }
        });

        const today = new Date();
        const initialDate = today.toISOString().split('T')[0];
        dateInput.value = initialDate;
    }

    // ========= MANEJO DE PRODUCTOS =========
    const form = document.getElementById('stockEntryForm');
    const addProductButton = document.getElementById('addProduct');
    const productList = document.getElementById('productList');

    function addProductRow() {
        const template = document.getElementById('productRowTemplate');
        if (!template) {
            console.error('Template no encontrado');
            return;
        }

        const clone = template.content.cloneNode(true);
        const row = clone.querySelector('.product-row');
        
        if (!row) {
            console.error('Fila de producto no encontrada en el template');
            return;
        }

        const productSelect = row.querySelector('.product-select');
        const expirationField = row.querySelector('.expiration-date-field');
        
        if (productSelect) {
            productSelect.addEventListener('change', function() {
                const option = this.options[this.selectedIndex];
                if (option && expirationField) {
                    const requiresExpiration = option.dataset.requiresExpiration === 'true';
                    expirationField.style.display = requiresExpiration ? 'block' : 'none';
                    const dateInput = expirationField.querySelector('input');
                    if (dateInput) {
                        dateInput.required = requiresExpiration;
                    }
                }
            });
        }

        const removeButton = row.querySelector('.remove-product');
        if (removeButton) {
            removeButton.addEventListener('click', function() {
                row.remove();
            });
        }

        productList.appendChild(row);
    }

    if (addProductButton && productList) {
        addProductButton.addEventListener('click', addProductRow);
        addProductRow(); // Agregar primera fila al cargar
    }

    // ========= MANEJO DEL FORMULARIO =========
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            try {
                // Validar la fecha
                const selectedDate = dateInput._flatpickr.selectedDates[0];
                if (!selectedDate) {
                    alert('Debe seleccionar una fecha válida');
                    return;
                }

                // Crear FormData y establecer la fecha
                const formData = new FormData(form);
                const formattedDate = selectedDate.toISOString().split('T')[0];
                formData.set('date', formattedDate);

                // Recolectar datos de productos
                const details = [];
                const productRows = document.querySelectorAll('.product-row');

                if (productRows.length === 0) {
                    alert('Debe agregar al menos un producto');
                    return;
                }

                for (const row of productRows) {
                    const productSelect = row.querySelector('[name="product"]');
                    const quantity = row.querySelector('[name="quantity"]');
                    const purchasePrice = row.querySelector('[name="purchase_price"]');
                    const isPriceWithTax = row.querySelector('[name="is_price_with_tax"]');
                    const batchNumber = row.querySelector('[name="batch_number"]');
                    const expirationDate = row.querySelector('[name="expiration_date"]');

                    // Validaciones
                    if (!productSelect.value) {
                        alert('Debe seleccionar un producto');
                        return;
                    }

                    if (!quantity.value || quantity.value <= 0) {
                        alert('La cantidad debe ser mayor a 0');
                        return;
                    }

                    if (!purchasePrice.value || purchasePrice.value <= 0) {
                        alert('El precio de compra debe ser mayor a 0');
                        return;
                    }

                    const requiresExpiration = productSelect.options[productSelect.selectedIndex].dataset.requiresExpiration === 'true';
                    if (requiresExpiration && !expirationDate.value) {
                        alert('Este producto requiere fecha de vencimiento');
                        return;
                    }

                    details.push({
                        product: productSelect.value,
                        quantity: quantity.value,
                        purchase_price: purchasePrice.value,
                        is_price_with_tax: isPriceWithTax.checked,
                        batch_number: batchNumber.value,
                        expiration_date: expirationDate.value
                    });
                }

                formData.append('details', JSON.stringify(details));

                // Enviar formulario
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                    }
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || 'Error al procesar la solicitud');
                }

                if (data.status === 'success') {
                    window.location.href = data.redirect_url;
                } else {
                    throw new Error(data.message || 'Error desconocido');
                }

            } catch (error) {
                console.error('Error:', error);
                alert(error.message || 'Error al procesar la solicitud');
            }
        });
    }
});