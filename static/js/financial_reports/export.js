document.addEventListener('DOMContentLoaded', function() {
    const reportType = document.getElementById('reportType');
    const reportContent = document.getElementById('reportContent');

    const reportDescriptions = {
        income_statement: [
            "• Resumen de ingresos y gastos",
            "• Análisis de márgenes",
            "• Desglose por categorías",
            "• Comparativa con período anterior"
        ],
        sales_detail: [
            "• Detalle de ventas por día",
            "• Análisis por método de pago",
            "• Top productos vendidos",
            "• Tendencias de ventas"
        ],
        expense_detail: [
            "• Desglose de gastos por categoría",
            "• Análisis temporal",
            "• Comparativa mensual",
            "• Proyecciones de gastos"
        ],
        profitability: [
            "• Análisis de rentabilidad por producto",
            "• Márgenes de ganancia",
            "• ROI por categoría",
            "• Tendencias de rentabilidad"
        ]
    };

    function updatePreview() {
        const selectedReport = reportType.value;
        const description = reportDescriptions[selectedReport];
        
        reportContent.innerHTML = description
            .map(item => `<div class="mb-1">${item}</div>`)
            .join('');
    }

    reportType.addEventListener('change', updatePreview);
    updatePreview(); // Inicializar
});