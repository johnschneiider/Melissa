/**
 * Script para cargar negocios vistos recientemente desde localStorage
 * Solo se ejecuta para usuarios no autenticados
 */

document.addEventListener('DOMContentLoaded', function() {
    // Solo ejecutar si el usuario no está autenticado
    if (typeof window.actividadUsuario === 'undefined') {
        return;
    }
    
    // Obtener negocios vistos recientemente desde localStorage
    const visitasRecientes = window.actividadUsuario.obtenerVisitasRecientes();
    
    if (visitasRecientes.length === 0) {
        return; // No hay visitas recientes
    }
    
    // Crear la sección de "Visto recientemente" dinámicamente
    const container = document.querySelector('.container');
    if (!container) return;
    
    // Buscar donde insertar la sección (después del hero, antes de las otras secciones)
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;
    
    // Crear la sección de visto recientemente
    const seccionRecientes = document.createElement('section');
    seccionRecientes.className = 'inicio-cliente-section py-5';
    seccionRecientes.innerHTML = `
        <div class="container">
            <div class="row mb-4 carrusel-cnt">
                <div class="col-12">
                    <h3 class="fw-bold mb-3"><i class="bi bi-clock-history me-2"></i>Visto recientemente</h3>
                    <div class="d-flex gap-4 overflow-auto flex-nowrap" id="recientes-container">
                        <!-- Los negocios se cargarán aquí dinámicamente -->
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Insertar después del hero
    heroSection.parentNode.insertBefore(seccionRecientes, heroSection.nextSibling);
    
    // Cargar los datos de los negocios desde el servidor
    const negociosIds = visitasRecientes.map(v => v.objeto_id).filter(id => id);
    
    if (negociosIds.length === 0) return;
    
    // Hacer petición al servidor para obtener los datos completos de los negocios
    fetch('/clientes/api/negocios-vistos-recientes/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        const recientesContainer = document.getElementById('recientes-container');
        if (!recientesContainer) return;
        
        // Filtrar solo los negocios que están en localStorage
        const negociosFiltrados = data.negocios.filter(negocio => 
            negociosIds.includes(negocio.id)
        );
        
        if (negociosFiltrados.length === 0) {
            // Si no hay datos del servidor, crear cards básicas desde localStorage
            visitasRecientes.slice(0, 5).forEach(visita => {
                const card = crearCardBasica(visita);
                recientesContainer.appendChild(card);
            });
        } else {
            // Usar los datos del servidor
            negociosFiltrados.slice(0, 5).forEach(negocio => {
                const card = crearCardCompleta(negocio);
                recientesContainer.appendChild(card);
            });
        }
    })
    .catch(error => {
        console.error('Error cargando negocios recientes:', error);
        // Fallback: crear cards básicas desde localStorage
        const recientesContainer = document.getElementById('recientes-container');
        if (recientesContainer) {
            visitasRecientes.slice(0, 5).forEach(visita => {
                const card = crearCardBasica(visita);
                recientesContainer.appendChild(card);
            });
        }
    });
});

/**
 * Crear una card básica con datos de localStorage
 */
function crearCardBasica(visita) {
    const card = document.createElement('a');
    card.href = `/clientes/peluquero/${visita.objeto_id}/`;
    card.className = 'text-decoration-none';
    card.style.color = 'inherit';
    
    card.innerHTML = `
        <div class="card negocio-card flex-shrink-0" style="min-width:320px;max-width:320px;">
            <div class="d-flex align-items-center justify-content-center bg-light" style="height:160px;border-top-left-radius:1.2rem;border-top-right-radius:1.2rem;">
                <i class="bi bi-shop fs-1 text-muted"></i>
            </div>
            <div class="negocio-nombre">${visita.descripcion.replace('Visitó el negocio ', '')}</div>
            <div class="negocio-rating">-- <i class="bi bi-star-fill" style="font-size:1em;"></i> <span style="font-weight:400; color:#888;">(--)</span></div>
            <div class="negocio-direccion">Información no disponible</div>
            <span class="negocio-badge">Salón de belleza</span>
        </div>
    `;
    
    return card;
}

/**
 * Crear una card completa con datos del servidor
 */
function crearCardCompleta(negocio) {
    const card = document.createElement('a');
    card.href = negocio.url;
    card.className = 'text-decoration-none';
    card.style.color = 'inherit';
    
    const portada = negocio.portada_url ? 
        `<img src="${negocio.portada_url}" alt="${negocio.nombre}" class="object-fit-cover w-100" style="height:160px;border-top-left-radius:1.2rem;border-top-right-radius:1.2rem;">` :
        `<div class="d-flex align-items-center justify-content-center bg-light" style="height:160px;border-top-left-radius:1.2rem;border-top-right-radius:1.2rem;">
            <i class="bi bi-shop fs-1 text-muted"></i>
        </div>`;
    
    card.innerHTML = `
        <div class="card negocio-card flex-shrink-0" style="min-width:320px;max-width:320px;">
            ${portada}
            <div class="negocio-nombre">${negocio.nombre}</div>
            <div class="negocio-rating">${negocio.rating.toFixed(1)} <i class="bi bi-star-fill" style="font-size:1em;"></i> <span style="font-weight:400; color:#888;">(${negocio.total_resenias})</span></div>
            <div class="negocio-direccion">${negocio.direccion}</div>
            <span class="negocio-badge">${negocio.categoria}</span>
        </div>
    `;
    
    return card;
} 