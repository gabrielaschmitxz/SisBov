// SISBOV - JavaScript Principal

// Service Worker para PWA (offline)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('ServiceWorker registrado:', registration.scope);
            })
            .catch(error => {
                console.log('ServiceWorker erro:', error);
            });
    });
}

// Funções utilitárias
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.main-content');
    const firstChild = container.firstChild;
    container.insertBefore(alertDiv, firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function formatNumber(number) {
    if (number === null || number === undefined) return '-';
    return number.toLocaleString('pt-BR');
}

// API Helper
const API = {
    async get(url) {
        const response = await fetch(url);
        if (!response.ok) throw new Error(response.statusText);
        return response.json();
    },
    
    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || response.statusText);
        }
        return response.json();
    },
    
    async put(url, data) {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || response.statusText);
        }
        return response.json();
    },
    
    async delete(url) {
        const response = await fetch(url, {
            method: 'DELETE'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || response.statusText);
        }
        return response.json();
    }
};

// Exportar para uso global
window.API = API;
window.showAlert = showAlert;
window.formatDate = formatDate;
window.formatNumber = formatNumber;

