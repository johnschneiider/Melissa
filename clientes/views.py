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
from .models import Reserva
from .forms import ReservaForm, ReservaNegocioForm
import json
import holidays
import logging
from django.core.exceptions import ValidationError
from django.utils.html import escape
import re
from django.db.models import Q
from profesionales.models import Notificacion, Profesional, Matriculacion

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
                    reserva = form.save(commit=False)
                    reserva.cliente = request.user
                    reserva.negocio = negocio
                    
                    # Calcular hora_fin basado en la duración
                    hora_inicio = form.cleaned_data['hora_inicio']
                    servicio = form.cleaned_data.get('servicio')
                    duracion = servicio.duracion if servicio else 30
                    
                    # Crear datetime aware para hora_fin
                    hora_fin = (timezone.make_aware(
                        datetime.combine(form.cleaned_data['fecha'], hora_inicio)
                        + timedelta(minutes=duracion)).time())
                    
                    reserva.hora_fin = hora_fin
                    reserva.save()
                    
                    # Notificar al negocio
                    Notificacion.objects.create(
                        profesional=None,
                        tipo='reserva',
                        titulo='Nueva reserva recibida',
                        mensaje=f'Has recibido una nueva reserva de {reserva.cliente.username} para el servicio {reserva.servicio}.',
                        url_relacionada='' # Puedes poner la url de la reserva
                    )
                    
                    logger.info(f"Reserva creada por {request.user.username} para {negocio.nombre}")
                    messages.success(request, '¡Reserva realizada con éxito!')
                    return redirect('clientes:confirmacion_reserva', reserva_id=reserva.id)
                except Exception as e:
                    logger.error(f"Error creando reserva: {str(e)}")
                    messages.error(request, 'Error al crear la reserva. Inténtalo de nuevo.')
            else:
                logger.warning(f"Formulario inválido al reservar: {form.errors}")
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
        duracion = None
        if servicio_negocio_id:
            try:
                servicio_negocio = ServicioNegocio.objects.get(id=servicio_negocio_id, negocio=negocio)
                duracion = servicio_negocio.duracion
            except ServicioNegocio.DoesNotExist:
                pass
        
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
            'Monday': 'Lunes',
            'Tuesday': 'Martes',
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }.get(nombre_dia, nombre_dia)
        
        es_festivo = fecha_obj in co_holidays or nombre_dia_es == 'Domingo'
        
        if es_festivo:
            return JsonResponse({'disponibles': [], 'festivo': True})
        
        # Obtener horario del negocio para este día
        horario = negocio.horario_atencion.get(nombre_dia_es, {}) if negocio.horario_atencion else {}
        turnos = horario.get('turnos', []) if horario else []
        
        # Obtener reservas existentes para este día
        reservas = Reserva.objects.filter(
            peluquero=negocio,
            fecha=fecha_obj,
            estado__in=['pendiente', 'confirmado']
        ).values_list('hora_inicio', 'hora_fin')
        
        # Calcular horarios disponibles
        horarios_disponibles = []
        for turno in turnos:
            if turno.get('disponible', True):
                try:
                    inicio = datetime.strptime(turno['inicio'], '%H:%M').time()
                    fin = datetime.strptime(turno['fin'], '%H:%M').time()
                    duracion_turno = duracion or int(turno.get('duracion', 30))
                    
                    # Generar intervalos
                    inicio_minutos = inicio.hour * 60 + inicio.minute
                    fin_minutos = fin.hour * 60 + fin.minute
                    tiempo_actual = inicio_minutos
                    
                    while tiempo_actual + duracion_turno <= fin_minutos:
                        hora_inicio = time(tiempo_actual // 60, tiempo_actual % 60)
                        hora_fin = time((tiempo_actual + duracion_turno) // 60, (tiempo_actual + duracion_turno) % 60)
                        
                        # Verificar si este intervalo está disponible
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
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error procesando turno en horarios_disponibles: {str(e)}")
                    continue
        
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

def dashboard_cliente(request):
    """Dashboard principal para clientes - Marketplace estilo Airbnb"""
    negocios = Negocio.objects.filter(activo=True)
    query = request.GET.get('q', '')
    if query:
        negocios = negocios.filter(
            Q(nombre__icontains=query) |
            Q(peluqueros__nombre__icontains=query) |
            Q(direccion__icontains=query)
        ).distinct()

    # Calificaciones para cada negocio
    negocios_info = []
    for negocio in negocios:
        profesionales_activos = Profesional.objects.filter(
            matriculaciones__negocio=negocio,
            matriculaciones__estado='aprobada',
            disponible=True
        )
        calificaciones = Reserva.objects.filter(profesional__in=profesionales_activos).count()
        if calificaciones > 0:
            promedio = round(sum([
                r.servicio.puntaje for r in Reserva.objects.filter(profesional__in=profesionales_activos) if r.servicio and hasattr(r.servicio, 'puntaje')
            ]) / calificaciones, 1)
        else:
            promedio = 5.0
        negocios_info.append({
            'negocio': negocio,
            'profesionales_activos': profesionales_activos,
            'calificaciones': calificaciones,
            'promedio': promedio,
        })

    reservas_usuario = None
    total_reservas = 0
    reservas_pendientes = 0
    reservas_completadas = 0
    if request.user.is_authenticated:
        reservas_usuario = Reserva.objects.filter(cliente=request.user).order_by('-fecha', '-hora_inicio')
        total_reservas = reservas_usuario.count()
        reservas_pendientes = reservas_usuario.filter(estado='pendiente').count()
        reservas_completadas = reservas_usuario.filter(estado='completado').count()

    context = {
        'negocios_info': negocios_info,
        'reservas_usuario': reservas_usuario[:5] if reservas_usuario else [],
        'total_reservas': total_reservas,
        'reservas_pendientes': reservas_pendientes,
        'reservas_completadas': reservas_completadas,
        'query': query,
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
        form = ReservaNegocioForm(request.POST, negocio=negocio, profesional_preseleccionado=profesional_preseleccionado)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.cliente = request.user
            # Calcular hora_fin usando la duración del servicio
            if reserva.servicio and reserva.hora_inicio:
                duracion = reserva.servicio.duracion
                from datetime import datetime, timedelta
                hora_inicio_dt = datetime.combine(reserva.fecha, reserva.hora_inicio)
                hora_fin_dt = hora_inicio_dt + timedelta(minutes=duracion)
                reserva.hora_fin = hora_fin_dt.time()
            reserva.save()
            messages.success(request, '¡Reserva realizada con éxito!')
            return redirect('clientes:confirmacion_reserva', reserva_id=reserva.id)
    else:
        form = ReservaNegocioForm(negocio=negocio, profesional_preseleccionado=profesional_preseleccionado)
    return render(request, 'clientes/reservar_negocio.html', {
        'negocio': negocio,
        'servicios': servicios,
        'form': form,
        'profesional_preseleccionado': profesional_preseleccionado,
    })