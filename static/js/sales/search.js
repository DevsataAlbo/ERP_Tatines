// search.js
import { addToCart } from './cart.js';

let lastSearchTerm = '';

export function initializeSearch() {
    const searchContainer = document.querySelector('.flex.gap-4');
    
    searchContainer.innerHTML = `
        <div class="flex-1">
            <input type="text" 
                   id="searchInput" 
                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" 
                   placeholder="Buscar productos...">
        </div>
        <button id="clearSearchBtn" 
                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 hidden">
            Limpiar búsqueda
        </button>
    `;

    restoreLastSearch();
}

function restoreLastSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');

    if (sessionStorage.getItem('lastSearchTerm')) {
        searchInput.value = sessionStorage.getItem('lastSearchTerm');
        clearSearchBtn.classList.remove('hidden');
        performSearch(searchInput.value);
    }
}

export function setupSearchEventListeners() {
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    let searchTimeout;

    searchInput.addEventListener('input', function (e) {
        clearTimeout(searchTimeout);
        const term = e.target.value.trim();

        searchTimeout = setTimeout(() => {
            if (term.length >= 2) {
                performSearch(term);
                clearSearchBtn.classList.remove('hidden');
            } else {
                document.getElementById('searchResultsBody').innerHTML = '';
                clearSearchBtn.classList.add('hidden');
            }
        }, 300);
    });

    clearSearchBtn.addEventListener('click', function () {
        searchInput.value = '';
        document.getElementById('searchResultsBody').innerHTML = '';
        this.classList.add('hidden');
        sessionStorage.removeItem('lastSearchTerm');
    });
}

export async function performSearch(term) {
    if (term.length < 2) {
        document.getElementById('searchResultsBody').innerHTML = '';
        return;
    }
    
    try {
        const response = await fetch(`/sales/api/products/search/?term=${encodeURIComponent(term)}`);
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        const products = await response.json();
        displaySearchResults(products);
    } catch (error) {
        console.error('Error en la búsqueda:', error);
    }
}

function displaySearchResults(products) {
    const resultsContainer = document.getElementById('searchResultsBody');
    resultsContainer.innerHTML = '';

    if (products.length === 0) {
        resultsContainer.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-gray-500 py-4">
                    No se encontraron productos
                </td>
            </tr>
        `;
        return;
    }

    products.forEach(product => {
        resultsContainer.innerHTML += `
            <tr>
                <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900">${product.name}</div>
                    ${product.brand ? `<div class="text-sm text-gray-500">${product.brand}</div>` : ''}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                    ${product.is_bulk ? `${product.bulk_stock.toFixed(3)} kg` : `${product.stock} unidades`}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">$${product.sale_price.toLocaleString()}</td>
                <td class="px-6 py-4">
                    <button class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
                            onclick="window.salesModule.addToCart(${product.id}, ${product.is_bulk})">
                        Agregar
                    </button>
                </td>
            </tr>
        `;
    });
}