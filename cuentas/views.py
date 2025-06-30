from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse
from .forms import RegistroUnificadoForm
from .models import UsuarioPersonalizado
import logging
from django.http import JsonResponse
from profesionales.models import Notificacion, Profesional, Matriculacion
from negocios.models import Negocio

logger = logging.getLogger(__name__)

def registro_unificado(request):
    """Vista unificada para registro con selección obligatoria de tipo de cuenta"""
    if request.method == 'POST':
        form = RegistroUnificadoForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.save()
                
                # Log del registro exitoso
                logger.info(f"Nuevo usuario registrado: {user.username} ({user.email}) - Tipo: {user.tipo}")
                
                # Iniciar sesión automáticamente con backend específico
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Mensaje de bienvenida según el tipo
                if user.tipo == 'cliente':
                    messages.success(request, f'¡Bienvenido a Melissa, {user.username}! Tu cuenta de cliente ha sido creada exitosamente.')
                    return redirect('clientes:dashboard')
                elif user.tipo == 'negocio':
                    messages.success(request, f'¡Bienvenido a Melissa, {user.username}! Tu cuenta de negocio ha sido creada exitosamente.')
                    return redirect('negocios:mis_negocios')
                elif user.tipo == 'profesional':
                    messages.success(request, f'¡Bienvenido a Melissa, {user.username}! Ahora completa tu perfil profesional.')
                    return redirect('profesionales:completar_perfil')
                
            except Exception as e:
                logger.error(f"Error al registrar usuario: {e}")
                messages.error(request, 'Hubo un error al crear tu cuenta. Por favor, intenta nuevamente.')
    else:
        form = RegistroUnificadoForm()
    
    return render(request, 'cuentas/registro_unificado.html', {'form': form})

@method_decorator(csrf_protect, name='dispatch')
class LoginPersonalizadoView(View):
    """Vista personalizada para login con redirección inteligente según tipo de usuario"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return self.redirect_by_user_type(request.user)
        
        form = AuthenticationForm()
        return render(request, 'account/login.html', {'form': form})
    
    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()
                if user is not None:
                    login(request, user)
                    
                    # Log del login exitoso
                    logger.info(f"Login exitoso: {user.username} ({user.email}) - Tipo: {user.tipo}")
                    
                    messages.success(request, f'¡Bienvenido de vuelta, {user.username}!')
                    
                    # Redirigir según el parámetro next o tipo de usuario
                    next_url = request.GET.get('next')
                    if next_url and next_url.startswith('/'):
                        return redirect(next_url)
                    else:
                        return self.redirect_by_user_type(user)
                else:
                    messages.error(request, 'Usuario o contraseña incorrectos. Por favor, verifica tus credenciales.')
                    
            except Exception as e:
                logger.error(f"Error en login: {e}")
                messages.error(request, 'Hubo un error al iniciar sesión. Por favor, intenta nuevamente.')
        else:
            # Log de intento de login fallido
            username = request.POST.get('username', '')
            logger.warning(f"Intento de login fallido para usuario: {username}")
            messages.error(request, 'Usuario o contraseña incorrectos. Por favor, verifica tus credenciales.')
        
        return render(request, 'account/login.html', {'form': form})
    
    def redirect_by_user_type(self, user):
        """Redirige al usuario según su tipo de cuenta"""
        if user.tipo == 'cliente':
            return redirect('clientes:dashboard')
        else:
            return redirect('negocios:mis_negocios')

@login_required
@require_http_methods(["POST"])
def logout_personalizado(request):
    """Vista personalizada para logout con mejor manejo"""
    try:
        username = request.user.username
        logout(request)
        
        # Log del logout
        logger.info(f"Logout exitoso: {username}")
        
        messages.success(request, 'Has cerrado sesión exitosamente. ¡Esperamos verte pronto!')
        
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        messages.error(request, 'Hubo un error al cerrar sesión.')
    
    return redirect('inicio')

@login_required
def perfil_usuario(request):
    """Vista para mostrar y editar el perfil del usuario"""
    user = request.user
    
    if request.method == 'POST':
        # Aquí puedes agregar lógica para actualizar el perfil
        messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
        return redirect('perfil_usuario')
    
    context = {
        'user': user,
        'es_cliente': user.tipo == 'cliente',
        'es_negocio': user.tipo == 'negocio',
    }
    
    return render(request, 'cuentas/perfil_usuario.html', context)

@login_required
def cambiar_tipo_usuario(request):
    """Vista para cambiar el tipo de usuario de cliente a negocio"""
    if request.method == 'POST':
        try:
            # Cambiar tipo de usuario a negocio
            user = request.user
            user.tipo = 'negocio'
            user.save()
            
            messages.success(request, 'Tu cuenta ha sido convertida a tipo negocio. Ahora puedes crear tu negocio.')
            return redirect('negocios:crear_negocio')
            
        except Exception as e:
            logger.error(f"Error al cambiar tipo de usuario: {e}")
            messages.error(request, 'Hubo un error al cambiar el tipo de cuenta.')
    
    return render(request, 'cuentas/cambiar_tipo_usuario.html')

@login_required
def seleccionar_tipo_cuenta_google(request):
    """
    Vista para que usuarios que se registraron con Google seleccionen su tipo de cuenta
    """
    # Verificar si el usuario ya tiene un tipo asignado
    if hasattr(request.user, 'tipo') and request.user.tipo:
        # Si ya tiene tipo, redirigir al dashboard correspondiente
        if request.user.tipo == 'cliente':
            return redirect('clientes:dashboard')
        else:
            return redirect('negocios:mis_negocios')

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        if tipo in ['cliente', 'negocio']:
            # Asignar tipo al usuario
            request.user.tipo = tipo
            request.user.save()

            messages.success(request, f'¡Bienvenido a Melissa! Tu cuenta ha sido configurada como {tipo}.')
            
            # Redirigir al dashboard correspondiente
            if tipo == 'cliente':
                return redirect('clientes:dashboard')
            else:
                return redirect('negocios:mis_negocios')

    return render(request, 'cuentas/seleccionar_tipo_cuenta.html')

@login_required
def completar_perfil_google(request):
    """
    Vista para completar el perfil de usuarios que se registraron con Google
    """
    if request.method == 'POST':
        # Actualizar información del perfil
        telefono = request.POST.get('telefono')
        if telefono:
            request.user.telefono = telefono
            request.user.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('clientes:dashboard' if request.user.tipo == 'cliente' else 'negocios:mis_negocios')

    return render(request, 'cuentas/completar_perfil_google.html', {
        'usuario_personalizado': request.user
    })

@login_required
def api_notificaciones(request):
    user = request.user
    data = []
    count_no_leidas = 0

    if user.tipo == 'profesional':
        profesional = getattr(user, 'perfil_profesional', None)
        if profesional:
            notis = Notificacion.objects.filter(profesional=profesional).order_by('-fecha_creacion')
            for n in notis:
                data.append({
                    'id': n.id,
                    'tipo': n.tipo,
                    'titulo': n.titulo,
                    'mensaje': n.mensaje,
                    'leida': n.leida,
                    'fecha': n.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                    'url': n.url_relacionada,
                })
            count_no_leidas = notis.filter(leida=False).count()
    elif user.tipo == 'negocio':
        # Solicitudes de matriculación pendientes
        negocios = Negocio.objects.filter(propietario=user)
        for negocio in negocios:
            solicitudes = Matriculacion.objects.filter(negocio=negocio, estado='pendiente')
            for s in solicitudes:
                data.append({
                    'id': s.id,
                    'tipo': 'matriculacion',
                    'titulo': f'Solicitud de matriculación de {s.profesional.nombre_completo}',
                    'mensaje': s.mensaje_solicitud,
                    'leida': False,
                    'fecha': s.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
                    'url': '',
                    'profesional_id': s.profesional.id,
                    'profesional_nombre': s.profesional.nombre_completo,
                })
            count_no_leidas += solicitudes.count()
        # Aquí puedes agregar notificaciones de reservas para negocio si las tienes
    elif user.tipo == 'cliente':
        # Si implementas notificaciones para clientes, agrégalas aquí
        pass
    return JsonResponse({'notificaciones': data, 'no_leidas': count_no_leidas})



