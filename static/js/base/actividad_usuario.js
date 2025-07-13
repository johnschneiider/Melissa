/**
 * Sistema de tracking de actividades para usuarios no autenticados
 * Utiliza localStorage para almacenar visitas recientes
 */

class ActividadUsuario {
    constructor() {
        this.storageKey = 'melissa_actividades';
        this.maxActividades = 20; // Máximo de actividades a almacenar
        this.actividades = this.cargarActividades();
    }

    /**
     * Carga las actividades desde localStorage
     */
    cargarActividades() {
        try {
            const actividades = localStorage.getItem(this.storageKey);
            return actividades ? JSON.parse(actividades) : [];
        } catch (error) {
            console.error('Error cargando actividades:', error);
            return [];
        }
    }

    /**
     * Guarda las actividades en localStorage
     */
    guardarActividades() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.actividades));
        } catch (error) {
            console.error('Error guardando actividades:', error);
        }
    }

    /**
     * Registra una visita a un negocio
     */
    registrarVisitaNegocio(negocioId, negocioNombre) {
        const actividad = {
            tipo: 'visita_negocio',
            objeto_id: negocioId,
            objeto_tipo: 'negocio',
            descripcion: `Visitó el negocio ${negocioNombre}`,
            fecha: new Date().toISOString(),
            datos_adicionales: {
                url: window.location.href,
                user_agent: navigator.userAgent
            }
        };

        this.agregarActividad(actividad);
    }

    /**
     * Registra una búsqueda
     */
    registrarBusqueda(termino, resultados) {
        const actividad = {
            tipo: 'busqueda_realizada',
            descripcion: `Buscó: ${termino}`,
            fecha: new Date().toISOString(),
            datos_adicionales: {
                termino: termino,
                resultados: resultados,
                url: window.location.href
            }
        };

        this.agregarActividad(actividad);
    }

    /**
     * Agrega una actividad y mantiene el límite
     */
    agregarActividad(actividad) {
        // Remover actividades duplicadas del mismo tipo y objeto
        this.actividades = this.actividades.filter(a => 
            !(a.tipo === actividad.tipo && 
              a.objeto_id === actividad.objeto_id && 
              a.objeto_tipo === actividad.objeto_tipo)
        );

        // Agregar la nueva actividad al inicio
        this.actividades.unshift(actividad);

        // Mantener solo las últimas maxActividades
        if (this.actividades.length > this.maxActividades) {
            this.actividades = this.actividades.slice(0, this.maxActividades);
        }

        this.guardarActividades();
    }

    /**
     * Obtiene las visitas recientes a negocios
     */
    obtenerVisitasRecientes() {
        return this.actividades.filter(a => a.tipo === 'visita_negocio');
    }

    /**
     * Obtiene las búsquedas recientes
     */
    obtenerBusquedasRecientes() {
        return this.actividades.filter(a => a.tipo === 'busqueda_realizada');
    }

    /**
     * Limpia todas las actividades
     */
    limpiarActividades() {
        this.actividades = [];
        this.guardarActividades();
    }

    /**
     * Obtiene estadísticas básicas
     */
    obtenerEstadisticas() {
        const visitas = this.obtenerVisitasRecientes();
        const busquedas = this.obtenerBusquedasRecientes();
        
        return {
            total_actividades: this.actividades.length,
            visitas_negocios: visitas.length,
            busquedas: busquedas.length,
            ultima_actividad: this.actividades[0]?.fecha || null
        };
    }
}

// Inicializar el sistema de actividades
const actividadUsuario = new ActividadUsuario();

// Detectar automáticamente visitas a negocios
document.addEventListener('DOMContentLoaded', function() {
    // Detectar si estamos en una página de detalle de negocio
    const negocioId = document.querySelector('[data-negocio-id]')?.dataset.negocioId;
    const negocioNombre = document.querySelector('[data-negocio-nombre]')?.dataset.negocioNombre;
    
    if (negocioId && negocioNombre) {
        actividadUsuario.registrarVisitaNegocio(negocioId, negocioNombre);
    }
});

// Exportar para uso global
window.ActividadUsuario = ActividadUsuario;
window.actividadUsuario = actividadUsuario; 