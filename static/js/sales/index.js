import { initializeSearch, setupSearchEventListeners } from './search.js';
import { setupPaymentHandlers, recalculateCommission } from './commission.js';  // Cambiar aquí
import { updateTotals, completeSale, resetSubmitState } from './ui.js';
import { updateCartDisplay, addToCart, getCart, setCart } from './cart.js';
import { initializeCustomerSelect } from '../customers/selector.js';

document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    setupSearchEventListeners();
    setupPaymentHandlers();
    updateCartDisplay();
    updateTotals();
    
    // Inicializar selector de clientes
    const customerSelect = document.querySelector('#customer-select');
    if (customerSelect) {
        initializeCustomerSelect(customerSelect);
    }
});

// Exponer funciones globalmente
window.salesModule = {
    addToCart,
    completeSale,
    updateCartDisplay,
    updateTotals,
    getCart,
    setCart,
    recalculateCommission,
    resetSubmitState
};