// movement_history.js
function showDetails(data, type = 'edit') {
    try {
        const modal = document.getElementById('editDetailsModal');
        const content = document.getElementById('editDetailsContent');
        
        // Asegurarse de que data sea un objeto
        let changes;
        try {
            // Si data ya es un objeto, JSON.parse lanzará un error
            changes = typeof data === 'string' ? JSON.parse(data) : data;
        } catch (e) {
            console.error('Error parsing data:', e);
            console.error('Received data:', data);
            return;
        }

        let htmlContent = '<div class="space-y-3">';

        if (type === 'adjustment') {
            // Formato para ajustes de inventario
            if (changes && changes.Stock) {
                htmlContent += `
                    <div class="border-b pb-2">
                        <p class="font-medium">Stock</p>
                        <div class="grid grid-cols-2 gap-2 mt-1">
                            <div>
                                <span class="text-sm text-gray-500">Anterior:</span>
                                <p class="text-red-600">${changes.Stock.old}</p>
                            </div>
                            <div>
                                <span class="text-sm text-gray-500">Nuevo:</span>
                                <p class="text-green-600">${changes.Stock.new}</p>
                            </div>
                        </div>
                    </div>
                `;
            }
        } else {
            // Formato para ediciones
            if (changes && typeof changes === 'object') {
                Object.entries(changes).forEach(([field, values]) => {
                    if (values && values.old !== undefined && values.new !== undefined) {
                        htmlContent += `
                            <div class="border-b pb-2">
                                <p class="font-medium">${field}</p>
                                <div class="grid grid-cols-2 gap-2 mt-1">
                                    <div>
                                        <span class="text-sm text-gray-500">Anterior:</span>
                                        <p class="text-red-600">${values.old}</p>
                                    </div>
                                    <div>
                                        <span class="text-sm text-gray-500">Nuevo:</span>
                                        <p class="text-green-600">${values.new}</p>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                });
            }
        }
        
        htmlContent += '</div>';
        content.innerHTML = htmlContent;
        modal.classList.remove('hidden');
        
    } catch (err) {
        console.error('Error al procesar los datos:', err);
        console.error('Datos recibidos:', data);
    }
}

function closeEditDetailsModal() {
    document.getElementById('editDetailsModal').classList.add('hidden');
}

// Event listener para cerrar modal al hacer clic fuera
document.addEventListener('click', function(e) {
    const modal = document.getElementById('editDetailsModal');
    if (e.target === modal) {
        closeEditDetailsModal();
    }
});