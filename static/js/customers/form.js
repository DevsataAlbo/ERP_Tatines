document.addEventListener('DOMContentLoaded', function() {
    const customerTypeSelect = document.querySelector('#id_customer_type');
    const personFields = document.querySelector('#person-fields');
    const companyFields = document.querySelector('#company-fields');

    function toggleFields() {
        if (customerTypeSelect.value === 'PERSON') {
            personFields.style.display = 'block';
            companyFields.style.display = 'none';
        } else {
            personFields.style.display = 'none';
            companyFields.style.display = 'block';
        }
    }

    if (customerTypeSelect) {
        customerTypeSelect.addEventListener('change', toggleFields);
        toggleFields(); // Ejecutar al cargar la página
    }
});