// Variables globales
let currentProduct = null;
let searchTimeout;
let isLoading = true;

// Inicialización del DOM
document.addEventListener('DOMContentLoaded', function() {
    initializeLoading();
    initializeCategoriesMenu();
    initializeSearch();
    initializeFavoriteButtons();
    initializeModalClose();
});

// función de inicialización de loading
function initializeLoading() {
    const skeletonLoader = document.getElementById('skeletonLoader');
    const productsGrid = document.getElementById('productsGrid');
    
    // Simular carga de contenido
    window.setTimeout(() => {
        skeletonLoader.classList.add('hidden');
        productsGrid.classList.remove('hidden');
        isLoading = false;
    }, 1000);
}

// Función auxiliar para el manejo de favoritos
function toggleFavorite(productId, button) {
    const isFavorite = button.dataset.isFavorite === 'true';
    if (!isFavorite) {
        addToFavorites(productId, button);
    } else {
        removeFromFavorites(productId, button);
    }
}

// Gestión del menú de categorías móvil
function initializeCategoriesMenu() {
    const categoriesMenu = document.getElementById('categoriesMenu');
    const menuContent = categoriesMenu?.querySelector('.fixed');
    const openBtn = document.getElementById('openCategoriesBtn');
    const closeBtn = document.getElementById('closeCategoriesBtn');

    function openMenu() {
        if (!categoriesMenu) return;
        categoriesMenu.classList.remove('hidden');
        setTimeout(() => {
            menuContent?.classList.remove('translate-x-full');
        }, 10);
    }

    function closeMenu() {
        if (!menuContent) return;
        menuContent.classList.add('translate-x-full');
        setTimeout(() => {
            categoriesMenu?.classList.add('hidden');
        }, 300);
    }

    openBtn?.addEventListener('click', openMenu);
    closeBtn?.addEventListener('click', closeMenu);
    categoriesMenu?.addEventListener('click', function(e) {
        if (e.target === this) closeMenu();
    });
}

// Gestión de búsqueda
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchInputMobile = document.getElementById('searchInputMobile');
    const productCards = document.querySelectorAll('.product-card');

    function handleSearch(searchTerm) {
        if (isLoading) return;
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchTerm = searchTerm.toLowerCase().trim();
            
            // Mostrar skeleton durante la búsqueda
            const skeletonLoader = document.getElementById('skeletonLoader');
            const productsGrid = document.getElementById('productsGrid');
            
            skeletonLoader.classList.remove('hidden');
            productsGrid.classList.add('hidden');
            
            setTimeout(() => {
                productCards.forEach(card => {
                    const name = card.querySelector('h3').textContent.toLowerCase();
                    const description = card.querySelector('.product-description')?.textContent.toLowerCase() || '';
                    const sku = card.querySelector('.product-sku')?.textContent.toLowerCase() || '';
                    
                    if (name.includes(searchTerm) || description.includes(searchTerm) || sku.includes(searchTerm)) {
                        card.style.display = '';
                        card.style.opacity = '1';
                    } else {
                        card.style.display = 'none';
                    }
                });
                
                skeletonLoader.classList.add('hidden');
                productsGrid.classList.remove('hidden');
            }, 500);
        }, 300);
    }

    [searchInput, searchInputMobile].forEach(input => {
        if (!input) return;
        
        input.addEventListener('input', function(e) {
            const searchTerm = e.target.value;
            if (searchInput && searchInput !== e.target) 
                searchInput.value = searchTerm;
            if (searchInputMobile && searchInputMobile !== e.target) 
                searchInputMobile.value = searchTerm;
            handleSearch(searchTerm);
        });
    });
}

// Gestión del modal de productos
window.showProductDetails = async function(productId) {
    try {
        const response = await fetch(`/catalog/product/${productId}/`);
        if (!response.ok) {
            console.error('Error de servidor:', response.status);
            return;
        }
        
        const product = await response.json();
        currentProduct = product;
        
        const modal = document.getElementById('productModal');
        if (!modal) {
            console.error('Modal no encontrado');
            return;
        }

        updateModalContent(product);
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    } catch (error) {
        console.error('Error:', error);
    }
}

function updateModalContent(product) {
    if (!product) return;

    document.getElementById('productName').textContent = product.name || '';
    document.getElementById('productCategory').textContent = product.category || '';

    // Imagen principal
    const mainImage = document.getElementById('mainImage');
    if (mainImage) {
        if (product.images && product.images.length > 0 && product.images[0].url) {
            mainImage.innerHTML = `
                <img src="${product.images[0].url}" 
                     alt="${product.name}" 
                     class="w-full h-full object-cover">`;
        } else {
            mainImage.innerHTML = `
                <div class="w-full h-full flex items-center justify-center bg-gray-200">
                    <i class="fas fa-image text-gray-400 text-4xl"></i>
                </div>`;
        }
    }

    // Precios
    const pricingDiv = document.getElementById('productPricing');
    if (pricingDiv) {
        if (product.is_bulk) {
            pricingDiv.innerHTML = `
                <p class="text-3xl font-bold">$${product.price_bulk.toLocaleString()} / kg</p>`;
        } else {
            pricingDiv.innerHTML = `
                <p class="text-3xl font-bold">$${product.price_unit.toLocaleString()}</p>
                ${product.has_bulk_option ? 
                    `<p class="text-sm text-gray-600 mt-1">
                        Precio a granel: $${product.price_bulk.toLocaleString()} / kg
                    </p>` : ''}`;
        }
    }

    // Stock
    const stockDiv = document.getElementById('productStock');
    if (stockDiv) {
        if (product.stock > 0) {
            stockDiv.innerHTML = `
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    En stock: ${product.stock} ${product.unit_type}${product.stock !== 1 ? 's' : ''}
                </span>`;
        } else {
            stockDiv.innerHTML = `
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    Sin stock
                </span>`;
        }
    }

    // Descripción
    const descriptionDiv = document.getElementById('productDescription');
    if (descriptionDiv) {
        if (product.description) {
            descriptionDiv.innerHTML = `<p>${product.description}</p>`;
            descriptionDiv.classList.remove('hidden');
        } else {
            descriptionDiv.classList.add('hidden');
        }
    }

    // Botón de favoritos
    const favoriteBtn = document.getElementById('modalFavoriteBtn');
    if (favoriteBtn) {
        const isFavorite = favoriteBtn.dataset.isFavorite === 'true';
        updateFavoriteButton(favoriteBtn, product.id, isFavorite);
        favoriteBtn.onclick = () => toggleFavorite(product.id, favoriteBtn);
    }
}

window.closeProductModal = function() {
    const modal = document.getElementById('productModal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
        currentProduct = null;
    }
}

// Gestión de favoritos
function initializeFavoriteButtons() {
    const favoriteButtons = document.querySelectorAll('.favorite-button');
    
    favoriteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            toggleFavorite(productId, this);
        });
    });
}

async function addToFavorites(productId, button) {
    try {
        const response = await fetch('/catalog/favorites/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ product_id: productId })
        });
        
        if (response.ok) {
            updateFavoriteButton(button, productId, true);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function removeFromFavorites(productId, button) {
    try {
        const response = await fetch(`/catalog/favorites/remove/${productId}/`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            updateFavoriteButton(button, productId, false);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function updateFavoriteButton(button, productId, isFavorite) {
    if (!button) return;
    
    const icon = button.querySelector('i');
    if (!icon) return;

    icon.classList.remove(isFavorite ? 'far' : 'fas');
    icon.classList.add(isFavorite ? 'fas' : 'far');
    button.dataset.isFavorite = isFavorite.toString();
}

// Compartir en redes sociales
window.shareProduct = function(platform, productId) {
    const id = productId || (currentProduct ? currentProduct.id : null);
    if (!id) return;
    
    const url = encodeURIComponent(`${window.location.origin}/catalog/product/${id}`);
    let shareUrl;
    
    switch(platform) {
        case 'whatsapp':
            shareUrl = `https://api.whatsapp.com/send?text=${url}`;
            break;
        case 'facebook':
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
            break;
        case 'telegram':
            shareUrl = `https://telegram.me/share/url?url=${url}`;
            break;
    }
    
    window.open(shareUrl, '_blank');
}

// Inicialización de eventos del modal
function initializeModalClose() {
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            window.closeProductModal();
        }
    });
}

// Utilidades
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}