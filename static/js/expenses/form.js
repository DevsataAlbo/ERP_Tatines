document.addEventListener('DOMContentLoaded', function() {
    // Elementos del formulario
    const isRecurringCheckbox = document.querySelector('#id_is_recurring');
    const recurrenceFields = document.querySelector('#recurrenceFields');
    const amountInput = document.querySelector('#id_amount');
    const ivaCheckbox = document.querySelector('#id_is_tax_included');
    const ivaPreview = document.querySelector('#ivaPreview');
    
    // Campos de recurrencia
    const recurrenceInputs = [
        'recurrence_type',
        'recurrence_start',
        'recurrence_end',
        'reference_amount',
        'status'
    ].map(id => document.querySelector(`#id_${id}`));

    // Función para manejar campos recurrentes
    function handleRecurrenceFields(show) {
        recurrenceFields.classList.toggle('hidden', !show);
        recurrenceInputs.forEach(input => {
            if (input) {
                input.disabled = !show;
                // Limpiar valores si se oculta
                if (!show) input.value = '';
            }
        });
    }

    // Configuración Flatpickr
    const dateConfig = {
        locale: 'es',
        dateFormat: 'Y-m-d',
        altInput: true,
        altFormat: 'd/m/Y',
        allowInput: true,
        disableMobile: true
    };

    // Inicializar datepickers
    flatpickr('#id_date', {
        ...dateConfig,
        minDate: null  // Permitir fechas pasadas para el gasto
    });

    flatpickr('#id_recurrence_start', {
        ...dateConfig,
        minDate: 'today',
        onChange: function(selectedDates) {
            if (selectedDates[0]) {
                const endDatePicker = document.querySelector('#id_recurrence_end')._flatpickr;
                endDatePicker.set('minDate', selectedDates[0]);
            }
        }
    });

    flatpickr('#id_recurrence_end', {
        ...dateConfig,
        minDate: document.querySelector('#id_recurrence_start').value || 'today'
    });

    // Función para calcular y mostrar IVA
    function updateIvaPreview() {
        const amount = parseFloat(amountInput.value) || 0;
        if (amount > 0 && ivaCheckbox.checked) {
            const neto = Math.round(amount / 1.19);
            const iva = amount - neto;
            ivaPreview.textContent = `Neto: $${neto.toLocaleString()} | IVA: $${iva.toLocaleString()}`;
        } else {
            ivaPreview.textContent = '';
        }
    }

    // Event listeners
    isRecurringCheckbox.addEventListener('change', (e) => handleRecurrenceFields(e.target.checked));
    amountInput.addEventListener('input', updateIvaPreview);
    ivaCheckbox.addEventListener('change', updateIvaPreview);

    // Inicialización
    handleRecurrenceFields(isRecurringCheckbox.checked);
    updateIvaPreview();
});