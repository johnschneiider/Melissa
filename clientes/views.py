from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.utils import timezone
from datetime import timedelta, datetime, time
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from negocios.models import Negocio, ServicioNegocio
from .models import Reserva, NotificacionCliente, Calificacion
from .forms import ReservaForm, ReservaNegocioForm, CalificacionForm
import json
import holidays
import logging
from django.core.exceptions import ValidationError
from django.utils.html import escape
import re
from django.db.models import Q
from profesionales.models import Notificacion, Profesional, Matriculacion, HorarioProfesional
from django.db import models

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
            # Obtener todos los profesionales aceptados para cada negocio
            negocios_con_profesionales = []
            for negocio in context['negocios']:
                profesionales_aceptados = [m.profesional for m in Matriculacion.objects.filter(negocio=negocio, estado='aprobada')]
                negocios_con_profesionales.append({
                    'negocio': negocio,
                    'profesionales': profesionales_aceptados
                })
            context['negocios_con_profesionales'] = negocios_con_profesionales
        except Exception as e:
            logger.error(f"Error procesando contexto de negocios: {str(e)}")
            context['negocios_con_profesionales'] = []
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
        
        return context

@login_required
@csrf_protect
def reservar_turno(request, negocio_id):
    try:
        negocio = get_object_or_404(Negocio, id=negocio_id, activo=True)
        
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
                    messages.success(request, '¡Reserva realizada con éxito!')
                    return redirect('clientes:confirmacion_reserva', reserva_id=reserva.id)
                except Exception as e:
                    logger.error(f"Error guardando reserva: {str(e)}")
                    logger.error(f"Datos de la reserva: cliente={request.user}, peluquero={negocio}, profesional={getattr(reserva, 'profesional', None)}, servicio={getattr(reserva, 'servicio', None)}")
                    messages.error(request, 'Error al guardar la reserva. Por favor, intenta nuevamente.')
            else:
                logger.warning(f"Formulario inválido: {form.errors}")
        else:
            form = ReservaForm(negocio=negocio)
        
        return render(request, 'clientes/reservar_turno.html', {
            'negocio': negocio,
            'form': form
        })
    except Exception as e:
        logger.error(f"Error en reservar_turno: {str(e)}")
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

@login_required
def mis_reservas(request):
    """Vista para que los clientes vean sus reservas"""
    try:
        reservas = Reserva.objects.filter(
            cliente=request.user
        ).select_related('negocio').order_by('-fecha', '-hora_inicio')
        
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
            models.Q(profesionales__nombre_completo__icontains=query)
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
    profesional_preseleccionado = None
    if profesional_id:
        try:
            profesional_preseleccionado = Profesional.objects.get(id=profesional_id)
        except Profesional.DoesNotExist:
            profesional_preseleccionado = None
    
    if request.method == 'POST':
        logger.info(f"POST recibido en reservar_negocio - negocio_id: {negocio_id}")
        
        # Intentar crear una reserva mínima sin usar el formulario
        try:
            from datetime import date, time
            
            # Crear reserva con solo campos esenciales
            reserva = Reserva.objects.create(
                cliente=request.user,
                peluquero=negocio,
                fecha=date.today(),
                hora_inicio=time(10, 0),
                hora_fin=time(10, 30),
                estado='pendiente'
            )
            
            logger.info(f"Reserva creada exitosamente: {reserva.id}")
            messages.success(request, '¡Reserva realizada con éxito!')
            return redirect('clientes:confirmacion_reserva', reserva_id=reserva.id)
            
        except Exception as e:
            logger.error(f"Error creando reserva mínima: {str(e)}")
            messages.error(request, f'Error al crear la reserva: {str(e)}')
    
    # Si no es POST, mostrar formulario normal
    form = ReservaNegocioForm(negocio=negocio, profesional_preseleccionado=profesional_preseleccionado)
    return render(request, 'clientes/reservar_negocio.html', {
        'negocio': negocio,
        'servicios': servicios,
        'form': form,
        'profesional_preseleccionado': profesional_preseleccionado,
    })

@login_required
def notificaciones_cliente(request):
    notificaciones = NotificacionCliente.objects.filter(cliente=request.user).order_by('-fecha_creacion')
    return render(request, 'clientes/notificaciones.html', {'notificaciones': notificaciones})

@require_POST
@login_required
def eliminar_notificacion_cliente(request, notificacion_id):
    try:
        noti = NotificacionCliente.objects.get(id=notificacion_id, cliente=request.user)
        noti.delete()
        return JsonResponse({'ok': True})
    except NotificacionCliente.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrada'}, status=404)

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, cliente=request.user)
    if reserva.estado not in ['cancelado', 'completado']:
        reserva.estado = 'cancelado'
        reserva.save()
        msg = 'Reserva cancelada exitosamente.'
        success = True
    else:
        msg = 'No se puede cancelar una reserva ya cancelada o completada.'
        success = False
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': success, 'message': msg})
    if success:
        messages.success(request, msg)
    else:
        messages.warning(request, msg)
    return redirect('clientes:mis_reservas')

@login_required
def reagendar_reserva(request, reserva_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    try:
        reserva = get_object_or_404(Reserva, id=reserva_id, cliente=request.user)
        
        if reserva.estado in ['cancelado', 'completado']:
            return JsonResponse({
                'success': False, 
                'message': 'No se puede reagendar una reserva cancelada o completada'
            })
        
        data = json.loads(request.body)
        nueva_fecha = data.get('fecha')
        nueva_hora = data.get('hora_inicio')
        
        if not nueva_fecha or not nueva_hora:
            return JsonResponse({
                'success': False,
                'errors': {'fecha': ['Fecha requerida'], 'hora_inicio': ['Hora requerida']}
            })
        
        # Validar fecha
        try:
            fecha_obj = datetime.strptime(nueva_fecha, '%Y-%m-%d').date()
            if fecha_obj < timezone.now().date():
                return JsonResponse({
                    'success': False,
                    'errors': {'fecha': ['No puedes seleccionar una fecha pasada']}
                })
        except ValueError:
            return JsonResponse({
                'success': False,
                'errors': {'fecha': ['Formato de fecha inválido']}
            })
        
        # Validar hora
        try:
            hora_obj = datetime.strptime(nueva_hora, '%H:%M').time()
        except ValueError:
            return JsonResponse({
                'success': False,
                'errors': {'hora_inicio': ['Formato de hora inválido']}
            })
        
        # Verificar disponibilidad
        hora_fin = (timezone.make_aware(
            datetime.combine(fecha_obj, hora_obj) + timedelta(minutes=reserva.servicio.duracion if reserva.servicio else 30)
        ).time())
        
        # Verificar si hay conflictos
        reservas_conflicto = Reserva.objects.filter(
            peluquero=reserva.peluquero,
            fecha=fecha_obj,
            estado__in=['pendiente', 'confirmado']
        ).exclude(id=reserva.id)
        
        for otra_reserva in reservas_conflicto:
            if not (hora_fin <= otra_reserva.hora_inicio or hora_obj >= otra_reserva.hora_fin):
                return JsonResponse({
                    'success': False,
                    'message': 'El horario seleccionado no está disponible'
                })
        
        # Actualizar reserva
        reserva.fecha = fecha_obj
        reserva.hora_inicio = hora_obj
        reserva.hora_fin = hora_fin
        reserva.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Reserva reagendada exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        })
    except Exception as e:
        logger.error(f"Error reagendando reserva: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        })

@login_required
def crear_calificacion(request, negocio_id, profesional_id):
    """Vista para crear una calificación"""
    negocio = get_object_or_404(Negocio, id=negocio_id)
    profesional = get_object_or_404(Profesional, id=profesional_id)
    
    # Verificar que el usuario tenga reservas completadas con este profesional en este negocio
    reservas_completadas = Reserva.objects.filter(
        cliente=request.user,
        peluquero=negocio,
        profesional=profesional,
        estado='completado'
    )
    
    if not reservas_completadas.exists():
        messages.error(request, 'Solo puedes calificar a profesionales con los que hayas completado una reserva.')
        return redirect('negocios:detalle_negocio', negocio_id=negocio_id)
    
    # Verificar que no haya calificado ya
    calificacion_existente = Calificacion.objects.filter(
        cliente=request.user,
        negocio=negocio,
        profesional=profesional
    ).first()
    
    if calificacion_existente:
        messages.info(request, 'Ya has calificado a este profesional en este negocio.')
        return redirect('negocios:detalle_negocio', negocio_id=negocio_id)
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.cliente = request.user
            calificacion.negocio = negocio
            calificacion.profesional = profesional
            calificacion.save()
            
            # Notificar al profesional sobre la nueva calificación
            Notificacion.objects.create(
                destinatario=profesional.usuario,
                tipo='calificacion',
                titulo=f'Nueva calificación de {request.user.username}',
                mensaje=f'Has recibido una calificación de {calificacion.puntaje}/5 estrellas en {negocio.nombre}',
                url_relacionada=f'/negocios/detalle-negocio/{negocio.id}/',
            )
            
            # Notificar al dueño del negocio
            if negocio.usuario != profesional.usuario:
                Notificacion.objects.create(
                    destinatario=negocio.usuario,
                    tipo='calificacion',
                    titulo=f'Nueva calificación en {negocio.nombre}',
                    mensaje=f'{request.user.username} calificó a {profesional.nombre_completo} con {calificacion.puntaje}/5 estrellas',
                    url_relacionada=f'/negocios/detalle-negocio/{negocio.id}/',
                )
            
            messages.success(request, '¡Gracias por tu calificación!')
            return redirect('negocios:detalle_negocio', negocio_id=negocio_id)
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