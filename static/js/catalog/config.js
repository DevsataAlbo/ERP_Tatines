document.addEventListener('DOMContentLoaded', function() {
    // Por ahora este archivo está vacío pero aquí irá
    // la lógica para el color picker y preview de configuraciones

    function copyToClipboard(element) {
        element.select();
        document.execCommand('copy');
        alert('URL copiada al portapapeles');
    }
});

function copyUrl() {
    const urlInput = document.getElementById('catalogUrl');
    urlInput.select();
    document.execCommand('copy');
    
    // Feedback visual
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '¡Copiado!';
    
    setTimeout(() => {
        button.textContent = originalText;
    }, 2000);
}