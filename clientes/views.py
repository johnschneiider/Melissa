from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.utils import timezone
from datetime import timedelta, datetime, time
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from negocios.models import Negocio, ServicioNegocio, Servicio
from .models import Reserva, NotificacionCliente, Calificacion
from .forms import ReservaForm, ReservaNegocioForm, CalificacionForm
from .utils import enviar_email_reserva_confirmada, enviar_email_reserva_cancelada, enviar_email_reserva_reagendada
import json
import holidays
import logging
from django.core.exceptions import ValidationError
from django.utils.html import escape
import re
from django.db.models import Q
from profesionales.models import Notificacion, Profesional, Matriculacion, HorarioProfesional
from django.db import models
from math import radians, cos, sin, asin, sqrt
from cuentas.utils import log_user_activity, log_reservation_activity, log_error
from django_ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)

def sanitize_input(text):
    """Sanitizar entrada de texto para prevenir XSS"""
    if text:
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<.*?>', '', text)
        return escape(text.strip())
    return text

class ListaNegociosView(ListView):
    model = Negocio
    template_name = 'clientes/lista_negocios.html'
    context_object_name = 'negocios'
    
    def get_queryset(self):
        try:
            return Negocio.objects.filter(activo=True)
        except Exception as e:
            logger.error(f"Error obteniendo lista de negocios: {str(e)}")
            return Negocio.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            negocios = context['negocios']
            negocios_mapa = []
            for negocio in negocios:
                profesionales_aceptados = [m.profesional for m in Matriculacion.objects.filter(negocio=negocio, estado='aprobada')]
                negocios_mapa.append({
                    'id': negocio.id,
                    'nombre': negocio.nombre,
                    'direccion': negocio.direccion,
                    'latitud': negocio.latitud,
                    'longitud': negocio.longitud,
                    'url': f"/clientes/detalle_peluquero/{negocio.id}/",  # Ajusta si tienes un nombre de url
                    'logo_url': negocio.logo.url if negocio.logo else '',
                    'profesionales': profesionales_aceptados,
                })
            context['negocios_mapa'] = negocios_mapa
        except Exception as e:
            logger.error(f"Error procesando contexto de negocios: {str(e)}")
            context['negocios_mapa'] = []
        return context

class DetallePeluqueroView(DetailView):
    model = Negocio
    template_name = 'clientes/detalle_peluquero.html'
    context_object_name = 'negocio'
    
    def get_queryset(self):
        return Negocio.objects.filter(activo=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        negocio = self.object
        
        try:
            # Obtener los próximos 14 días de disponibilidad
            hoy = timezone.now().date()
            proximos_dias = [hoy + timedelta(days=i) for i in range(14)]
            
            # Verificar días festivos
            co_holidays = holidays.CountryHoliday('CO')
            
            dias_disponibilidad = []
            for dia in proximos_dias:
                nombre_dia = dia.strftime('%A')
                nombre_dia_es = {
                    'Monday': 'Lunes',
                    'Tuesday': 'Martes',
                    'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves',
                    'Friday': 'Viernes',
                    'Saturday': 'Sábado',
                    'Sunday': 'Domingo'
                }.get(nombre_dia, nombre_dia)
                
                es_festivo = dia in co_holidays or nombre_dia_es == 'Domingo'
                
                # Obtener horario del negocio para este día
                horario = negocio.horario_atencion.get(nombre_dia_es, {}) if negocio.horario_atencion else {}
                turnos = horario.get('turnos', []) if horario else []
                
                # Verificar reservas existentes para este día
                reservas_dia = Reserva.objects.filter(
                    peluquero=negocio,
                    fecha=dia,
                    estado__in=['pendiente', 'confirmado']
                ).values_list('hora_inicio', 'hora_fin')
                
                # Calcular intervalos disponibles
                intervalos_disponibles = []
                for turno in turnos:
                    if turno.get('disponible', True) and not es_festivo:
                        try:
                            inicio = datetime.strptime(turno['inicio'], '%H:%M').time()
                            fin = datetime.strptime(turno['fin'], '%H:%M').time()
                            duracion = int(turno.get('duracion', 30))
                            
                            # Generar intervalos
                            inicio_minutos = inicio.hour * 60 + inicio.minute
                            fin_minutos = fin.hour * 60 + fin.minute
                            tiempo_actual = inicio_minutos
                            
                            while tiempo_actual + duracion <= fin_minutos:
                                hora_inicio = time(tiempo_actual // 60, tiempo_actual % 60)
                                hora_fin = time((tiempo_actual + duracion) // 60, (tiempo_actual + duracion) % 60)
                                
                                # Verificar si este intervalo está disponible
                                ocupado = False
                                for reserva_inicio, reserva_fin in reservas_dia:
                                    if not (hora_fin <= reserva_inicio or hora_inicio >= reserva_fin):
                                        ocupado = True
                                        break
                                        
                                if not ocupado:
                                    intervalos_disponibles.append({
                                        'inicio': hora_inicio.strftime('%H:%M'),
                                        'fin': hora_fin.strftime('%H:%M'),
                                        'duracion': duracion
                                    })
                                    
                                tiempo_actual += duracion
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Error procesando turno: {str(e)}")
                            continue
                
                dias_disponibilidad.append({
                    'fecha': dia,
                    'nombre_dia': nombre_dia_es,
                    'festivo': es_festivo,
                    'intervalos': intervalos_disponibles
                })
            
            context['dias_disponibilidad'] = dias_disponibilidad
            context['hoy'] = hoy
        except Exception as e:
            logger.error(f"Error procesando disponibilidad: {str(e)}")
            context['dias_disponibilidad'] = []
            context['hoy'] = timezone.now().date()
        # Calcular promedio y total de calificaciones
        calificaciones = negocio.calificaciones.all()
        total_opiniones = calificaciones.count()
        if total_opiniones > 0:
            promedio = sum([c.puntaje for c in calificaciones]) / total_opiniones
        else:
            promedio = None
        context['promedio_calificacion'] = promedio
        context['total_opiniones'] = total_opiniones
        return context

@login_required
@csrf_protect
@ratelimit(key='ip', rate='10/m', method=['POST'])
def reservar_turno(request, peluquero_id):
    try:
        negocio = get_object_or_404(Negocio, id=peluquero_id, activo=True)
        
        if request.method == 'POST':
            form = ReservaForm(request.POST, negocio=negocio)
            if form.is_valid():
                try:
                    # Obtener los datos del formulario
                    servicio = form.cleaned_data.get('servicio')
                    profesional = form.cleaned_data.get('profesional')
                    fecha = form.cleaned_data.get('fecha')
                    hora_inicio = form.cleaned_data.get('hora_inicio')
                    notas = form.cleaned_data.get('notas', '')
                    
                    logger.info(f"Datos del formulario - servicio: {servicio}, profesional: {profesional}, fecha: {fecha}, hora_inicio: {hora_inicio}")
                    
                    # Crear la reserva manualmente
                    reserva = Reserva(
                        cliente=request.user,
                        peluquero=negocio,
                        profesional=profesional,
                        fecha=fecha,
                        hora_inicio=hora_inicio,
                        servicio=servicio,
                        notas=notas,
                        estado='pendiente'
                    )
                    
                    # Calcular hora_fin usando la duración del servicio
                    if servicio and hora_inicio:
                        duracion = servicio.duracion
                        from datetime import datetime, timedelta
                        hora_inicio_dt = datetime.combine(fecha, hora_inicio)
                        hora_fin_dt = hora_inicio_dt + timedelta(minutes=duracion)
                        reserva.hora_fin = hora_fin_dt.time()
                        logger.info(f"Hora fin calculada: {reserva.hora_fin}")
                    
                    logger.info(f"Intentando guardar reserva con datos: cliente={reserva.cliente.id}, peluquero={reserva.peluquero.id}, profesional={reserva.profesional.id if reserva.profesional else None}, servicio={reserva.servicio.id if reserva.servicio else None}")
                    
                    reserva.save()
                    
                    # Log de actividad de reserva exitosa
                    log_reservation_activity(
                        user=request.user,
                        reservation=reserva,
                        action="reserva_creada",
                        details=f"Negocio: {negocio.nombre}, Servicio: {servicio.nombre}, Fecha: {fecha}, Hora: {hora_inicio}"
                    )
                    
                    # Crear notificación para el profesional si existe
                    if reserva.profesional:
                        from profesionales.models import Notificacion
                        Notificacion.objects.create(
                            profesional=reserva.profesional,
                            tipo='reserva',
                            titulo='Nueva Reserva',
                            mensaje=f'Nueva reserva pendiente para el {reserva.fecha} a las {reserva.hora_inicio} con {reserva.cliente.username}.',
                            url_relacionada='/profesionales/panel/'
                        )
                    
                    # Enviar email de confirmación
                    try:
                        enviar_email_reserva_confirmada(reserva)
                    except Exception as e:
                        log_error(
                            error_type="email_confirmacion_fallido",
                            error_message=str(e),
                            user=request.user,
                            context={"reserva_id": reserva.id}
                        )
                        # No fallar la reserva si el email falla
                    
                    messages.success(request, '¡Reserva realizada con éxito!')
                    return redirect('clientes:confirmacion_reserva', reserva_id=reserva.id)
                except Exception as e:
                    log_error(
                        error_type="reserva_fallida",
                        error_message=str(e),
                        user=request.user,
                        context={
                            "negocio_id": negocio.id,
                            "servicio": servicio.nombre if servicio else None,
                            "fecha": fecha,
                            "hora_inicio": hora_inicio
                        }
                    )
                    messages.error(request, 'Error al guardar la reserva. Por favor, intenta nuevamente.')
            else:
                log_user_activity(
                    user=request.user,
                    action="formulario_reserva_invalido",
                    details=f"Errores: {form.errors}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
        else:
            form = ReservaForm(negocio=negocio)
        
        return render(request, 'clientes/reservar_turno.html', {
            'negocio': negocio,
            'form': form
        })
    except Exception as e:
        log_error(
            error_type="error_cargar_reserva",
            error_message=str(e),
            user=request.user if request.user.is_authenticated else None,
            context={"peluquero_id": peluquero_id}
        )
        messages.error(request, 'Error al cargar la página de reserva.')
        return redirect('clientes:lista_negocios')

@login_required
@require_GET
def confirmacion_reserva(request, reserva_id):
    try:
        reserva = get_object_or_404(Reserva, id=reserva_id, cliente=request.user)
        return render(request, 'clientes/confirmacion_reserva.html', {'reserva': reserva})
    except Exception as e:
        logger.error(f"Error mostrando confirmación de reserva: {str(e)}")
        messages.error(request, 'Error al mostrar la confirmación de la reserva.')
        return redirect('clientes:lista_negocios')

@require_GET
def horarios_disponibles(request, negocio_id):
    try:
        negocio = get_object_or_404(Negocio, id=negocio_id, activo=True)
        fecha = request.GET.get('fecha')
        servicio_negocio_id = request.GET.get('servicio_negocio_id')
        profesional_id = request.GET.get('profesional_id')
        duracion = None
        
        # Log de depuración
        logger.info(f"horarios_disponibles - negocio_id: {negocio_id}, fecha: {fecha}, profesional_id: {profesional_id}, servicio_id: {servicio_negocio_id}")
        
        if servicio_negocio_id:
            try:
                servicio_negocio = ServicioNegocio.objects.get(id=servicio_negocio_id, negocio=negocio)
                duracion = servicio_negocio.duracion
                logger.info(f"Servicio encontrado: {servicio_negocio.servicio.nombre}, duración: {duracion}")
            except ServicioNegocio.DoesNotExist:
                logger.warning(f"ServicioNegocio no encontrado: {servicio_negocio_id}")
                pass
        if not fecha or not profesional_id:
            logger.warning(f"Faltan parámetros: fecha={fecha}, profesional_id={profesional_id}")
            return JsonResponse({'error': 'Fecha y profesional requeridos'}, status=400)
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"Formato de fecha inválido: {fecha}")
            return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
        # Verificar si es festivo
        co_holidays = holidays.CountryHoliday('CO')
        nombre_dia = fecha_obj.strftime('%A')
        nombre_dia_es = {
            'Monday': 'lunes',
            'Tuesday': 'martes',
            'Wednesday': 'miercoles',
            'Thursday': 'jueves',
            'Friday': 'viernes',
            'Saturday': 'sabado',
            'Sunday': 'domingo'
        }.get(nombre_dia, nombre_dia)
        es_festivo = fecha_obj in co_holidays or nombre_dia_es == 'domingo'
        
        logger.info(f"Día de la semana: {nombre_dia} -> {nombre_dia_es}, es_festivo: {es_festivo}")
        
        if es_festivo:
            logger.info("Es festivo, no hay horarios disponibles")
            return JsonResponse({'disponibles': [], 'festivo': True})
        # Buscar horario del profesional para ese día
        profesional = get_object_or_404(Profesional, id=profesional_id)
        logger.info(f"Profesional encontrado: {profesional.nombre_completo}")
        
        horario_prof = HorarioProfesional.objects.filter(profesional=profesional, dia_semana=nombre_dia_es, disponible=True).first()
        logger.info(f"Horario del profesional para {nombre_dia_es}: {horario_prof}")
        
        if not horario_prof:
            # Log todos los horarios del profesional para depuración
            todos_horarios = HorarioProfesional.objects.filter(profesional=profesional)
            logger.info(f"Todos los horarios del profesional: {list(todos_horarios)}")
            return JsonResponse({'disponibles': [], 'festivo': False})
        
        inicio = horario_prof.hora_inicio
        fin = horario_prof.hora_fin
        duracion_turno = duracion or 30
        
        logger.info(f"Horario: {inicio} - {fin}, duración turno: {duracion_turno}")
        
        # Obtener reservas existentes para este profesional, negocio y día
        reservas = Reserva.objects.filter(
            peluquero=negocio,
            profesional=profesional,
            fecha=fecha_obj,
            estado__in=['pendiente', 'confirmado']
        ).values_list('hora_inicio', 'hora_fin')
        
        logger.info(f"Reservas existentes: {list(reservas)}")
        
        # Generar slots
        horarios_disponibles = []
        inicio_minutos = inicio.hour * 60 + inicio.minute
        fin_minutos = fin.hour * 60 + fin.minute
        tiempo_actual = inicio_minutos
        
        logger.info(f"Generando slots desde {inicio_minutos} hasta {fin_minutos} minutos")
        
        while tiempo_actual + duracion_turno <= fin_minutos:
            hora_inicio = time(tiempo_actual // 60, tiempo_actual % 60)
            hora_fin = time((tiempo_actual + duracion_turno) // 60, (tiempo_actual + duracion_turno) % 60)
            # Verificar si este slot está ocupado
            ocupado = False
            for reserva_inicio, reserva_fin in reservas:
                if not (hora_fin <= reserva_inicio or hora_inicio >= reserva_fin):
                    ocupado = True
                    break
            if not ocupado:
                horarios_disponibles.append({
                    'inicio': hora_inicio.strftime('%H:%M'),
                    'fin': hora_fin.strftime('%H:%M'),
                    'duracion': duracion_turno
                })
            tiempo_actual += duracion_turno
        
        logger.info(f"Slots generados: {len(horarios_disponibles)}")
        
        return JsonResponse({
            'disponibles': horarios_disponibles,
            'festivo': False
        })
    except Exception as e:
        logger.error(f"Error en horarios_disponibles: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

@require_GET
def horarios_disponibles_reagendar(request, reserva_id):
    """Vista para obtener horarios disponibles al reagendar una reserva"""
    try:
        reserva = get_object_or_404(Reserva, id=reserva_id, cliente=request.user)
        fecha = request.GET.get('fecha')
        
        if not fecha:
            return JsonResponse({'error': 'Fecha requerida'}, status=400)
        
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
        
        # Verificar si es festivo
        co_holidays = holidays.CountryHoliday('CO')
        nombre_dia = fecha_obj.strftime('%A')
        nombre_dia_es = {
            'Monday': 'lunes',
            'Tuesday': 'martes',
            'Wednesday': 'miercoles',
            'Thursday': 'jueves',
            'Friday': 'viernes',
            'Saturday': 'sabado',
            'Sunday': 'domingo'
        }.get(nombre_dia, nombre_dia)
        es_festivo = fecha_obj in co_holidays or nombre_dia_es == 'domingo'
        
        if es_festivo:
            return JsonResponse({'disponibles': [], 'festivo': True})
        
        # Obtener información de la reserva
        negocio = reserva.peluquero
        profesional = reserva.profesional
        duracion = reserva.servicio.duracion if reserva.servicio else 30
        
        # Buscar horario del profesional para ese día
        horario_prof = HorarioProfesional.objects.filter(
            profesional=profesional, 
            dia_semana=nombre_dia_es, 
            disponible=True
        ).first()
        
        if not horario_prof:
            return JsonResponse({'disponibles': [], 'festivo': False})
        
        inicio = horario_prof.hora_inicio
        fin = horario_prof.hora_fin
        
        # Obtener reservas existentes para este profesional, negocio y día (excluyendo la reserva actual)
        reservas = Reserva.objects.filter(
            peluquero=negocio,
            profesional=profesional,
            fecha=fecha_obj,
            estado__in=['pendiente', 'confirmado']
        ).exclude(id=reserva.id).values_list('hora_inicio', 'hora_fin')
        
        # Generar slots
        horarios_disponibles = []
        inicio_minutos = inicio.hour * 60 + inicio.minute
        fin_minutos = fin.hour * 60 + fin.minute
        tiempo_actual = inicio_minutos
        
        while tiempo_actual + duracion <= fin_minutos:
            hora_inicio = time(tiempo_actual // 60, tiempo_actual % 60)
            hora_fin = time((tiempo_actual + duracion) // 60, (tiempo_actual + duracion) % 60)
            
            # Verificar si este slot está ocupado
            ocupado = False
            for reserva_inicio, reserva_fin in reservas:
                if not (hora_fin <= reserva_inicio or hora_inicio >= reserva_fin):
                    ocupado = True
                    break
            
            if not ocupado:
                horarios_disponibles.append({
                    'inicio': hora_inicio.strftime('%H:%M'),
                    'fin': hora_fin.strftime('%H:%M'),
                    'duracion': duracion
                })
            
            tiempo_actual += duracion
        
        return JsonResponse({
            'disponibles': horarios_disponibles,
            'festivo': False
        })
        
    except Exception as e:
        logger.error(f"Error en horarios_disponibles_reagendar: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

@login_required
def mis_reservas(request):
    """Vista para que los clientes vean sus reservas"""
    try:
        reservas = Reserva.objects.filter(
            cliente=request.user
        ).select_related('peluquero', 'profesional', 'servicio').order_by('-fecha', '-hora_inicio')
        
        logger.info(f"Reservas encontradas para {request.user.username}: {reservas.count()}")
        
        # Separar reservas por estado
        reservas_pendientes = reservas.filter(estado='pendiente')
        reservas_confirmadas = reservas.filter(estado='confirmado')
        reservas_completadas = reservas.filter(estado='completado')
        reservas_canceladas = reservas.filter(estado='cancelado')
        
        context = {
            'reservas_pendientes': reservas_pendientes,
            'reservas_confirmadas': reservas_confirmadas,
            'reservas_completadas': reservas_completadas,
            'reservas_canceladas': reservas_canceladas,
            'total_reservas': reservas.count(),
        }
        
        return render(request, 'clientes/mis_reservas.html', context)
        
    except Exception as e:
        logger.error(f"Error obteniendo reservas del usuario {request.user.username}: {str(e)}")
        messages.error(request, 'Error al cargar tus reservas.')
        return render(request, 'clientes/mis_reservas.html', {
            'reservas_pendientes': [],
            'reservas_confirmadas': [],
            'reservas_completadas': [],
            'reservas_canceladas': [],
            'total_reservas': 0,
        })

@login_required
def dashboard_cliente(request):
    """Dashboard principal del cliente"""
    query = request.GET.get('q', '')
    
    # Obtener negocios con información adicional
    negocios = Negocio.objects.filter(activo=True)
    if query:
        negocios = negocios.filter(
            models.Q(nombre__icontains=query) |
            models.Q(direccion__icontains=query) |
            models.Q(
                id__in=Matriculacion.objects.filter(
                    estado='aprobada',
                    profesional__nombre_completo__icontains=query
                ).values('negocio_id')
            )
        ).distinct()
    
    negocios_info = []
    for negocio in negocios:
        # Obtener profesionales del negocio
        profesionales = Profesional.objects.filter(
            matriculaciones__negocio=negocio,
            matriculaciones__estado='aprobada'
        ).distinct()
        
        # Calcular calificación promedio
        calificaciones = Calificacion.objects.filter(negocio=negocio)
        calificacion_promedio = calificaciones.aggregate(avg=models.Avg('puntaje'))['avg'] or 0
        calificacion_cantidad = calificaciones.count()
        
        negocios_info.append({
            'negocio': negocio,
            'profesionales': profesionales,
            'calificacion_promedio': round(calificacion_promedio, 1),
            'calificacion_cantidad': calificacion_cantidad,
        })
    
    # Obtener reservas del usuario
    reservas_usuario = Reserva.objects.filter(cliente=request.user).order_by('-creado_en')[:5]
    
    # Obtener calificaciones del usuario
    calificaciones_usuario = Calificacion.objects.filter(cliente=request.user).order_by('-fecha_calificacion')[:5]
    
    # Estadísticas del usuario
    total_reservas = Reserva.objects.filter(cliente=request.user).count()
    reservas_pendientes = Reserva.objects.filter(cliente=request.user, estado='pendiente').count()
    reservas_completadas = Reserva.objects.filter(cliente=request.user, estado='completado').count()
    
    context = {
        'negocios_info': negocios_info,
        'reservas_usuario': reservas_usuario,
        'calificaciones_usuario': calificaciones_usuario,
        'query': query,
        'total_reservas': total_reservas,
        'reservas_pendientes': reservas_pendientes,
        'reservas_completadas': reservas_completadas,
    }
    
    return render(request, 'clientes/dashboard.html', context)

@login_required
def reservar_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, activo=True)
    servicios = negocio.servicios_negocio.select_related('servicio').all()
    profesional_id = request.GET.get('profesional')
    servicio_id = request.GET.get('servicio')
    fecha_preseleccionada = request.GET.get('fecha')
    profesional_preseleccionado = None
    if profesional_id:
        try:
            profesional_preseleccionado = Profesional.objects.get(id=profesional_id)
        except Profesional.DoesNotExist:
            profesional_preseleccionado = None
    initial = {}
    if servicio_id:
        initial['servicio'] = servicio_id
    if request.method == 'POST':
        logger.info(f"POST recibido en reservar_negocio - negocio_id: {negocio_id}")
        form = ReservaNegocioForm(request.POST, negocio=negocio, profesional_preseleccionado=profesional_preseleccionado)
        
        logger.info(f"Formulario creado - válido: {form.is_valid()}")
        if not form.is_valid():
            logger.warning(f"Formulario inválido - errores: {form.errors}")
            logger.warning(f"Datos POST: {request.POST}")
        
        if form.is_valid():
            try:
                # Obtener los datos del formulario
                servicio = form.cleaned_data.get('servicio')
                profesional = form.cleaned_data.get('profesional')
                fecha = form.cleaned_data.get('fecha')
                hora_inicio = form.cleaned_data.get('hora_inicio')
                notas = form.cleaned_data.get('notas', '')
                
                logger.info(f"Datos del formulario - servicio: {servicio}, profesional: {profesional}, fecha: {fecha}, hora_inicio: {hora_inicio}")
                
                # Validar que todos los campos requeridos estén presentes
                if not fecha or not hora_inicio:
                    logger.error("Fecha o hora_inicio faltantes")
                    messages.error(request, 'Fecha y hora son obligatorios.')
                    return render(request, 'clientes/reservar_negocio.html', {
                        'negocio': negocio,
                        'servicios': servicios,
                        'form': form,
                        'profesional_preseleccionado': profesional_preseleccionado,
                        'fecha_preseleccionada': fecha_preseleccionada,
                    })
                
                # Calcular hora_fin usando la duración del servicio
                hora_fin = None
                if servicio and hora_inicio:
                    duracion = servicio.duracion
                    from datetime import datetime, timedelta
                    hora_inicio_dt = datetime.combine(fecha, hora_inicio)
                    hora_fin_dt = hora_inicio_dt + timedelta(minutes=duracion)
                    hora_fin = hora_fin_dt.time()
                    logger.info(f"Hora fin calculada: {hora_fin}")
                
                # Crear la reserva
                reserva = Reserva(
                    cliente=request.user,
                    peluquero=negocio,
                    fecha=fecha,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin or hora_inicio,
                    estado='pendiente'
                )
                
                # Agregar campos opcionales solo si existen
                if profesional:
                    reserva.profesional = profesional
                if servicio:
                    reserva.servicio = servicio
                if notas:
                    reserva.notas = notas
                
                logger.info(f"Intentando guardar reserva con datos: cliente={reserva.cliente.id}, peluquero={reserva.peluquero.id}, profesional={reserva.profesional.id if reserva.profesional else None}, servicio={reserva.servicio.id if reserva.servicio else None}")
                
                reserva.save()
                
                # Crear notificación para el profesional si existe
                if reserva.profesional:
                    from profesionales.models import Notificacion
                    Notificacion.objects.create(
                        profesional=reserva.profesional,
                        tipo='reserva',
                        titulo='Nueva Reserva',
                        mensaje=f'Nueva reserva pendiente para el {reserva.fecha} a las {reserva.hora_inicio} con {reserva.cliente.username}.',
                        url_relacionada='/profesionales/panel/'
                    )
                
                logger.info(f"Reserva creada exitosamente: {reserva.id}")
                messages.success(request, '¡Reserva realizada con éxito!')
                return redirect('clientes:confirmacion_reserva', reserva_id=reserva.id)
                
            except Exception as e:
                logger.error(f"Error guardando reserva: {str(e)}")
                messages.error(request, 'Error al guardar la reserva. Por favor, intenta nuevamente.')
        else:
            logger.error(f"Formulario inválido: {form.errors}")
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    
    # Si no es POST, mostrar formulario normal
    form = ReservaNegocioForm(negocio=negocio, profesional_preseleccionado=profesional_preseleccionado, initial=initial)

    # --- NUEVO: calcular disponibilidad diaria para el mes visible si hay profesional seleccionado ---
    from datetime import date, timedelta
    import calendar
    disponibilidad = {}
    hoy = date.today()
    mes = hoy.month
    anio = hoy.year
    # Si hay fecha preseleccionada, usar ese mes
    if fecha_preseleccionada:
        try:
            partes = fecha_preseleccionada.split('-')
            anio = int(partes[0])
            mes = int(partes[1])
        except Exception:
            pass
    # Calcular primer y último día del mes
    primer_dia = date(anio, mes, 1)
    ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])
    dias_mes = (ultimo_dia - primer_dia).days + 1
    profesional = profesional_preseleccionado
    servicio = None
    if servicio_id:
        try:
            servicio = negocio.servicios_negocio.get(id=servicio_id)
        except Exception:
            servicio = None
    for i in range(dias_mes):
        dia = primer_dia + timedelta(days=i)
        disponible = False
        if profesional and servicio:
            # Verificar si es festivo/domingo
            import holidays
            co_holidays = holidays.CountryHoliday('CO')
            nombre_dia = dia.strftime('%A')
            nombre_dia_es = {
                'Monday': 'lunes',
                'Tuesday': 'martes',
                'Wednesday': 'miercoles',
                'Thursday': 'jueves',
                'Friday': 'viernes',
                'Saturday': 'sabado',
                'Sunday': 'domingo'
            }.get(nombre_dia, nombre_dia)
            es_festivo = dia in co_holidays or nombre_dia_es == 'domingo'
            if not es_festivo:
                from profesionales.models import HorarioProfesional
                horario_prof = HorarioProfesional.objects.filter(profesional=profesional, dia_semana=nombre_dia_es, disponible=True).first()
                if horario_prof:
                    # Verificar si hay al menos un slot disponible
                    inicio = horario_prof.hora_inicio
                    fin = horario_prof.hora_fin
                    duracion = servicio.duracion or 30
                    inicio_minutos = inicio.hour * 60 + inicio.minute
                    fin_minutos = fin.hour * 60 + fin.minute
                    tiempo_actual = inicio_minutos
                    reservas = Reserva.objects.filter(
                        peluquero=negocio,
                        profesional=profesional,
                        fecha=dia,
                        estado__in=['pendiente', 'confirmado']
                    ).values_list('hora_inicio', 'hora_fin')
                    while tiempo_actual + duracion <= fin_minutos:
                        hora_inicio = time(tiempo_actual // 60, tiempo_actual % 60)
                        hora_fin = time((tiempo_actual + duracion) // 60, (tiempo_actual + duracion) % 60)
                        ocupado = False
                        for reserva_inicio, reserva_fin in reservas:
                            if not (hora_fin <= reserva_inicio or hora_inicio >= reserva_fin):
                                ocupado = True
                                break
                        if not ocupado:
                            disponible = True
                            break
                        tiempo_actual += duracion
        disponibilidad[dia.strftime('%Y-%m-%d')] = disponible
    # --- FIN NUEVO ---

    return render(request, 'clientes/reservar_negocio.html', {
        'negocio': negocio,
        'servicios': servicios,
        'form': form,
        'profesional_preseleccionado': profesional_preseleccionado,
        'fecha_preseleccionada': fecha_preseleccionada,
        'disponibilidad': disponibilidad,  # <-- pasar al contexto
    })

@login_required
def notificaciones_cliente(request):
    notificaciones = NotificacionCliente.objects.filter(cliente=request.user).order_by('-fecha_creacion')
    return render(request, 'clientes/notificaciones.html', {'notificaciones': notificaciones})

@require_POST
@login_required
@ratelimit(key='ip', rate='5/m', method=['POST'])
def eliminar_notificacion_cliente(request, notificacion_id):
    try:
        noti = NotificacionCliente.objects.get(id=notificacion_id, cliente=request.user)
        noti.delete()
        return JsonResponse({'ok': True})
    except NotificacionCliente.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrada'}, status=404)

@login_required
def confirmar_reserva(request, reserva_id):
    """
    Vista para confirmar una reserva pendiente
    """
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar permisos
    if request.user.tipo == 'negocio':
        # El negocio puede confirmar reservas de sus negocios
        if not reserva.peluquero.propietario == request.user:
            messages.error(request, 'No tienes permisos para confirmar esta reserva.')
            return redirect('clientes:mis_reservas')
    elif request.user.tipo == 'cliente':
        # El cliente solo puede confirmar sus propias reservas
        if not reserva.cliente == request.user:
            messages.error(request, 'No tienes permisos para confirmar esta reserva.')
            return redirect('clientes:mis_reservas')
    else:
        messages.error(request, 'No tienes permisos para confirmar reservas.')
        return redirect('clientes:mis_reservas')
    
    if request.method == 'POST':
        notas_adicionales = request.POST.get('notas_adicionales', '')
        
        try:
            reserva.confirmar(notas_adicionales)
            messages.success(request, 'Reserva confirmada exitosamente.')
        except ValidationError as e:
            messages.error(request, str(e))
        
        return redirect('clientes:mis_reservas')
    
    context = {
        'reserva': reserva,
        'accion': 'confirmar'
    }
    return render(request, 'clientes/confirmar_reserva.html', context)

@login_required
def cancelar_reserva(request, reserva_id):
    """
    Vista para cancelar una reserva
    """
    logger.info(f"=== INICIO cancelar_reserva ===")
    logger.info(f"Reserva ID: {reserva_id}")
    logger.info(f"Usuario: {request.user.username} ({request.user.tipo})")
    logger.info(f"Método HTTP: {request.method}")
    logger.info(f"POST data: {request.POST}")
    logger.info(f"GET data: {request.GET}")
    
    try:
        reserva = get_object_or_404(Reserva, id=reserva_id)
        logger.info(f"Reserva encontrada: {reserva.id}, estado: {reserva.estado}, cliente: {reserva.cliente.username}")
        
        # Verificar permisos
        if request.user.tipo == 'negocio':
            # El negocio puede cancelar reservas de sus negocios
            if not reserva.peluquero.propietario == request.user:
                logger.warning(f"Usuario {request.user.username} intentó cancelar reserva {reserva_id} sin permisos (negocio)")
                messages.error(request, 'No tienes permisos para cancelar esta reserva.')
                return redirect('clientes:mis_reservas')
        elif request.user.tipo == 'cliente':
            # El cliente solo puede cancelar sus propias reservas
            if not reserva.cliente == request.user:
                logger.warning(f"Usuario {request.user.username} intentó cancelar reserva {reserva_id} sin permisos (cliente)")
                messages.error(request, 'No tienes permisos para cancelar esta reserva.')
                return redirect('clientes:mis_reservas')
        else:
            logger.warning(f"Usuario {request.user.username} de tipo {request.user.tipo} intentó cancelar reserva {reserva_id}")
            messages.error(request, 'No tienes permisos para cancelar reservas.')
            return redirect('clientes:mis_reservas')
        
        if request.method == 'POST':
            motivo = request.POST.get('motivo', '')
            cancelado_por = request.user.tipo
            
            logger.info(f"Cancelando reserva {reserva_id} con motivo: '{motivo}', cancelado por: {cancelado_por}")
            
            try:
                reserva.cancelar(motivo, cancelado_por)
                logger.info(f"Reserva {reserva_id} cancelada exitosamente")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Reserva cancelada exitosamente.'
                    })
                else:
                    messages.success(request, 'Reserva cancelada exitosamente.')
                    return redirect('clientes:mis_reservas')
                    
            except ValidationError as e:
                error_msg = str(e)
                logger.error(f"Error de validación al cancelar reserva {reserva_id}: {error_msg}")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    })
                else:
                    messages.error(request, error_msg)
                    context = {
                        'reserva': reserva,
                        'accion': 'cancelar'
                    }
                    return render(request, 'clientes/cancelar_reserva.html', context)
            except Exception as e:
                logger.error(f"Error inesperado al cancelar reserva {reserva_id}: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'Error al cancelar la reserva: {str(e)}'
                    })
                else:
                    messages.error(request, f'Error al cancelar la reserva: {str(e)}')
        
        context = {
            'reserva': reserva,
            'accion': 'cancelar'
        }
        logger.info(f"Renderizando template para reserva {reserva_id}")
        return render(request, 'clientes/cancelar_reserva.html', context)
        
    except Exception as e:
        logger.error(f"Error general en cancelar_reserva para reserva {reserva_id}: {str(e)}")
        messages.error(request, 'Error al procesar la solicitud de cancelación.')
        return redirect('clientes:mis_reservas')

@login_required
def completar_reserva(request, reserva_id):
    """
    Vista para marcar una reserva como completada
    """
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar permisos - solo negocios pueden completar reservas
    if request.user.tipo != 'negocio':
        messages.error(request, 'Solo los negocios pueden marcar reservas como completadas.')
        return redirect('clientes:mis_reservas')
    
    if not reserva.peluquero.propietario == request.user:
        messages.error(request, 'No tienes permisos para completar esta reserva.')
        return redirect('clientes:mis_reservas')
    
    if request.method == 'POST':
        notas_adicionales = request.POST.get('notas_adicionales', '')
        
        try:
            reserva.completar(notas_adicionales)
            messages.success(request, 'Reserva marcada como completada exitosamente.')
        except ValidationError as e:
            messages.error(request, str(e))
        
        return redirect('clientes:mis_reservas')
    
    context = {
        'reserva': reserva,
        'accion': 'completar'
    }
    return render(request, 'clientes/completar_reserva.html', context)

@login_required
def reagendar_reserva(request, reserva_id):
    """
    Vista para reagendar una reserva
    """
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar permisos
    if request.user.tipo == 'negocio':
        # El negocio puede reagendar reservas de sus negocios
        if not reserva.peluquero.propietario == request.user:
            messages.error(request, 'No tienes permisos para reagendar esta reserva.')
            return redirect('clientes:mis_reservas')
    elif request.user.tipo == 'cliente':
        # El cliente solo puede reagendar sus propias reservas
        if not reserva.cliente == request.user:
            messages.error(request, 'No tienes permisos para reagendar esta reserva.')
            return redirect('clientes:mis_reservas')
    else:
        messages.error(request, 'No tienes permisos para reagendar reservas.')
        return redirect('clientes:mis_reservas')
    
    if request.method == 'POST':
        nueva_fecha = request.POST.get('nueva_fecha')
        nueva_hora_inicio = request.POST.get('nueva_hora_inicio')
        nueva_hora_fin = request.POST.get('nueva_hora_fin')
        motivo = request.POST.get('motivo', '')
        
        try:
            from datetime import datetime
            nueva_fecha = datetime.strptime(nueva_fecha, '%Y-%m-%d').date()
            nueva_hora_inicio = datetime.strptime(nueva_hora_inicio, '%H:%M').time()
            nueva_hora_fin = datetime.strptime(nueva_hora_fin, '%H:%M').time()
            
            reserva.reagendar(nueva_fecha, nueva_hora_inicio, nueva_hora_fin, motivo)
            messages.success(request, 'Reserva reagendada exitosamente.')
        except (ValidationError, ValueError) as e:
            messages.error(request, f'Error al reagendar: {str(e)}')
        
        return redirect('clientes:mis_reservas')
    
    context = {
        'reserva': reserva,
        'accion': 'reagendar'
    }
    return render(request, 'clientes/reagendar_reserva.html', context)

@login_required
def crear_calificacion(request, negocio_id, profesional_id):
    """Vista para crear una calificación"""
    negocio = get_object_or_404(Negocio, id=negocio_id)
    profesional = None
    if int(profesional_id) != 0:
        profesional = get_object_or_404(Profesional, id=profesional_id)
    # Si es comentario solo al negocio, no exigir reserva previa con profesional
    if profesional:
        reservas_completadas = Reserva.objects.filter(
            cliente=request.user,
            peluquero=negocio,
            profesional=profesional,
            estado='completado'
        )
        if not reservas_completadas.exists():
            messages.error(request, 'Solo puedes calificar a profesionales con los que hayas completado una reserva.')
            return redirect('negocios:detalle_negocio', negocio_id=negocio_id)
        # Verificar que no haya calificado ya a ese profesional en ese negocio
        calificacion_existente = Calificacion.objects.filter(
            cliente=request.user,
            negocio=negocio,
            profesional=profesional
        ).first()
        if calificacion_existente:
            messages.info(request, 'Ya has calificado a este profesional en este negocio.')
            return redirect('negocios:detalle_negocio', negocio_id=negocio_id)
    else:
        # Solo negocio: verificar que no haya calificado ya solo al negocio
        calificacion_existente = Calificacion.objects.filter(
            cliente=request.user,
            negocio=negocio,
            profesional__isnull=True
        ).first()
        if calificacion_existente:
            messages.info(request, 'Ya has dejado un comentario para este negocio.')
            return redirect('clientes:detalle_peluquero', pk=negocio_id)
    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.cliente = request.user
            calificacion.negocio = negocio
            calificacion.profesional = profesional
            calificacion.save()
            # Notificaciones solo si hay profesional
            if profesional:
                Notificacion.objects.create(
                    destinatario=profesional.usuario,
                    tipo='calificacion',
                    titulo=f'Nueva calificación de {request.user.username}',
                    mensaje=f'Has recibido una calificación de {calificacion.puntaje}/5 estrellas en {negocio.nombre}',
                    url_relacionada=f'/negocios/detalle-negocio/{negocio.id}/',
                )
                if negocio.usuario != profesional.usuario:
                    Notificacion.objects.create(
                        destinatario=negocio.usuario,
                        tipo='calificacion',
                        titulo=f'Nueva calificación en {negocio.nombre}',
                        mensaje=f'{request.user.username} calificó a {profesional.nombre_completo} con {calificacion.puntaje}/5 estrellas',
                        url_relacionada=f'/negocios/detalle-negocio/{negocio.id}/',
                    )
            messages.success(request, '¡Gracias por tu comentario!')
            return redirect('clientes:detalle_peluquero', pk=negocio_id)
    else:
        form = CalificacionForm()
    context = {
        'form': form,
        'negocio': negocio,
        'profesional': profesional,
    }
    return render(request, 'clientes/crear_calificacion.html', context)

@login_required
def editar_calificacion(request, calificacion_id):
    """Vista para editar una calificación existente"""
    calificacion = get_object_or_404(Calificacion, id=calificacion_id, cliente=request.user)
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=calificacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Calificación actualizada correctamente.')
            return redirect('negocios:detalle_negocio', negocio_id=calificacion.negocio.id)
    else:
        form = CalificacionForm(instance=calificacion)
    
    context = {
        'form': form,
        'calificacion': calificacion,
        'negocio': calificacion.negocio,
        'profesional': calificacion.profesional,
    }
    return render(request, 'clientes/editar_calificacion.html', context)

@login_required
def eliminar_calificacion(request, calificacion_id):
    """Vista para eliminar una calificación"""
    calificacion = get_object_or_404(Calificacion, id=calificacion_id, cliente=request.user)
    
    if request.method == 'POST':
        negocio_id = calificacion.negocio.id
        calificacion.delete()
        messages.success(request, 'Calificación eliminada correctamente.')
        return redirect('negocios:detalle_negocio', negocio_id=negocio_id)
    
    context = {
        'calificacion': calificacion,
    }
    return render(request, 'clientes/eliminar_calificacion.html', context)

def proximamente_app(request):
    return render(request, 'clientes/proximamente_app.html')

def autocompletar_servicios(request):
    """Endpoint para autocompletar servicios según los negocios activos y el texto ingresado, filtrando por ubicación si se provee lat/lon."""
    q = request.GET.get('q', '').strip()
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    radio_metros = 500
    negocios_qs = Negocio.objects.filter(activo=True, latitud__isnull=False, longitud__isnull=False)
    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
            def haversine(lat1, lon1, lat2, lon2):
                # Radio de la tierra en km
                R = 6371.0
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                return R * c * 1000  # metros
            negocios_qs = [n for n in negocios_qs if haversine(lat, lon, n.latitud, n.longitud) <= radio_metros]
        except Exception:
            negocios_qs = []
    servicios_qs = Servicio.objects.filter(servicionegocio__negocio__in=negocios_qs).distinct()
    if q:
        servicios_qs = servicios_qs.filter(nombre__icontains=q)
    servicios = list(servicios_qs.values_list('nombre', flat=True))
    return JsonResponse({'servicios': servicios})

@require_GET
def negocios_cercanos(request):
    from math import radians, cos, sin, asin, sqrt
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    if not lat or not lon:
        return JsonResponse({'negocios': []})
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return JsonResponse({'negocios': []})
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return R * c * 1000  # metros
    negocios = []
    for n in Negocio.objects.filter(activo=True, latitud__isnull=False, longitud__isnull=False):
        distancia = haversine(lat, lon, n.latitud, n.longitud)
        negocios.append({
            'id': n.id,
            'nombre': n.nombre,
            'direccion': n.direccion,
            'latitud': n.latitud,
            'longitud': n.longitud,
            'distancia': distancia,
            'servicios': list(n.servicios_negocio.values_list('servicio__nombre', flat=True)),
        })
    negocios = sorted(negocios, key=lambda x: x['distancia'])[:5]
    return JsonResponse({'negocios': negocios})

@require_GET
def autocompletar_negocios(request):
    try:
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'sugerencias': []})
        
        # Buscar negocios por nombre
        negocios = Negocio.objects.filter(
            Q(nombre__icontains=query) | 
            Q(direccion__icontains=query),
            activo=True
        )[:10]
        
        def haversine(lat1, lon1, lat2, lon2):
            # Radio de la tierra en km
            R = 6371
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c
        
        sugerencias = []
        for negocio in negocios:
            sugerencias.append({
                'id': negocio.id,
                'nombre': negocio.nombre,
                'direccion': negocio.direccion,
                'ciudad': negocio.ciudad,
                'barrio': negocio.barrio
            })
        
        return JsonResponse({'sugerencias': sugerencias})
    except Exception as e:
        logger.error(f"Error en autocompletar negocios: {str(e)}")
        return JsonResponse({'sugerencias': []})

def buscar_negocios(request):
    """
    Búsqueda combinada de negocios:
    - Por ubicación (lat/lon con radio de 500m si solo ubicación)
    - Por servicio
    - Por nombre de negocio
    - Cualquier combinación de los anteriores
    """
    try:
        # Parámetros de búsqueda
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        radio = request.GET.get('radio', '500')  # Radio por defecto 500m
        servicio = request.GET.get('servicio', '').strip()
        negocio_nombre = request.GET.get('negocio', '').strip()
        
        # Query base
        queryset = Negocio.objects.filter(activo=True)
        
        # Si solo hay ubicación, buscar por radio
        if lat and lon and not servicio and not negocio_nombre:
            try:
                lat = float(lat)
                lon = float(lon)
                radio_km = float(radio) / 1000  # Convertir metros a km
                
                def haversine(lat1, lon1, lat2, lon2):
                    R = 6371  # Radio de la tierra en km
                    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    return R * c
                
                # Filtrar por distancia
                negocios_cercanos = []
                for neg in queryset:
                    if neg.latitud and neg.longitud:
                        distancia = haversine(lat, lon, neg.latitud, neg.longitud)
                        if distancia <= radio_km:
                            neg.distancia = distancia
                            negocios_cercanos.append(neg)
                
                # Ordenar por distancia
                negocios_cercanos.sort(key=lambda x: x.distancia)
                queryset = negocios_cercanos
                
            except (ValueError, TypeError) as e:
                logger.error(f"Error procesando coordenadas: {str(e)}")
                queryset = Negocio.objects.none()
        
        # Filtrar por servicio si se especifica
        if servicio:
            queryset = queryset.filter(
                servicios__servicio__nombre__icontains=servicio
            ).distinct()
        
        # Filtrar por nombre de negocio si se especifica
        if negocio_nombre:
            queryset = queryset.filter(
                Q(nombre__icontains=negocio_nombre) |
                Q(direccion__icontains=negocio_nombre)
            )
        
        # Filtrar por ubicación (ciudad/barrio) si se especifica sin lat/lon
        if not lat and not lon:
            ubicacion = request.GET.get('ubicacion', '').strip()
            if ubicacion:
                queryset = queryset.filter(
                    Q(ciudad__icontains=ubicacion) |
                    Q(barrio__icontains=ubicacion) |
                    Q(direccion__icontains=ubicacion)
                )
        
        # Limitar resultados
        queryset = queryset[:50]
        
        # Preparar contexto
        context = {
            'negocios': queryset,
            'total_resultados': len(queryset),
            'parametros_busqueda': {
                'lat': lat,
                'lon': lon,
                'radio': radio,
                'servicio': servicio,
                'negocio': negocio_nombre,
                'ubicacion': request.GET.get('ubicacion', '')
            }
        }
        
        # Preparar datos para el mapa si hay resultados
        if queryset:
            negocios_mapa = []
            for negocio in queryset:
                profesionales_aceptados = [m.profesional for m in Matriculacion.objects.filter(negocio=negocio, estado='aprobada')]
                negocio_mapa = {
                    'id': negocio.id,
                    'nombre': negocio.nombre,
                    'direccion': negocio.direccion,
                    'latitud': negocio.latitud,
                    'longitud': negocio.longitud,
                    'url': f"/clientes/detalle_peluquero/{negocio.id}/",
                    'logo_url': negocio.logo.url if negocio.logo else '',
                    'profesionales': profesionales_aceptados,
                }
                if hasattr(negocio, 'distancia'):
                    negocio_mapa['distancia'] = round(negocio.distancia * 1000)  # Convertir a metros
                negocios_mapa.append(negocio_mapa)
            context['negocios_mapa'] = negocios_mapa
        
        return render(request, 'clientes/lista_negocios.html', context)
        
    except Exception as e:
        logger.error(f"Error en búsqueda de negocios: {str(e)}")
        return render(request, 'clientes/lista_negocios.html', {
            'negocios': [],
            'total_resultados': 0,
            'error': 'Error en la búsqueda'
        })

@require_GET
def disponibilidad_dias(request):
    from datetime import date, timedelta
    import calendar
    import holidays
    from profesionales.models import HorarioProfesional
    profesional_id = request.GET.get('profesional_id')
    servicio_id = request.GET.get('servicio_id')
    mes = int(request.GET.get('mes'))
    anio = int(request.GET.get('anio'))
    negocio_id = request.GET.get('negocio_id')
    disponibilidad = {}
    if not (profesional_id and servicio_id and negocio_id):
        return JsonResponse({'disponibilidad': disponibilidad})
    try:
        negocio = Negocio.objects.get(id=negocio_id)
        profesional = Profesional.objects.get(id=profesional_id)
        servicio = negocio.servicios_negocio.get(id=servicio_id)
    except Exception:
        return JsonResponse({'disponibilidad': disponibilidad})
    primer_dia = date(anio, mes, 1)
    ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])
    dias_mes = (ultimo_dia - primer_dia).days + 1
    for i in range(dias_mes):
        dia = primer_dia + timedelta(days=i)
        disponible = False
        # Verificar si es festivo/domingo
        co_holidays = holidays.CountryHoliday('CO')
        nombre_dia = dia.strftime('%A')
        nombre_dia_es = {
            'Monday': 'lunes',
            'Tuesday': 'martes',
            'Wednesday': 'miercoles',
            'Thursday': 'jueves',
            'Friday': 'viernes',
            'Saturday': 'sabado',
            'Sunday': 'domingo'
        }.get(nombre_dia, nombre_dia)
        es_festivo = dia in co_holidays or nombre_dia_es == 'domingo'
        if not es_festivo:
            horario_prof = HorarioProfesional.objects.filter(profesional=profesional, dia_semana=nombre_dia_es, disponible=True).first()
            if horario_prof:
                # Verificar si hay al menos un slot disponible
                inicio = horario_prof.hora_inicio
                fin = horario_prof.hora_fin
                duracion = servicio.duracion or 30
                inicio_minutos = inicio.hour * 60 + inicio.minute
                fin_minutos = fin.hour * 60 + fin.minute
                tiempo_actual = inicio_minutos
                reservas = Reserva.objects.filter(
                    peluquero=negocio,
                    profesional=profesional,
                    fecha=dia,
                    estado__in=['pendiente', 'confirmado']
                ).values_list('hora_inicio', 'hora_fin')
                while tiempo_actual + duracion <= fin_minutos:
                    hora_inicio = time(tiempo_actual // 60, tiempo_actual % 60)
                    hora_fin = time((tiempo_actual + duracion) // 60, (tiempo_actual + duracion) % 60)
                    ocupado = False
                    for reserva_inicio, reserva_fin in reservas:
                        if not (hora_fin <= reserva_inicio or hora_inicio >= reserva_fin):
                            ocupado = True
                            break
                    if not ocupado:
                        disponible = True
                        break
                    tiempo_actual += duracion
        disponibilidad[dia.strftime('%Y-%m-%d')] = disponible
    return JsonResponse({'disponibilidad': disponibilidad})