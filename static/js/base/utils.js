// Funciones de utilidad reutilizables

// Obtener CSRF token
function getCSRFToken() {
    const input = document.getElementById('csrf_token_js');
    if (input) return input.value;
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!token) {
        throw new Error('CSRF token no encontrado');
    }
    return token.value;
}

// Mostrar alertas
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insertar al inicio del contenedor principal
    const container = document.querySelector('.container') || document.querySelector('main');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-hide después de 5 segundos
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
}

// Validar respuesta de fetch
async function validateResponse(response) {
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Manejar errores de API
function handleApiError(error, customMessage = null) {
    console.error('API Error:', error);
    const message = customMessage || error.message || 'Ocurrió un error inesperado';
    showAlert(message, 'error');
}

// Loading states para botones
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Procesando...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || 'Enviar';
    }
}

// Formatear fecha
function formatDate(date) {
    return new Date(date).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Formatear hora
function formatTime(time) {
    return new Date(`2000-01-01T${time}`).toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Exportar funciones para uso global
window.utils = {
    getCSRFToken,
    showAlert,
    validateResponse,
    handleApiError,
    setButtonLoading,
    formatDate,
    formatTime,
    debounce,
    throttle
}; 