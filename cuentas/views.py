from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse
from .forms import RegistroUnificadoForm, FeedbackForm, RespuestaTicketForm, CambiarEstadoTicketForm, EditarPerfilClienteForm
from .models import UsuarioPersonalizado, Feedback, NotificacionAdmin, RespuestaTicket
import logging
from django.http import JsonResponse
from profesionales.models import Notificacion, Profesional, Matriculacion, MetricaProfesional, SolicitudAusencia
from negocios.models import Negocio, ServicioNegocio, Servicio, MetricaNegocio, ReporteMensual
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.db.models import Count, Avg, Q, Sum
import calendar
from datetime import datetime, timedelta
from django.db import models
from clientes.models import MetricaCliente
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
import subprocess
from .utils import log_user_activity, log_security_event, log_error, get_rate_limit_config
from django_ratelimit.decorators import ratelimit
from clientes.models import Reserva
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def registro_unificado(request):
    """Vista unificada para registro con selección obligatoria de tipo de cuenta"""
    if request.method == 'POST':
        form = RegistroUnificadoForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.save()
                
                # Log del registro exitoso
                log_user_activity(
                    user=user,
                    action="registro_exitoso",
                    details=f"Tipo: {user.tipo}, Email: {user.email}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
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
                log_error(
                    error_type="registro_fallido",
                    error_message=str(e),
                    user=None,
                    context={"form_data": request.POST}
                )
                messages.error(request, 'Hubo un error al crear tu cuenta. Por favor, intenta nuevamente.')
    else:
        form = RegistroUnificadoForm()
    
    return render(request, 'cuentas/registro_unificado.html', {'form': form})

# @method_decorator(csrf_protect, name='dispatch')
class LoginPersonalizadoView(View):
    """Vista personalizada para login con redirección inteligente según tipo de usuario"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return self.redirect_by_user_type(request.user)
        
        form = AuthenticationForm()
        return render(request, 'account/login.html', {'form': form})
    
    # @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()
                if user is not None:
                    login(request, user)
                    
                    # Log del login exitoso
                    log_user_activity(
                        user=user,
                        action="login_exitoso",
                        details=f"Tipo: {user.tipo}",
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                    messages.success(request, f'¡Bienvenido de vuelta, {user.username}!')
                    
                    # Si es superadmin, siempre redirigir a su panel
                    if user.is_superuser or getattr(user, 'tipo', None) == 'super_admin':
                        return self.redirect_by_user_type(user)
                    # Redirigir según el parámetro next o tipo de usuario
                    next_url = request.GET.get('next')
                    if next_url and next_url.startswith('/'):
                        return redirect(next_url)
                    else:
                        return self.redirect_by_user_type(user)
                else:
                    messages.error(request, 'Usuario o contraseña incorrectos. Por favor, verifica tus credenciales.')
                    
            except Exception as e:
                log_error(
                    error_type="login_error",
                    error_message=str(e),
                    user=None,
                    context={"username": request.POST.get('username', '')}
                )
                messages.error(request, 'Hubo un error al iniciar sesión. Por favor, intenta nuevamente.')
        else:
            # Log de intento de login fallido
            username = request.POST.get('username', '')
            log_security_event(
                user=None,
                event_type="login_fallido",
                details=f"Usuario: {username}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.error(request, 'Usuario o contraseña incorrectos. Por favor, verifica tus credenciales.')
        
        return render(request, 'account/login.html', {'form': form})
    
    def redirect_by_user_type(self, user):
        if user.is_superuser or getattr(user, 'tipo', None) == 'super_admin':
            return redirect('dashboard_super_admin')
        elif getattr(user, 'tipo', None) == 'cliente':
            return redirect('clientes:dashboard')
        elif getattr(user, 'tipo', None) == 'profesional':
            return redirect('profesionales:panel')
        elif getattr(user, 'tipo', None) == 'negocio':
            return redirect('negocios:mis_negocios')
        else:
            return redirect('inicio')

@login_required
@require_http_methods(["POST"])
def logout_personalizado(request):
    """Vista personalizada para logout con mejor manejo"""
    try:
        username = request.user.username
        user_type = getattr(request.user, 'tipo', '')
        
        # Log del logout antes de cerrar sesión
        log_user_activity(
            user=request.user,
            action="logout_exitoso",
            details=f"Tipo: {user_type}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        logout(request)
        
        messages.success(request, 'Has cerrado sesión exitosamente. ¡Esperamos verte pronto!')
        
    except Exception as e:
        log_error(
            error_type="logout_error",
            error_message=str(e),
            user=request.user if request.user.is_authenticated else None,
            context={"username": getattr(request.user, 'username', 'Unknown')}
        )
        messages.error(request, 'Hubo un error al cerrar sesión.')
    
    return redirect('inicio')

@login_required
def perfil_usuario(request):
    """Vista para mostrar y editar el perfil del usuario"""
    user = request.user
    if request.method == 'POST':
        form = EditarPerfilClienteForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
            return redirect('cuentas:perfil_usuario')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = EditarPerfilClienteForm(instance=user)
    context = {
        'user': user,
        'es_cliente': user.tipo == 'cliente',
        'es_negocio': user.tipo == 'negocio',
        'form': form,
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
            # Notificaciones regulares del profesional
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
            
            # Solicitudes de ausencia con respuestas (aprobadas/rechazadas)
            solicitudes_respuesta = SolicitudAusencia.objects.filter(
                profesional=profesional,
                estado__in=['aprobada', 'rechazada']
            ).order_by('-fecha_respuesta')
            
            for solicitud in solicitudes_respuesta:
                estado_texto = 'aprobada' if solicitud.estado == 'aprobada' else 'rechazada'
                data.append({
                    'id': f'ausencia_{solicitud.id}',
                    'tipo': 'solicitud_ausencia',
                    'titulo': f'Solicitud de ausencia {estado_texto}',
                    'mensaje': f'Tu solicitud del {solicitud.fecha_inicio} al {solicitud.fecha_fin} ha sido {estado_texto} por {solicitud.negocio.nombre}',
                    'leida': False,
                    'fecha': solicitud.fecha_respuesta.strftime('%d/%m/%Y %H:%M'),
                    'url': '/profesionales/gestionar-ausencias/',
                })
                count_no_leidas += 1
                
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
            
            # Solicitudes de ausencia pendientes
            solicitudes_ausencia = SolicitudAusencia.objects.filter(
                negocio=negocio,
                estado='pendiente'
            ).order_by('-fecha_solicitud')
            
            for solicitud in solicitudes_ausencia:
                data.append({
                    'id': f'ausencia_{solicitud.id}',
                    'tipo': 'solicitud_ausencia',
                    'titulo': f'Nueva solicitud de ausencia de {solicitud.profesional.nombre_completo}',
                    'mensaje': f'Solicita ausencia del {solicitud.fecha_inicio} al {solicitud.fecha_fin}',
                    'leida': False,
                    'fecha': solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
                    'url': f'/negocios/revisar-solicitud-ausencia/{solicitud.id}/',
                })
                count_no_leidas += 1
                
    elif user.tipo == 'cliente':
        # Si implementas notificaciones para clientes, agrégalas aquí
        pass
    return JsonResponse({'notificaciones': data, 'no_leidas': count_no_leidas})

# Helper para verificar si es super admin
def es_super_admin(user):
    return user.is_authenticated and user.tipo == 'super_admin'

@login_required
@user_passes_test(es_super_admin)
def dashboard_super_admin(request):
    total_negocios = UsuarioPersonalizado.objects.filter(tipo='negocio').count()
    total_clientes = UsuarioPersonalizado.objects.filter(tipo='cliente').count()
    total_profesionales = UsuarioPersonalizado.objects.filter(tipo='profesional').count()
    feedbacks = Feedback.objects.all().order_by('-fecha')

    # Evolución mensual (últimos 6 meses)
    today = timezone.now().date().replace(day=1)
    meses = []
    negocios_mensual = []
    clientes_mensual = []
    profesionales_mensual = []
    feedbacks_mensual = []
    for i in range(5, -1, -1):
        mes = (today.replace(day=1) - timezone.timedelta(days=30*i))
        year = mes.year
        month = mes.month
        label = f"{calendar.month_abbr[month]} {year}"
        meses.append(label)
        negocios_mensual.append(UsuarioPersonalizado.objects.filter(tipo='negocio', date_joined__year=year, date_joined__month=month).count())
        clientes_mensual.append(UsuarioPersonalizado.objects.filter(tipo='cliente', date_joined__year=year, date_joined__month=month).count())
        profesionales_mensual.append(UsuarioPersonalizado.objects.filter(tipo='profesional', date_joined__year=year, date_joined__month=month).count())
        feedbacks_mensual.append(Feedback.objects.filter(fecha__year=year, fecha__month=month).count())

    context = {
        'total_negocios': total_negocios,
        'total_clientes': total_clientes,
        'total_profesionales': total_profesionales,
        'feedbacks': feedbacks,
        'meses': meses,
        'negocios_mensual': negocios_mensual,
        'clientes_mensual': clientes_mensual,
        'profesionales_mensual': profesionales_mensual,
        'feedbacks_mensual': feedbacks_mensual,
    }
    return render(request, 'cuentas/dashboard_super_admin.html', context)

@login_required
def enviar_feedback(request):
    if request.user.tipo == 'super_admin':
        messages.error(request, 'El super admin no puede enviarse feedback a sí mismo.')
        return redirect('inicio')
    if request.method == 'POST':
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.usuario = request.user
            feedback.save()
            form.save_m2m()
            
            # Crear notificación para todos los superadmins
            superadmins = UsuarioPersonalizado.objects.filter(models.Q(is_superuser=True) | models.Q(tipo='super_admin'))
            for admin in superadmins:
                NotificacionAdmin.objects.create(
                    destinatario=admin,
                    tipo='ticket',
                    titulo=f'Nuevo ticket: {feedback.titulo}',
                    mensaje=f'Se ha creado un nuevo ticket #{feedback.numero_ticket} de {request.user.username}: "{feedback.mensaje[:100]}"',
                    url_relacionada=f'/cuentas/ticket/{feedback.id}/',
                )
            messages.success(request, f'¡Gracias por tu feedback! Tu ticket #{feedback.numero_ticket} ha sido creado.')
            return redirect('inicio')
    else:
        form = FeedbackForm()
    return render(request, 'cuentas/enviar_feedback.html', {'form': form})

@login_required
def redireccion_dashboard(request):
    user = request.user
    # Si es superusuario de Django o super_admin personalizado
    if user.is_superuser or getattr(user, 'tipo', None) == 'super_admin':
        return redirect('dashboard_super_admin')
    # Si es cliente
    elif getattr(user, 'tipo', None) == 'cliente':
        return redirect('dashboard_cliente')
    # Si es profesional
    elif getattr(user, 'tipo', None) == 'profesional':
        return redirect('dashboard_profesional')
    # Si es negocio
    elif getattr(user, 'tipo', None) == 'negocio':
        return redirect('dashboard_negocio')
    # Por defecto, home
    return redirect('home')

@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'tipo', None) == 'super_admin')
def analiticas_negocios(request):
    from negocios.models import Negocio
    from clientes.models import Reserva
    from profesionales.models import Profesional
    # Top 10 negocios con más reservas (último mes)
    from django.utils import timezone
    today = timezone.now().date()
    mes = today.month
    año = today.year
    top_negocios = Negocio.objects.annotate(
        num_reservas=models.Sum(
            models.Case(
                models.When(metricas__fecha__month=mes, metricas__fecha__year=año, then='metricas__total_reservas'),
                default=0,
                output_field=models.IntegerField()
            )
        )
    ).order_by('-num_reservas')[:10]
    # KPIs generales (hoy)
    metricas_hoy = MetricaNegocio.objects.filter(fecha=today)
    total_turnos = metricas_hoy.aggregate(total=models.Sum('total_reservas'))['total'] or 0
    tasa_ocupacion = 0  # Puedes calcularlo si tienes horas trabajadas/disponibles en MetricaNegocio
    # Servicios más solicitados y profesionales más reservados requieren lógica adicional o modelos agregados
    # Clientes recurrentes/nuevos, ingresos, cancelaciones, etc. pueden obtenerse de los modelos agregados
    # Ingresos generados (últimos 7 días, semanas, meses)
    ingresos_dia = []
    for m in metricas_hoy:
        ingresos_dia.append({
            'dia': m.fecha.strftime('%d/%m'),
            'total': float(m.ingresos_totales or 0)
        })
    metricas_mes = MetricaNegocio.objects.filter(fecha__month=mes, fecha__year=año)
    ingresos_mes = metricas_mes.aggregate(total=models.Sum('ingresos_totales'))['total'] or 0
    # Promedio de cancelaciones
    promedio_cancelaciones = metricas_hoy.aggregate(avg=models.Avg('reservas_canceladas'))['avg'] or 0
    
    # Variables faltantes para el template
    servicios_mas_solicitados = []  # Placeholder
    profesionales_mas_reservados = []  # Placeholder
    clientes_recurrentes = 0  # Placeholder
    clientes_nuevos = 0  # Placeholder
    ingresos_semana = []  # Placeholder - lista de diccionarios con 'semana' y 'total'
    calificacion_promedio = 0  # Placeholder
    
    # Corregir ingresos_mes para que sea una lista de diccionarios
    ingresos_mes_list = []
    # Crear datos de ejemplo para los últimos 6 meses
    for i in range(6):
        mes_num = (mes - i - 1) % 12 + 1
        año_mes = año if mes_num <= mes else año - 1
        ingresos_mes_list.append({
            'mes': f"{mes_num:02d}/{año_mes}",
            'total': float(ingresos_mes / 6)  # Distribuir el total entre los meses
        })
    
    # Para gráficas
    top_negocios_labels = [n.nombre for n in top_negocios]
    top_negocios_data = [n.num_reservas for n in top_negocios]
    servicios_labels = []
    servicios_data = []
    prof_labels = []
    prof_data = []
    
    context = {
        'top_negocios': top_negocios,
        'total_turnos': total_turnos,
        'tasa_ocupacion': tasa_ocupacion,
        'ingresos_dia': ingresos_dia,
        'ingresos_mes': ingresos_mes_list,  # Ahora es una lista de diccionarios
        'promedio_cancelaciones': promedio_cancelaciones,
        'servicios_mas_solicitados': servicios_mas_solicitados,
        'profesionales_mas_reservados': profesionales_mas_reservados,
        'clientes_recurrentes': clientes_recurrentes,
        'clientes_nuevos': clientes_nuevos,
        'ingresos_semana': ingresos_semana,
        'calificacion_promedio': calificacion_promedio,
        'top_negocios_labels': top_negocios_labels,
        'top_negocios_data': top_negocios_data,
        'servicios_labels': servicios_labels,
        'servicios_data': servicios_data,
        'prof_labels': prof_labels,
        'prof_data': prof_data,
    }
    return render(request, 'cuentas/analiticas_negocios.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'tipo', None) == 'super_admin')
def analiticas_profesionales(request):
    from django.utils import timezone
    today = timezone.now().date()
    mes = today.month
    año = today.year
    # Top 10 profesionales con más turnos (mes actual)
    top_profesionales = Profesional.objects.annotate(
        num_turnos=models.Sum(
            models.Case(
                models.When(metricas__fecha__month=mes, metricas__fecha__year=año, then='metricas__total_turnos'),
                default=0,
                output_field=models.IntegerField()
            )
        )
    ).order_by('-num_turnos')[:10]
    # Turnos agendados (hoy / semana / mes)
    turnos_hoy = MetricaProfesional.objects.filter(fecha=today).aggregate(total=models.Sum('total_turnos'))['total'] or 0
    turnos_semana = MetricaProfesional.objects.filter(fecha__week=today.isocalendar()[1], fecha__year=today.year).aggregate(total=models.Sum('total_turnos'))['total'] or 0
    turnos_mes = MetricaProfesional.objects.filter(fecha__month=mes, fecha__year=año).aggregate(total=models.Sum('total_turnos'))['total'] or 0
    # Tiempo promedio entre servicios y horas trabajadas (usando horas_trabajadas)
    metricas_mes = MetricaProfesional.objects.filter(fecha__month=mes, fecha__year=año)
    horas_trabajadas = metricas_mes.aggregate(total=models.Sum('horas_trabajadas'))['total'] or 0
    # Calificación promedio
    calificacion_promedio = metricas_mes.aggregate(avg=models.Avg('calificacion_promedio'))['avg'] or 0
    # Ingresos estimados
    ingresos_estimados = metricas_mes.aggregate(total=models.Sum('ingresos_totales'))['total'] or 0
    # Tasa de cancelaciones por profesional
    tasa_cancelaciones = []
    for profesional in top_profesionales:
        metricas_prof = profesional.metricas.filter(fecha__month=mes, fecha__year=año)
        total = metricas_prof.aggregate(total=models.Sum('total_turnos'))['total'] or 0
        canceladas = metricas_prof.aggregate(total=models.Sum('turnos_cancelados'))['total'] or 0
        tasa = (canceladas / total * 100) if total else 0
        tasa_cancelaciones.append({'profesional': profesional, 'tasa': round(tasa, 2)})
    # Horas disponibles (asumimos 8h por día con métricas)
    dias_con_reservas = metricas_mes.values('fecha').distinct().count()
    horas_disponibles = dias_con_reservas * 8 if dias_con_reservas else 1
    # Para gráficas en template (profesionales)
    top_prof_labels = [p.nombre_completo for p in top_profesionales]
    top_prof_data = [p.num_turnos for p in top_profesionales]
    cancel_labels = [t['profesional'].nombre_completo for t in tasa_cancelaciones]
    cancel_data = [t['tasa'] for t in tasa_cancelaciones]
    context = {
        'top_profesionales': top_profesionales,
        'turnos_hoy': turnos_hoy,
        'turnos_semana': turnos_semana,
        'turnos_mes': turnos_mes,
        'tiempo_promedio_servicio': 0,  # No disponible directo, opcional: calcularlo si se almacena
        'ingresos_estimados': ingresos_estimados,
        'calificacion_promedio': round(calificacion_promedio, 2),
        'tasa_cancelaciones': tasa_cancelaciones,
        'horas_trabajadas': horas_trabajadas,
        'horas_disponibles': horas_disponibles,
        'top_prof_labels': top_prof_labels,
        'top_prof_data': top_prof_data,
        'cancel_labels': cancel_labels,
        'cancel_data': cancel_data,
    }
    return render(request, 'cuentas/analiticas_profesionales.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'tipo', None) == 'super_admin')
def analiticas_clientes(request):
    from cuentas.models import UsuarioPersonalizado
    from profesionales.models import Profesional
    from django.utils import timezone
    today = timezone.now().date()
    mes = today.month
    año = today.year
    # Top 10 clientes con más turnos (mes actual)
    top_clientes = UsuarioPersonalizado.objects.filter(tipo='cliente').annotate(
        num_turnos=models.Sum(
            models.Case(
                models.When(metricas_cliente__fecha__month=mes, metricas_cliente__fecha__year=año, then='metricas_cliente__total_turnos'),
                default=0,
                output_field=models.IntegerField()
            )
        )
    ).order_by('-num_turnos')[:10]
    # Total de turnos agendados
    total_turnos = MetricaCliente.objects.filter(fecha__month=mes, fecha__year=año).aggregate(total=models.Sum('total_turnos'))['total'] or 0
    # Servicios más solicitados y profesionales más reservados (usando campos agregados)
    metricas_mes = MetricaCliente.objects.filter(fecha__month=mes, fecha__year=año)
    from collections import Counter
    servicios = []
    profesionales = []
    for m in metricas_mes:
        servicios += m.servicios_mas_solicitados.split(',') if m.servicios_mas_solicitados else []
        profesionales += m.profesionales_mas_reservados.split(',') if m.profesionales_mas_reservados else []
    servicios_mas_solicitados = Counter([s.strip() for s in servicios if s.strip()])
    profesionales_mas_reservados = Counter([p.strip() for p in profesionales if p.strip()])
    servicios_mas_solicitados = [{'nombre': s, 'num': n} for s, n in servicios_mas_solicitados.most_common(5)]
    profesionales_mas_reservados = [{'nombre_completo': p, 'num': n} for p, n in profesionales_mas_reservados.most_common(5)]
    # Tasa de asistencia vs cancelaciones
    total_cancelaciones = metricas_mes.aggregate(total=models.Sum('turnos_cancelados'))['total'] or 0
    tasa_asistencia = ((total_turnos - total_cancelaciones) / total_turnos * 100) if total_turnos else 0
    tasa_cancelaciones = (total_cancelaciones / total_turnos * 100) if total_turnos else 0
    # Tiempo promedio entre reservas (no disponible directo)
    tiempo_promedio = 0
    # Para gráficas en template (clientes)
    top_clientes_labels = [c.username for c in top_clientes]
    top_clientes_data = [c.num_turnos for c in top_clientes]
    servicios_labels = [s['nombre'] for s in servicios_mas_solicitados]
    servicios_data = [s['num'] for s in servicios_mas_solicitados]
    prof_labels = [p['nombre_completo'] for p in profesionales_mas_reservados]
    prof_data = [p['num'] for p in profesionales_mas_reservados]
    context = {
        'top_clientes': top_clientes,
        'total_turnos': total_turnos,
        'servicios_mas_solicitados': servicios_mas_solicitados,
        'tasa_asistencia': round(tasa_asistencia, 2),
        'tasa_cancelaciones': round(tasa_cancelaciones, 2),
        'tiempo_promedio': round(tiempo_promedio, 2),
        'profesionales_mas_reservados': profesionales_mas_reservados,
        'ingresos_estimados': 0,  # No disponible directo
        'top_clientes_labels': top_clientes_labels,
        'top_clientes_data': top_clientes_data,
        'servicios_labels': servicios_labels,
        'servicios_data': servicios_data,
        'prof_labels': prof_labels,
        'prof_data': prof_data,
    }
    return render(request, 'cuentas/analiticas_clientes.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'tipo', None) == 'super_admin')
def analiticas_general(request):
    from django.utils import timezone
    today = timezone.now().date()
    metricas_hoy = MetricaNegocio.objects.filter(fecha=today)
    turnos_hoy = metricas_hoy.aggregate(total=models.Sum('total_reservas'))['total'] or 0
    turnos_semana = metricas_hoy.aggregate(total=models.Sum('total_reservas'))['total'] or 0  # Puedes ajustar el filtro para la semana
    turnos_mes = metricas_hoy.aggregate(total=models.Sum('total_reservas'))['total'] or 0  # Puedes ajustar el filtro para el mes
    ingresos_estimados = metricas_hoy.aggregate(total=models.Sum('ingresos_totales'))['total'] or 0
    # ...otros KPIs...
    context = {
        'turnos_hoy': turnos_hoy,
        'turnos_semana': turnos_semana,
        'turnos_mes': turnos_mes,
        'ingresos_estimados': ingresos_estimados,
        # ...otros datos...
    }
    return render(request, 'cuentas/analiticas_general.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'tipo', None) == 'super_admin')
def notificaciones_super_admin(request):
    notificaciones = NotificacionAdmin.objects.filter(destinatario=request.user).order_by('-fecha_creacion')
    
    # Estadísticas de tickets
    tickets_pendientes = Feedback.objects.filter(estado='pendiente').count()
    tickets_en_proceso = Feedback.objects.filter(estado='en_proceso').count()
    tickets_resueltos = Feedback.objects.filter(estado='resuelto').count()
    tickets_urgentes = Feedback.objects.filter(prioridad='urgente').count()
    
    context = {
        'notificaciones': notificaciones,
        'tickets_pendientes': tickets_pendientes,
        'tickets_en_proceso': tickets_en_proceso,
        'tickets_resueltos': tickets_resueltos,
        'tickets_urgentes': tickets_urgentes,
    }
    return render(request, 'cuentas/notificaciones_super_admin.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'tipo', None) == 'super_admin')
def lista_tickets(request):
    """Vista para listar todos los tickets (solo super admin)"""
    tickets = Feedback.objects.all().order_by('-fecha')
    
    # Filtros
    estado = request.GET.get('estado')
    prioridad = request.GET.get('prioridad')
    categoria = request.GET.get('categoria')
    
    if estado:
        tickets = tickets.filter(estado=estado)
    if prioridad:
        tickets = tickets.filter(prioridad=prioridad)
    if categoria:
        tickets = tickets.filter(categoria=categoria)
    
    context = {
        'tickets': tickets,
        'estados': Feedback.ESTADO_CHOICES,
        'prioridades': Feedback.PRIORIDAD_CHOICES,
        'categorias': Feedback.objects.values_list('categoria', flat=True).distinct(),
        'filtros_activos': {
            'estado': estado,
            'prioridad': prioridad,
            'categoria': categoria,
        }
    }
    return render(request, 'cuentas/lista_tickets.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'tipo', None) == 'super_admin')
def detalle_ticket(request, ticket_id):
    """Vista para ver el detalle de un ticket y sus respuestas"""
    ticket = get_object_or_404(Feedback, id=ticket_id)
    respuestas = ticket.respuestas.all()
    form_respuesta = RespuestaTicketForm()
    form_estado = CambiarEstadoTicketForm(initial={'estado': ticket.estado})

    if request.method == 'POST':
        print(f"POST data: {request.POST}")  # Debug
        print(f"Current ticket state: {ticket.estado}")  # Debug
        
        # Detectar qué formulario se envió basándose en los campos presentes
        if 'estado' in request.POST:
            # Formulario de cambio de estado
            form_estado = CambiarEstadoTicketForm(request.POST)
            print(f"Estado form valid: {form_estado.is_valid()}")  # Debug
            if form_estado.is_valid():
                nuevo_estado = form_estado.cleaned_data['estado']
                mensaje = form_estado.cleaned_data['mensaje']
                print(f"Changing state from {ticket.estado} to {nuevo_estado}")  # Debug
                
                # Cambiar el estado del ticket
                ticket.cambiar_estado(nuevo_estado, request.user)
                print(f"State changed to: {ticket.estado}")  # Debug
                
                # Si hay mensaje adicional, crear respuesta
                if mensaje:
                    RespuestaTicket.objects.create(
                        ticket=ticket,
                        autor=request.user,
                        mensaje=mensaje
                    )
                
                # Notificar al usuario que creó el ticket sobre el cambio de estado
                estado_display = dict(Feedback.ESTADO_CHOICES)[nuevo_estado]
                NotificacionAdmin.objects.create(
                    destinatario=ticket.usuario,
                    tipo='respuesta_ticket',
                    titulo=f'Estado actualizado en ticket #{ticket.numero_ticket}',
                    mensaje=f'El estado de tu ticket ha sido cambiado a: {estado_display}',
                    url_relacionada=f'/cuentas/ticket/{ticket.id}/',
                )
                
                messages.success(request, f'Estado del ticket cambiado a: {estado_display}')
                return redirect('cuentas:detalle_ticket', ticket_id=ticket.id)
            else:
                print(f"Estado form errors: {form_estado.errors}")  # Debug
        elif 'mensaje' in request.POST and 'estado' not in request.POST:
            # Formulario de respuesta (solo mensaje, sin estado)
            form_respuesta = RespuestaTicketForm(request.POST)
            print(f"Respuesta form valid: {form_respuesta.is_valid()}")  # Debug
            if form_respuesta.is_valid():
                respuesta = form_respuesta.save(commit=False)
                respuesta.ticket = ticket
                respuesta.autor = request.user
                respuesta.save()
                print(f"Respuesta saved with ID: {respuesta.id}")  # Debug
                
                # Notificar al usuario que creó el ticket
                NotificacionAdmin.objects.create(
                    destinatario=ticket.usuario,
                    tipo='respuesta_ticket',
                    titulo=f'Nueva respuesta en ticket #{ticket.numero_ticket}',
                    mensaje=f'El administrador ha respondido a tu ticket: "{respuesta.mensaje[:100]}"',
                    url_relacionada=f'/cuentas/ticket/{ticket.id}/',
                )
                
                messages.success(request, 'Respuesta enviada correctamente.')
                return redirect('cuentas:detalle_ticket', ticket_id=ticket.id)
            else:
                print(f"Respuesta form errors: {form_respuesta.errors}")  # Debug

    # Marcar como leído por admin
    if not ticket.leido_por_admin:
        ticket.leido_por_admin = True
        ticket.save()

    context = {
        'ticket': ticket,
        'respuestas': respuestas,
        'form_respuesta': form_respuesta,
        'form_estado': form_estado,
    }
    return render(request, 'cuentas/detalle_ticket.html', context)

@login_required
def mis_tickets(request):
    """Vista para que los usuarios vean sus propios tickets"""
    tickets = Feedback.objects.filter(usuario=request.user).order_by('-fecha')
    context = {
        'tickets': tickets,
    }
    return render(request, 'cuentas/mis_tickets.html', context)

@login_required
def detalle_mi_ticket(request, ticket_id):
    """Vista para que los usuarios vean el detalle de su ticket"""
    ticket = get_object_or_404(Feedback, id=ticket_id, usuario=request.user)
    respuestas = ticket.respuestas.all()
    
    if request.method == 'POST':
        form_respuesta = RespuestaTicketForm(request.POST)
        if form_respuesta.is_valid():
            respuesta = form_respuesta.save(commit=False)
            respuesta.ticket = ticket
            respuesta.autor = request.user
            respuesta.save()
            
            # Notificar a los super admins
            superadmins = UsuarioPersonalizado.objects.filter(models.Q(is_superuser=True) | models.Q(tipo='super_admin'))
            for admin in superadmins:
                NotificacionAdmin.objects.create(
                    destinatario=admin,
                    tipo='respuesta_ticket',
                    titulo=f'Nueva respuesta de usuario en ticket #{ticket.numero_ticket}',
                    mensaje=f'El usuario {request.user.username} ha respondido: "{respuesta.mensaje[:100]}"',
                    url_relacionada=f'/cuentas/ticket/{ticket.id}/',
                )
            
            messages.success(request, 'Respuesta enviada correctamente.')
            return redirect('cuentas:detalle_mi_ticket', ticket_id=ticket.id)
    else:
        form_respuesta = RespuestaTicketForm()
    
    # Marcar como leído por usuario
    if not ticket.leido_por_usuario:
        ticket.leido_por_usuario = True
        ticket.save()
    
    context = {
        'ticket': ticket,
        'respuestas': respuestas,
        'form_respuesta': form_respuesta,
    }
    return render(request, 'cuentas/detalle_mi_ticket.html', context)

def ajustes_usuario(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            user = request.user
            logout(request)
            user.delete()
            return redirect('inicio')
    return render(request, 'cuentas/ajustes.html')

def politica_datos(request):
    return render(request, 'cuentas/politica_datos.html')

@staff_member_required
def ejecutar_tests(request):
    resultado = None
    if request.method == 'POST':
        # Ejecutar los tests usando manage.py test
        try:
            completed = subprocess.run(['python', 'manage.py', 'test', '--verbosity', '2'], capture_output=True, text=True, timeout=120)
            resultado = completed.stdout + '\n' + completed.stderr
        except Exception as e:
            resultado = str(e)
    return render(request, 'cuentas/ejecutar_tests.html', {'resultado': resultado})

@staff_member_required
def poblar_demo(request):
    resultado = None
    if request.method == 'POST':
        try:
            completed = subprocess.run(['python', 'manage.py', 'poblar_demo'], capture_output=True, text=True, timeout=60)
            resultado = completed.stdout + '\n' + completed.stderr
        except Exception as e:
            resultado = str(e)
    return render(request, 'cuentas/poblar_demo.html', {'resultado': resultado})

@staff_member_required
def borrar_demo(request):
    resultado = None
    if request.method == 'POST':
        try:
            completed = subprocess.run(['python', 'manage.py', 'borrar_demo'], capture_output=True, text=True, timeout=60)
            resultado = completed.stdout + '\n' + completed.stderr
        except Exception as e:
            resultado = str(e)
    return render(request, 'cuentas/borrar_demo.html', {'resultado': resultado})

@staff_member_required
def reiniciar_servidor(request):
    import os, sys
    resultado = None
    if request.method == 'POST':
        try:
            # Solo para desarrollo: tocar manage.py para forzar autoreload
            manage_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'manage.py')
            with open(manage_py, 'a') as f:
                f.write('\n# touch for reload\n')
            resultado = 'Servidor de desarrollo: se forzó recarga (Django autoreload)'
        except Exception as e:
            resultado = str(e)
    return render(request, 'cuentas/reiniciar_servidor.html', {'resultado': resultado})

@staff_member_required
def ver_logs_servidor(request):
    """Vista para ver logs del sistema"""
    try:
        import os
        from pathlib import Path
        
        # Obtener directorio de logs
        logs_dir = Path(__file__).resolve().parent.parent / 'logs'
        
        # Tipos de logs disponibles
        log_files = {
            'general': 'melissa_general.log',
            'errors': 'melissa_errors.log', 
            'security': 'melissa_security.log',
            'activity': 'melissa_activity.log',
            'business': 'melissa_business.log',
            'recordatorios': 'melissa_recordatorios.log'
        }
        
        # Obtener tipo de log solicitado
        log_type = request.GET.get('type', 'general')
        log_filename = log_files.get(log_type, 'melissa_general.log')
        log_path = logs_dir / log_filename
        
        # Leer las últimas 100 líneas del log
        lines = []
        if log_path.exists():
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-100:]  # Últimas 100 líneas
            except Exception as e:
                log_error(
                    error_type="error_leer_log",
                    error_message=str(e),
                    user=request.user,
                    context={"log_file": log_filename}
                )
                lines = [f"Error leyendo archivo de log: {str(e)}"]
        else:
            lines = [f"Archivo de log no encontrado: {log_filename}"]
        
        # Obtener estadísticas de logs
        log_stats = {}
        for log_name, filename in log_files.items():
            file_path = logs_dir / filename
            if file_path.exists():
                try:
                    size = file_path.stat().st_size
                    log_stats[log_name] = {
                        'size_mb': round(size / (1024 * 1024), 2),
                        'exists': True
                    }
                except:
                    log_stats[log_name] = {'size_mb': 0, 'exists': False}
            else:
                log_stats[log_name] = {'size_mb': 0, 'exists': False}
        
        context = {
            'log_content': ''.join(lines),
            'log_type': log_type,
            'log_files': log_files,
            'log_stats': log_stats,
            'logs_dir': str(logs_dir)
        }
        
        return render(request, 'cuentas/ver_logs.html', context)
        
    except Exception as e:
        log_error(
            error_type="error_vista_logs",
            error_message=str(e),
            user=request.user
        )
        messages.error(request, 'Error al cargar los logs del servidor.')
        return redirect('dashboard_super_admin')

@ratelimit(key='ip', rate=lambda: get_rate_limit_config('test_rate', '10/m'), method=['GET', 'POST'])
def test_rate_limit(request):
    """Vista de prueba para verificar rate limiting"""
    if request.method == 'POST':
        return JsonResponse({
            'message': 'Rate limit test exitoso',
            'timestamp': datetime.now().isoformat(),
            'ip': request.META.get('REMOTE_ADDR')
        })
    
    return JsonResponse({
        'message': 'GET request exitoso',
        'timestamp': datetime.now().isoformat(),
        'ip': request.META.get('REMOTE_ADDR')
    })

@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'tipo', None) == 'super_admin')
def gestionar_rate_limiting(request):
    """Vista para gestionar configuraciones de rate limiting"""
    from .models import RateLimitConfig
    
    if request.method == 'POST':
        # Procesar cambios en las configuraciones
        for config in RateLimitConfig.objects.all():
            nuevo_limite = request.POST.get(f'limite_{config.id}')
            nuevo_activo = request.POST.get(f'activo_{config.id}') == 'on'
            
            if nuevo_limite and nuevo_limite != config.limite:
                config.limite = nuevo_limite
                config.save()
                messages.success(request, f'Límite actualizado para {config.nombre}')
            
            if config.activo != nuevo_activo:
                config.activo = nuevo_activo
                config.save()
                status = 'activada' if nuevo_activo else 'desactivada'
                messages.success(request, f'{config.nombre} {status}')
        
        # Limpiar caché después de cambios
        from django.core.cache import cache
        cache.clear()
        messages.success(request, 'Configuraciones de rate limiting actualizadas correctamente.')
        return redirect('cuentas:gestionar_rate_limiting')
    
    configuraciones = RateLimitConfig.objects.all().order_by('nombre')
    
    context = {
        'configuraciones': configuraciones,
        'total_activas': configuraciones.filter(activo=True).count(),
        'total_inactivas': configuraciones.filter(activo=False).count(),
    }
    
    return render(request, 'cuentas/gestionar_rate_limiting.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'tipo', None) == 'super_admin')
def control_reservas(request):
    # Obtener el límite actual (de cache o default)
    max_reservas = cache.get('max_reservas_por_servicio_dia', 2)
    if request.method == 'POST':
        try:
            nuevo_limite = int(request.POST.get('max_reservas', 2))
            if 1 <= nuevo_limite <= 10:
                cache.set('max_reservas_por_servicio_dia', nuevo_limite, timeout=None)
                max_reservas = nuevo_limite
                messages.success(request, 'Límite actualizado correctamente.')
            else:
                messages.error(request, 'El límite debe estar entre 1 y 10.')
        except Exception:
            messages.error(request, 'Valor inválido para el límite.')
    # Resumen de reservas activas por cliente y servicio para hoy
    hoy = timezone.now().date()
    resumen = (
        Reserva.objects.filter(fecha=hoy, estado__in=['pendiente', 'confirmado'])
        .values('cliente__username', 'servicio__servicio__nombre')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')
    )
    resumen = [
        {'cliente': r['cliente__username'], 'servicio': r['servicio__servicio__nombre'], 'cantidad': r['cantidad']}
        for r in resumen
    ]
    return render(request, 'cuentas/control_reservas.html', {
        'max_reservas': max_reservas,
        'resumen': resumen,
    })



