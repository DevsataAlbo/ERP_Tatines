document.addEventListener('DOMContentLoaded', function() {
    


    // Control de vencimiento (código existente)
    const requiresExpirationCheckbox = document.getElementById('id_requires_expiration');
    const expirationFields = document.getElementById('expiration-fields');

    function toggleExpirationFields() {
        expirationFields.style.display = requiresExpirationCheckbox.checked ? 'block' : 'none';
    }

    requiresExpirationCheckbox.addEventListener('change', toggleExpirationFields);
    toggleExpirationFields();

    // Nuevas funcionalidades
    const purchasePriceInput = document.getElementById('id_purchase_price');
    const isPurchaseTaxInput = document.getElementById('id_is_purchase_with_tax');
    const salePriceInput = document.getElementById('id_sale_price');
    const isSaleTaxInput = document.getElementById('id_is_sale_with_tax');
    const hasBulkSalesCheckbox = document.getElementById('id_has_bulk_sales');
    const bulkFields = document.querySelectorAll('.bulk-fields');
    
    function toggleBulkFields() {
        bulkFields.forEach(field => {
            field.classList.toggle('hidden', !hasBulkSalesCheckbox.checked);
        });
    }

    function calculatePrices() {
        const purchasePrice = parseFloat(purchasePriceInput.value) || 0;
        const isPurchaseTax = isPurchaseTaxInput.checked;
        const salePrice = parseFloat(salePriceInput.value) || 0;
        const isSaleTax = isSaleTaxInput.checked;

        let netPurchasePrice = isPurchaseTax ? Math.round(purchasePrice / 1.19) : purchasePrice;
        let netSalePrice = isSaleTax ? Math.round(salePrice / 1.19) : salePrice;

        let profitPercentage = 0;
        if (netPurchasePrice > 0 && netSalePrice > 0) {
            profitPercentage = Math.round(((netSalePrice - netPurchasePrice) / netPurchasePrice) * 100);
        }

        document.getElementById('netPurchasePrice').textContent = netPurchasePrice.toLocaleString();
        document.getElementById('netSalePrice').textContent = netSalePrice.toLocaleString();
        document.getElementById('profitPercentage').textContent = profitPercentage;
    }

    // Event listeners adicionales
    hasBulkSalesCheckbox.addEventListener('change', toggleBulkFields);
    purchasePriceInput.addEventListener('input', calculatePrices);
    isPurchaseTaxInput.addEventListener('change', calculatePrices);
    salePriceInput.addEventListener('input', calculatePrices);
    isSaleTaxInput.addEventListener('change', calculatePrices);

    // Inicialización
    toggleBulkFields();
    calculatePrices();
});