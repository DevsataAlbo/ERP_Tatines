const TAX_RATE = 0.19;

export function updateCommissionDisplay(commission, tax, rate) {
    const commissionElement = document.getElementById('commission_amount');
    const taxElement = document.getElementById('commission_tax');
    const totalElement = document.getElementById('commission_total');
    const rateElement = document.getElementById('commission_rate');

    if (commissionElement) commissionElement.textContent = `$ ${Math.round(commission).toLocaleString()}`;
    if (taxElement) taxElement.textContent = `$ ${Math.round(tax).toLocaleString()}`;
    if (totalElement) totalElement.textContent = `$ ${Math.round(commission + tax).toLocaleString()}`;
    if (rateElement) rateElement.textContent = `(${rate.toFixed(2)}%)`;
}

export function calculateCommission(rate) {
    const totalElement = document.getElementById('total');
    if (!totalElement) {
        console.warn('Elemento total no encontrado');
        return;
    }

    // Obtener el total sin formato
    const totalText = totalElement.textContent
        .replace(/\./g, '')
        .replace(/,/g, '.')
        .replace(/[^0-9.-]+/g, '');

    const total = parseInt(totalText, 10);
    const rateDecimal = parseFloat(rate);
    
    // Calcular comisión e IVA redondeados a enteros
    const commission = Math.round((total * rateDecimal) / 100);
    const tax = Math.round(commission * TAX_RATE);
    
    console.log('Cálculo comisión:', {
        montoVenta: total,
        tasa: rateDecimal,
        comisionBase: commission,
        iva: tax,
        comisionTotal: commission + tax
    });
    
    updateCommissionDisplay(commission, tax, rateDecimal);
    updateNetProfit(total, commission + tax);
}

function updateNetProfit(total, totalCommission) {
    const netProfitElement = document.getElementById('net_profit');
    if (!netProfitElement) return;

    const grossProfitElement = document.getElementById('gross_profit');
    const grossProfit = parseInt(grossProfitElement.textContent.replace(/[^0-9-]+/g, ''), 10);
    
    const netProfit = grossProfit - totalCommission;
    netProfitElement.textContent = `$ ${netProfit.toLocaleString()}`;
}

export function recalculateCommissionIfNeeded() {
    const paymentMethodSelect = document.querySelector('select[name="payment_method"]');
    const providerSelect = document.querySelector('select[name="payment_provider"]');
    
    if (!paymentMethodSelect || !providerSelect) {
        return;
    }

    if (providerSelect.value && ['DEBIT', 'CREDIT'].includes(paymentMethodSelect.value)) {
        const selectedOption = providerSelect.options[providerSelect.selectedIndex];
        const isCredit = paymentMethodSelect.value === 'CREDIT';
        const rate = isCredit ? 
            selectedOption.dataset.creditRate : 
            selectedOption.dataset.debitRate;
            
        calculateCommission(rate);
    }
}

export function recalculateCommission() {
    const paymentMethodSelect = document.querySelector('select[name="payment_method"]');
    const providerSelect = document.querySelector('select[name="payment_provider"]');
    
    if (!paymentMethodSelect || !providerSelect || !providerSelect.value) {
        return;
    }
 
    if (['DEBIT', 'CREDIT'].includes(paymentMethodSelect.value)) {
        const selectedOption = providerSelect.options[providerSelect.selectedIndex];
        const isCredit = paymentMethodSelect.value === 'CREDIT';
        const rate = isCredit ? 
            selectedOption.dataset.creditRate : 
            selectedOption.dataset.debitRate;
        
        console.log('Recalculando comisión:', {
            totalCarrito: document.getElementById('total').textContent,
            rate: rate
        });
            
        calculateCommission(rate);
    }
 }

 export function setupPaymentHandlers() {
    const paymentMethodSelect = document.querySelector('select[name="payment_method"]');
    const providerSection = document.getElementById('payment_provider_section');
    const installmentsSection = document.getElementById('installments_section');
    const commissionDetails = document.getElementById('commission_details');
    const providerSelect = document.querySelector('select[name="payment_provider"]');

    // Verificar estado inicial y calcular comisión si aplica
    if (paymentMethodSelect.value && ['DEBIT', 'CREDIT'].includes(paymentMethodSelect.value)) {
        providerSection.classList.remove('hidden');
        commissionDetails.classList.remove('hidden');
        if (paymentMethodSelect.value === 'CREDIT') {
            installmentsSection.classList.remove('hidden');
        }
        if (providerSelect.value) {
            triggerCommissionCalculation(providerSelect, paymentMethodSelect.value === 'CREDIT');
        }
    }

    // Event listeners
    paymentMethodSelect.addEventListener('change', function() {
        const isCardPayment = ['DEBIT', 'CREDIT'].includes(this.value);
        const isCreditCard = this.value === 'CREDIT';
        
        providerSection.classList.toggle('hidden', !isCardPayment);
        installmentsSection.classList.toggle('hidden', !isCreditCard);
        commissionDetails.classList.toggle('hidden', !isCardPayment);
        
        if (!isCardPayment) {
            clearCommissionDisplay();
        } else if (providerSelect.value) {
            triggerCommissionCalculation(providerSelect, isCreditCard);
        }
    
        // Reiniciar el estado del botón de completar venta
        if (window.salesModule && window.salesModule.resetSubmitState) {
            window.salesModule.resetSubmitState();
        }
    });

    providerSelect.addEventListener('change', function() {
        if (!this.value) {
            clearCommissionDisplay();
            return;
        }
        triggerCommissionCalculation(this, paymentMethodSelect.value === 'CREDIT');
    });
}

function triggerCommissionCalculation(providerSelect, isCredit) {
    const selectedOption = providerSelect.options[providerSelect.selectedIndex];
    const rate = isCredit ? 
        selectedOption.dataset.creditRate : 
        selectedOption.dataset.debitRate;
    calculateCommission(rate);
}

function clearCommissionDisplay() {
    updateCommissionDisplay(0, 0, 0);
}

export function updateInstallmentsOptions(maxInstallments) {
   const installmentsSelect = document.querySelector('select[name="installments"]');
   installmentsSelect.innerHTML = '<option value="1">Sin cuotas</option>';
   
   for (let i = 2; i <= maxInstallments; i++) {
       installmentsSelect.innerHTML += `<option value="${i}">${i} cuotas</option>`;
   }
}