import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)

class AuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware personalizado para mejorar la experiencia de autenticación
    """
    
    def process_request(self, request):
        """Procesa cada request para mejorar la experiencia de autenticación"""
        
        # Log de requests para usuarios autenticados
        if request.user.is_authenticated:
            logger.debug(f"Request de usuario autenticado: {request.user.username} - {request.path}")
        
        # Verificar si el usuario necesita verificar su email
        if (request.user.is_authenticated and 
            not request.user.is_staff and 
            not request.user.is_superuser and
            hasattr(request.user, 'email') and 
            request.user.email and
            not request.path.startswith('/admin/') and
            not request.path.startswith('/accounts/') and
            not request.path.startswith('/cuentas/')):
            
            # Aquí puedes agregar lógica adicional para verificación de email
            pass
        
        return None
    
    def process_response(self, request, response):
        """Procesa la respuesta para agregar headers de seguridad adicionales"""
        
        # Agregar headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Log de respuestas de error
        if response.status_code >= 400:
            logger.warning(f"Error {response.status_code} en {request.path} - Usuario: {request.user.username if request.user.is_authenticated else 'Anónimo'}")
        
        return response

class UserTypeMiddleware(MiddlewareMixin):
    """
    Middleware para manejar el tipo de usuario y redirecciones
    """
    
    def process_request(self, request):
        """Procesa el request para manejar tipos de usuario"""
        
        if request.user.is_authenticated:
            # Agregar información del tipo de usuario al request
            request.es_cliente = getattr(request.user, 'tipo', None) == 'cliente'
            request.es_negocio = getattr(request.user, 'tipo', None) == 'negocio'
            
            # Redirecciones basadas en el tipo de usuario
            if request.path == '/':
                if request.es_negocio and not request.user.negocios.exists():
                    # Si es negocio y no tiene negocios, sugerir crear uno
                    messages.info(request, 'Como dueño de negocio, te recomendamos crear tu primer negocio.')
                elif request.es_cliente:
                    # Si es cliente, mostrar opciones de búsqueda
                    pass
        
        return None 