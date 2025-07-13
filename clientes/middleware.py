from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import get_object_or_404
from .models import ActividadUsuario
from negocios.models import Negocio
import logging

logger = logging.getLogger(__name__)

class ActividadUsuarioMiddleware(MiddlewareMixin):
    """Middleware para registrar automáticamente las actividades de los usuarios"""
    
    def process_request(self, request):
        """Registra visitas a negocios automáticamente"""
        if not request.user.is_authenticated:
            return None
            
        # Solo registrar para usuarios clientes
        if not hasattr(request.user, 'tipo') or request.user.tipo != 'cliente':
            return None
            
        # Registrar visita a detalle de negocio
        if request.path.startswith('/clientes/peluquero/') and request.method == 'GET':
            try:
                # Extraer el ID del negocio de la URL
                path_parts = request.path.split('/')
                if len(path_parts) >= 4 and path_parts[3].isdigit():
                    negocio_id = int(path_parts[3])
                    
                    # Verificar que el negocio existe
                    negocio = get_object_or_404(Negocio, id=negocio_id, activo=True)
                    
                    # Registrar la actividad
                    ActividadUsuario.registrar_actividad(
                        usuario=request.user,
                        tipo='visita_negocio',
                        objeto_id=negocio_id,
                        objeto_tipo='negocio',
                        descripcion=f'Visitó el negocio {negocio.nombre}',
                        request=request
                    )
                    
                    logger.info(f"Actividad registrada: {request.user.username} visitó negocio {negocio_id}")
                    
            except Exception as e:
                logger.error(f"Error registrando actividad de visita: {str(e)}")
        
        return None 