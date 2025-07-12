from .forms import NegocioForm, ImagenNegocioForm
from django.contrib.auth.decorators import login_required
from .models import Negocio, MetricaNegocio, ReporteMensual, ImagenNegocio, Servicio, ServicioNegocio
from clientes.models import Calificacion
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timedelta
from django.http import JsonResponse
import holidays
import json
from datetime import datetime, timedelta, time
import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.html import escape
import re
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Max, Q
import numpy as np
from profesionales.models import Matriculacion, Profesional, SolicitudAusencia
from profesionales.models import Notificacion
from negocios.models import ImagenNegocio as ImagenGaleria
from django.db import models
from django.forms import ModelForm
from django.forms import modelformset_factory
from .models import NotificacionNegocio
from negocios.models import DiaDescanso
from datetime import date

logger = logging.getLogger(__name__)

def sanitize_input(text):
    """Sanitizar entrada de texto para prevenir XSS"""
    if text:
        # Remover caracteres peligrosos
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<.*?>', '', text)
        return escape(text.strip())
    return text

@login_required
def crear_negocio(request):
    print('[DEBUG SERVER] POST recibido:', request.method, request.POST)
    if request.method == 'POST':
        print('[DEBUG SERVER] Valor recibido de dirección:', request.POST.get('direccion'))
        # Verificar que el usuario sea de tipo negocio
        if not hasattr(request.user, 'tipo') or request.user.tipo != 'negocio':
            messages.error(request, 'Solo usuarios de tipo negocio pueden crear negocios.')
            return redirect('inicio')
        
        form = NegocioForm(request.POST, request.FILES)
        if form.is_valid():
            print('[DEBUG SERVER] Formulario válido. Guardando negocio...')
            try:
                negocio = form.save(commit=False)
                negocio.propietario = request.user
                negocio.activo = True
                negocio.save()
                from .models import Servicio, ServicioNegocio
                for servicio in Servicio.objects.all():
                    ServicioNegocio.objects.get_or_create(negocio=negocio, servicio=servicio)
                logger.info(f"Negocio '{negocio.nombre}' creado por {request.user.username}")
                messages.success(request, f'¡Felicidades! Tu negocio "{negocio.nombre}" ha sido creado exitosamente.')
                # Redirigir a la lista de negocios
                return redirect('negocios:mis_negocios')
            except Exception as e:
                logger.error(f"Error al crear negocio: {e}")
                messages.error(request, 'Hubo un error al crear tu negocio. Por favor, intenta nuevamente.')
        else:
            print('[DEBUG SERVER] Formulario inválido:', form.errors)
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = NegocioForm()
    return render(request, 'negocios/crear_negocio.html', {'form': form})

@login_required
@require_GET
def mis_negocios(request):
    try:
        negocios_activos = request.user.negocios.filter(activo=True)
        negocios_eliminados = request.user.negocios.filter(activo=False)
        tiene_eliminados = negocios_eliminados.exists()

        return render(request, 'negocios/mis_negocios.html', {
            'negocios': negocios_activos,
            'negocios_eliminados': negocios_eliminados,
            'tiene_eliminados': tiene_eliminados,
        })
    except Exception as e:
        logger.error(f"Error en mis_negocios: {str(e)}")
        messages.error(request, "Error al cargar tus negocios.")
        return redirect('inicio')

@require_POST
@login_required
@csrf_protect
def eliminar_negocio(request, negocio_id):
    """Vista para eliminar un negocio"""
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
    
    if request.method == 'POST':
        try:
            negocio.delete()
            messages.success(request, f'El negocio "{negocio.nombre}" ha sido eliminado.')
            return redirect('negocios:mis_negocios')
        except Exception as e:
            logger.error(f"Error al eliminar negocio: {e}")
            messages.error(request, 'Error al eliminar el negocio.')
    
    return render(request, 'negocios/confirmar_eliminacion_negocio.html', {'negocio': negocio})

@require_POST
@login_required
@csrf_protect
def restaurar_negocio(request, negocio_id):
    try:
        negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user, activo=False)
        negocio.activo = True
        negocio.save()
        logger.info(f"Negocio '{negocio.nombre}' restaurado por {request.user.username}")
        messages.success(request, f"El negocio '{negocio.nombre}' ha sido restaurado.")
    except Exception as e:
        logger.error(f"Error restaurando negocio: {str(e)}")
        messages.error(request, "Error al restaurar el negocio.")
    
    return redirect('negocios:mis_negocios')

@login_required
@csrf_protect
def configurar_negocio(request, negocio_id):
    try:
        negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)

        if request.method == 'POST':
            form = NegocioForm(request.POST, request.FILES, instance=negocio)
            if form.is_valid():
                form.save()
                logger.info(f"Negocio '{negocio.nombre}' actualizado por {request.user.username}")
                messages.success(request, "Negocio actualizado.")
                return redirect('negocios:configurar_negocio', negocio_id=negocio.id)
            else:
                logger.warning(f"Formulario inválido al configurar negocio: {form.errors}")
        else:
            form = NegocioForm(instance=negocio)

        return render(request, 'negocios/configurar_negocio.html', {'form': form, 'negocio': negocio})
    except Exception as e:
        logger.error(f"Error en configurar_negocio: {str(e)}")
        messages.error(request, "Error al cargar la configuración del negocio.")
        return redirect('negocios:mis_negocios')

@login_required
@csrf_protect
def panel_negocio(request, negocio_id):
    try:
        negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
        # Servicios activos del negocio
        servicios_activos = negocio.servicios_negocio.filter(activo=True).select_related('servicio')

        # Guardar horario de atención si es POST y no es cambio de logo
        if request.method == 'POST' and 'logo' not in request.FILES:
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            nuevo_horario = {}
            dias_activos = request.POST.getlist('dias_activos')
            for dia in dias:
                if dia in dias_activos:
                    inicio = request.POST.get(f'inicio_{dia}', '')
                    fin = request.POST.get(f'fin_{dia}', '')
                    if inicio and fin:
                        nuevo_horario[dia] = {"inicio": inicio, "fin": fin}
                # Si el día no está activo, no lo incluimos (aparecerá como cerrado)
            negocio.horario_atencion = nuevo_horario
            negocio.save()
            messages.success(request, "Horario de atención actualizado correctamente.")
            return redirect('negocios:panel_negocio', negocio_id=negocio.id)

        # Profesionales aceptados (matriculación aprobada)
        profesionales_aceptados = []
        for m in negocio.matriculaciones.filter(estado='aprobada').select_related('profesional'):
            prof = m.profesional
            # Horario (puedes ajustar el formato según tu modelo real)
            horarios = prof.horarios.all()
            horario_str = ', '.join([f"{h.get_dia_semana_display()}: {h.hora_inicio.strftime('%H:%M')} - {h.hora_fin.strftime('%H:%M')}" for h in horarios]) if horarios else 'No asignado'
            # Calificaciones
            calificaciones = prof.calificaciones.filter(negocio=negocio)
            promedio = round(calificaciones.aggregate(models.Avg('puntaje'))['puntaje__avg'] or 0, 1)
            num_calificaciones = calificaciones.count()
            # Servicios
            servicios = prof.servicios.all()
            servicios_nombres = ', '.join([s.nombre for s in servicios]) if servicios else 'No asignados'
            # Reservas
            from clientes.models import Reserva
            reservas_count = Reserva.objects.filter(profesional=prof, peluquero=negocio).count()
            profesionales_aceptados.append({
                'id': prof.id,
                'nombre_completo': prof.nombre_completo,
                'especialidad': prof.especialidad,
                'foto_perfil': prof.foto_perfil,
                'horario': horario_str,
                'promedio': promedio,
                'num_calificaciones': num_calificaciones,
                'servicios': servicios_nombres,
                'reservas_count': reservas_count,
            })

        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        horario_guardado = {}
        for dia in dias:
            base = negocio.horario_atencion.get(dia, {})
            horario_guardado[f"{dia}_inicio"] = base.get("inicio", "")
            horario_guardado[f"{dia}_fin"] = base.get("fin", "")
            horario_guardado[f"{dia}_activo"] = bool(base)

        return render(request, 'negocios/panel_negocio.html', {
            'negocio': negocio,
            'profesionales_aceptados': profesionales_aceptados,
            'dias': dias,
            'horario_guardado': horario_guardado,
            'servicios_activos': servicios_activos,
            'imagenes_galeria': negocio.imagenes.all().order_by('-created_at')[:6],  # Mostrar las 6 más recientes
        })
    except Exception as e:
        logger.error(f"Error en panel_negocio: {str(e)}")
        messages.error(request, "Error al cargar el panel del negocio.")
        return redirect('negocios:mis_negocios')

@login_required
def dashboard_negocio(request, negocio_id):
    # Obtener el negocio específico del usuario
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
    
    from datetime import datetime, timedelta, date
    from django.db.models import Count, Avg, Q
    from django.utils import timezone
    from clientes.models import Reserva
    from clientes.models import Calificacion
    
    # Fechas para los últimos 30 días
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    # Datos de reservas de los últimos 30 días
    reservas_30_dias = Reserva.objects.filter(
        peluquero=negocio,
        fecha__gte=hace_30_dias,
        fecha__lte=hoy
    ).order_by('fecha')
    
    # Generar datos para el gráfico de reservas (últimos 10 días)
    fechas_grafico = []
    reservas_grafico = []
    
    for i in range(10):
        fecha_actual = hoy - timedelta(days=9-i)
        count_reservas = reservas_30_dias.filter(fecha=fecha_actual).count()
        fechas_grafico.append(fecha_actual.strftime('%d/%m'))
        reservas_grafico.append(count_reservas)
    
    # Reporte del mes actual
    inicio_mes = hoy.replace(day=1)
    reservas_mes = Reserva.objects.filter(
        peluquero=negocio,
        fecha__gte=inicio_mes,
        fecha__lte=hoy
    )
    
    # Calcular ingresos totales (asumiendo precio promedio de $30 por servicio)
    total_reservas_mes = reservas_mes.count()
    ingresos_totales = total_reservas_mes * 30  # Precio promedio estimado
    
    # Clientes nuevos del mes (clientes que hicieron su primera reserva este mes)
    clientes_nuevos_mes = reservas_mes.values('cliente').distinct().count()
    
    # Día más ocupado del mes
    dia_mas_ocupado = reservas_mes.values('fecha').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    dia_mas_ocupado_nombre = 'N/A'
    if dia_mas_ocupado:
        fecha_ocupada = dia_mas_ocupado['fecha']
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        dia_mas_ocupado_nombre = dias_semana[fecha_ocupada.weekday()]
    
    # Hora pico (hora con más reservas)
    hora_pico_data = reservas_mes.values('hora_inicio').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    hora_pico = 'N/A'
    if hora_pico_data:
        hora_pico = hora_pico_data['hora_inicio'].strftime('%H:%M')
    
    # Mejor profesional del mes (por calificaciones)
    from profesionales.models import Matriculacion
    
    # Obtener profesionales aprobados del negocio
    matriculaciones_aprobadas = Matriculacion.objects.filter(
        negocio=negocio,
        estado='aprobada'
    ).select_related('profesional')
    
    profesionales_negocio = [m.profesional for m in matriculaciones_aprobadas]
    mejor_profesional = None
    mejor_puntuacion = 0
    
    for profesional in profesionales_negocio:
        calificaciones = Calificacion.objects.filter(
            negocio=negocio,
            profesional=profesional,
            fecha_calificacion__gte=inicio_mes
        )
        if calificaciones.exists():
            promedio = calificaciones.aggregate(Avg('puntaje'))['puntaje__avg']
            if promedio and promedio > mejor_puntuacion:
                mejor_puntuacion = promedio
                mejor_profesional = profesional
    
    # Ventas por mes (últimos 6 meses)
    meses_grafico = []
    ventas_mes_grafico = []
    
    for i in range(6):
        fecha_mes = hoy - timedelta(days=30*i)
        inicio_mes_grafico = fecha_mes.replace(day=1)
        fin_mes_grafico = (inicio_mes_grafico + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        reservas_mes_grafico = Reserva.objects.filter(
            peluquero=negocio,
            fecha__gte=inicio_mes_grafico,
            fecha__lte=fin_mes_grafico
        ).count()
        
        meses_grafico.append(fecha_mes.strftime('%m/%y'))
        ventas_mes_grafico.append(reservas_mes_grafico * 30)  # Precio promedio estimado
    
    # Crear objeto reporte
    class Reporte:
        def __init__(self):
            self.total_reservas = total_reservas_mes
            self.ingresos_totales = ingresos_totales
            self.clientes_nuevos = clientes_nuevos_mes
            self.dia_mas_ocupado = dia_mas_ocupado_nombre
            self.hora_pico = hora_pico
    
    reporte = Reporte()
    
    context = {
        'negocio': negocio,
        'fechas': fechas_grafico,
        'reservas': reservas_grafico,
        'meses': meses_grafico,
        'ventas_mes': ventas_mes_grafico,
        'reporte': reporte,
        'peluquero_top': mejor_profesional,
        'peluquero_top_score': round(mejor_puntuacion, 1) if mejor_puntuacion > 0 else 0,
        'dias_ocupados': dia_mas_ocupado_nombre,
        'hora_pico': hora_pico,
    }
    return render(request, 'negocios/dashboard_negocio.html', context)

@require_GET
def detalle_negocio(request, negocio_id):
    """Vista pública para ver detalles del negocio"""
    negocio = get_object_or_404(Negocio, id=negocio_id, activo=True)
    # Calificaciones percentil 75
    calificaciones = Calificacion.objects.filter(negocio=negocio).values_list('puntaje', flat=True)
    calificacion_percentil = 5
    if calificaciones:
        calificacion_percentil = round(float(np.percentile(list(calificaciones), 75)), 1)
    # Estado abierto/cerrado
    ahora = datetime.now()
    dia_semana = ahora.strftime('%A')
    dia_semana_es = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }[dia_semana]
    horario = negocio.horario_atencion.get(dia_semana_es, {})
    abierto = False
    proximo_cambio = None
    if horario and 'inicio' in horario and 'fin' in horario:
        try:
            inicio = datetime.strptime(horario['inicio'], '%H:%M').time()
            fin = datetime.strptime(horario['fin'], '%H:%M').time()
            if inicio <= ahora.time() <= fin:
                abierto = True
                proximo_cambio = fin.strftime('%H:%M')
            else:
                abierto = False
                proximo_cambio = inicio.strftime('%H:%M')
        except Exception:
            abierto = False
    # Ciudad (asumimos que está en la dirección)
    ciudad = negocio.direccion.split(',')[-1].strip() if ',' in negocio.direccion else negocio.direccion
    # Imágenes
    logo = negocio.logo
    portada = negocio.portada
    galeria = ImagenGaleria.objects.filter(negocio=negocio)
    imagenes = negocio.imagenes.all().order_by('-created_at')
    # Servicios del negocio
    servicios = negocio.servicios_negocio.select_related('servicio').all()
    # Profesionales matriculados aprobados
    matriculaciones = Matriculacion.objects.filter(negocio=negocio, estado='aprobada').select_related('profesional')
    profesionales = [m.profesional for m in matriculaciones]
    peluqueros_info = []
    for profesional in profesionales:
        avatar = profesional.foto_perfil if hasattr(profesional, 'foto_perfil') else None
        especialidad = profesional.especialidad if hasattr(profesional, 'especialidad') else ''
        descripcion = profesional.descripcion if hasattr(profesional, 'descripcion') else ''
        servicios_prof = profesional.servicios.all() if hasattr(profesional, 'servicios') else []
        # Calcular promedio y número de calificaciones
        calificaciones_prof = Calificacion.objects.filter(negocio=negocio, profesional=profesional)
        num_calificaciones = calificaciones_prof.count()
        promedio = round(calificaciones_prof.aggregate(models.Avg('puntaje'))['puntaje__avg'] or 0, 1) if num_calificaciones > 0 else 0
        peluquero_info = {
            'id': profesional.id,
            'nombre': profesional.nombre_completo,
            'avatar': avatar,
            'especialidad': especialidad,
            'descripcion': descripcion,
            'servicios': servicios_prof,
            'promedio': promedio,
            'num_calificaciones': num_calificaciones,
        }
        peluqueros_info.append(peluquero_info)
    # Comentarios
    comentarios = Calificacion.objects.filter(negocio=negocio).exclude(comentario='').order_by('-fecha_calificacion')
    # Días laborables para el calendario visual
    dias_laborables = set()
    for dia, h in (negocio.horario_atencion or {}).items():
        if h and h.get('inicio') and h.get('fin'):
            dias_laborables.add(dia)
    # Mes y año actual para el calendario
    from datetime import date
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year
    return render(request, 'negocios/detalle_negocio.html', {
        'negocio': negocio,
        'peluqueros_info': peluqueros_info,
        'calificacion_percentil': calificacion_percentil,
        'abierto': abierto,
        'proximo_cambio': proximo_cambio,
        'ciudad': ciudad,
        'logo': logo,
        'portada': portada,
        'galeria': galeria,
        'imagenes': imagenes,
        'servicios': servicios,
        'profesionales': profesionales,
        'comentarios': comentarios,
        'dias_laborables': list(dias_laborables),
        'mes_actual': mes_actual,
        'anio_actual': anio_actual,
    })

@login_required
def editar_negocio(request, negocio_id):
    """Vista para editar un negocio y su galería de imágenes"""
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
    imagenes = negocio.imagenes.all()
    imagen_form = ImagenNegocioForm()
    if request.method == 'POST':
        form = NegocioForm(request.POST, request.FILES, instance=negocio)
        if 'agregar_imagen' in request.POST:
            imagen_form = ImagenNegocioForm(request.POST, request.FILES)
            if imagen_form.is_valid():
                nueva_imagen = imagen_form.save(commit=False)
                nueva_imagen.negocio = negocio
                nueva_imagen.save()
                messages.success(request, 'Imagen agregada a la galería.')
                return redirect('negocios:editar_negocio', negocio_id=negocio.id)
        elif form.is_valid():
            negocio = form.save(commit=False)
            negocio.save()
            form.save_m2m()
            # Si se agregó un nuevo servicio, créalo y asígnalo
            nuevo_servicio = form.cleaned_data.get('nuevo_servicio')
            if nuevo_servicio:
                servicio, creado = Servicio.objects.get_or_create(nombre=nuevo_servicio)
                from .models import ServicioNegocio
                ServicioNegocio.objects.get_or_create(negocio=negocio, servicio=servicio)
            # Guardar servicios seleccionados y duración personalizada
            servicios_ids = request.POST.getlist('servicios')
            servicios_negocio = negocio.servicios_negocio.all()
            for sn in servicios_negocio:
                sn_activo = str(sn.id) in servicios_ids
                # Actualizar duración personalizada
                nueva_duracion = request.POST.get(f'duracion_{sn.id}')
                if nueva_duracion:
                    try:
                        sn.duracion = int(nueva_duracion)
                    except ValueError:
                        pass
                if sn_activo and not sn.activo:
                    sn.activo = True
                elif not sn_activo and sn.activo:
                    sn.activo = False
                sn.save()
            messages.success(request, 'Negocio actualizado exitosamente.')
            # Log para depuración de redirección
            logger.warning(f"[DEBUG] Usuario: {request.user.username}, tipo: {getattr(request.user, 'tipo', None)}")
            # Redirige según el tipo de usuario
            if hasattr(request.user, 'tipo') and request.user.tipo == 'negocio':
                logger.warning(f"[DEBUG] Redirigiendo a panel_negocio para negocio_id={negocio.id}")
                return redirect('negocios:panel_negocio', negocio_id=negocio.id)
            else:
                logger.warning(f"[DEBUG] Redirigiendo a detalle_negocio para negocio_id={negocio.id}")
                return redirect('negocios:detalle_negocio', negocio_id=negocio.id)
    else:
        form = NegocioForm(instance=negocio)
    # Obtener todos los servicios disponibles para el negocio
    servicios_negocio = negocio.servicios_negocio.all()
    return render(request, 'negocios/editar_negocio.html', {
        'form': form,
        'negocio': negocio,
        'imagenes': imagenes,
        'imagen_form': imagen_form,
        'servicios_negocio': servicios_negocio,
    })

@login_required
def solicitudes_matricula(request):
    user = request.user
    if user.tipo != 'negocio':
        messages.error(request, 'Acceso solo para negocios.')
        return redirect('inicio')
    negocios = user.negocios.all()
    solicitudes = Matriculacion.objects.filter(negocio__in=negocios, estado='pendiente').select_related('profesional', 'negocio')
    return render(request, 'negocios/solicitudes_matricula.html', {'solicitudes': solicitudes})

@login_required
def ver_perfil_profesional(request, profesional_id):
    profesional = get_object_or_404(Profesional, id=profesional_id)
    negocio_id = request.GET.get('negocio_id')
    negocio = None
    if negocio_id:
        from .models import Negocio
        try:
            negocio = Negocio.objects.get(id=negocio_id, propietario=request.user)
        except Negocio.DoesNotExist:
            negocio = None
    
    # Obtener horarios del profesional
    from profesionales.models import HorarioProfesional
    horarios = HorarioProfesional.objects.filter(profesional=profesional, disponible=True).order_by('dia_semana')
    
    return render(request, 'negocios/perfil_profesional.html', {
        'profesional': profesional,
        'negocio': negocio,
        'horarios': horarios,
    })

@require_POST
@login_required
def api_responder_matricula(request, solicitud_id, accion):
    user = request.user
    if user.tipo != 'negocio':
        return JsonResponse({'ok': False, 'error': 'Solo negocios pueden realizar esta acción.'}, status=403)
    try:
        solicitud = Matriculacion.objects.get(id=solicitud_id, negocio__propietario=user)
        if solicitud.estado != 'pendiente':
            return JsonResponse({'ok': False, 'error': 'La solicitud ya fue respondida.'}, status=400)
        if accion == 'aceptar':
            solicitud.aprobar()
            Notificacion.objects.create(
                profesional=solicitud.profesional,
                tipo='matriculacion',
                titulo='¡Solicitud aceptada!',
                mensaje=f'Tu solicitud para unirte a {solicitud.negocio.nombre} ha sido aceptada.',
                url_relacionada=''
            )
        elif accion == 'rechazar':
            solicitud.rechazar()
            Notificacion.objects.create(
                profesional=solicitud.profesional,
                tipo='matriculacion',
                titulo='Solicitud rechazada',
                mensaje=f'Tu solicitud para unirte a {solicitud.negocio.nombre} ha sido rechazada.',
                url_relacionada=''
            )
        else:
            return JsonResponse({'ok': False, 'error': 'Acción no válida.'}, status=400)
        return JsonResponse({'ok': True, 'negocio_id': solicitud.negocio.id})
    except Matriculacion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Solicitud no encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@login_required
def desvincular_profesional(request, matricula_id):
    user = request.user
    if user.tipo != 'negocio':
        messages.error(request, 'Acceso solo para negocios.')
        return redirect('inicio')
    matricula = get_object_or_404(Matriculacion, id=matricula_id, negocio__propietario=user, estado='aprobada')
    if request.method == 'POST':
        matricula.estado = 'cancelada'
        matricula.save()
        messages.success(request, 'Profesional desvinculado correctamente.')
        return redirect('negocios:solicitudes_matricula')
    return render(request, 'negocios/desvincular_profesional.html', {'matricula': matricula})

@login_required
def galeria_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
    imagenes = negocio.imagenes.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = ImagenNegocioForm(request.POST, request.FILES)
        if form.is_valid():
            imagen = form.save(commit=False)
            imagen.negocio = negocio
            imagen.save()
            messages.success(request, 'Imagen agregada a la galería correctamente.')
            return redirect('negocios:galeria_negocio', negocio_id=negocio.id)
        else:
            messages.error(request, 'Error al agregar la imagen. Por favor, verifica los datos.')
    else:
        form = ImagenNegocioForm()
    
    return render(request, 'negocios/galeria_negocio.html', {
        'negocio': negocio,
        'imagenes': imagenes,
        'form': form,
    })

@login_required
def editar_profesional_negocio(request, negocio_id, profesional_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
    profesional = get_object_or_404(Profesional, id=profesional_id)
    matriculacion = get_object_or_404(Matriculacion, negocio=negocio, profesional=profesional, estado='aprobada')
    servicios_negocio = ServicioNegocio.objects.filter(negocio=negocio)
    
    if request.method == 'POST':
        # Actualizar servicios asignados
        servicios_ids = request.POST.getlist('servicios')
        servicios_a_asignar = [s.servicio for s in servicios_negocio if str(s.id) in servicios_ids]
        profesional.servicios.set(servicios_a_asignar)
        
        # Mensaje específico sobre servicios
        if servicios_a_asignar:
            servicios_nombres = ', '.join([s.nombre for s in servicios_a_asignar])
            messages.success(request, f'Servicios asignados correctamente: {servicios_nombres}')
        else:
            messages.warning(request, 'No se asignaron servicios al profesional.')
        
        # Actualizar horarios usando el modelo HorarioProfesional
        from profesionales.models import HorarioProfesional
        from datetime import time
        
        # Eliminar horarios existentes
        profesional.horarios.all().delete()
        
        # Crear nuevos horarios
        dias = request.POST.getlist('dias')
        for dia in dias:
            inicio = request.POST.get(f'inicio_{dia}')
            fin = request.POST.get(f'fin_{dia}')
            if inicio and fin:
                try:
                    # Convertir strings de tiempo a objetos time
                    hora_inicio = time.fromisoformat(inicio)
                    hora_fin = time.fromisoformat(fin)
                    
                    # Mapear nombres de días a los valores del modelo
                    dia_mapping = {
                        'Lunes': 'lunes',
                        'Martes': 'martes', 
                        'Miércoles': 'miercoles',
                        'Jueves': 'jueves',
                        'Viernes': 'viernes',
                        'Sábado': 'sabado',
                        'Domingo': 'domingo'
                    }
                    
                    dia_semana = dia_mapping.get(dia, dia.lower())
                    
                    HorarioProfesional.objects.create(
                        profesional=profesional,
                        dia_semana=dia_semana,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        disponible=True
                    )
                except (ValueError, TypeError) as e:
                    messages.error(request, f'Error en el formato de hora para {dia}: {e}')
                    continue
        
        messages.success(request, 'Perfil del profesional actualizado correctamente.')
        return redirect('negocios:panel_negocio', negocio_id=negocio.id)
    
    # Días de la semana
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    # Obtener horarios actuales del modelo HorarioProfesional
    horarios_actuales = {}
    for horario in profesional.horarios.all():
        # Mapear de vuelta a nombres en español
        dia_mapping_reverse = {
            'lunes': 'Lunes',
            'martes': 'Martes',
            'miercoles': 'Miércoles', 
            'jueves': 'Jueves',
            'viernes': 'Viernes',
            'sabado': 'Sábado',
            'domingo': 'Domingo'
        }
        dia_nombre = dia_mapping_reverse.get(horario.dia_semana, horario.dia_semana)
        horarios_actuales[dia_nombre] = {
            'inicio': horario.hora_inicio.strftime('%H:%M'),
            'fin': horario.hora_fin.strftime('%H:%M')
        }
    
    servicios_asignados = profesional.servicios.values_list('id', flat=True)
    return render(request, 'negocios/editar_profesional_negocio.html', {
        'negocio': negocio,
        'profesional': profesional,
        'servicios_negocio': servicios_negocio,
        'dias_semana': dias_semana,
        'horario_actual': horarios_actuales,
        'servicios_asignados': servicios_asignados,
    })

def calendario_reservas(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
    return render(request, 'negocios/calendario_reservas.html', {'negocio': negocio})

def api_reservas_negocio(request, negocio_id):
    from clientes.models import Reserva
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
    reservas = Reserva.objects.filter(peluquero=negocio)
    eventos = []
    for r in reservas:
        eventos.append({
            'id': r.id,
            'title': f'{r.servicio.nombre if r.servicio else "Reserva"} - {r.cliente}',
            'start': f'{r.fecha}T{r.hora_inicio}',
            'end': f'{r.fecha}T{r.hora_fin}',
            'extendedProps': {
                'profesional': str(r.profesional) if r.profesional else '',
                'estado': r.estado,
            }
        })
    return JsonResponse(eventos, safe=False)

class ServicioNegocioForm(ModelForm):
    class Meta:
        model = ServicioNegocio
        fields = ['servicio', 'duracion', 'precio']

def gestionar_servicios(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
    ServicioFormSet = modelformset_factory(ServicioNegocio, form=ServicioNegocioForm, extra=1, can_delete=True)
    queryset = ServicioNegocio.objects.filter(negocio=negocio)
    if request.method == 'POST':
        formset = ServicioFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            for instance in instances:
                instance.negocio = negocio
                instance.save()
            formset.save_m2m()
            messages.success(request, 'Servicios actualizados correctamente.')
            return redirect('negocios:gestionar_servicios', negocio_id=negocio.id)
    else:
        formset = ServicioFormSet(queryset=queryset)
    return render(request, 'negocios/gestionar_servicios.html', {'negocio': negocio, 'formset': formset})

@login_required
def notificaciones_negocio(request):
    if getattr(request.user, 'tipo', None) != 'negocio':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Solo negocios pueden ver esta página.')
    # Obtener todas las notificaciones de los negocios del usuario
    negocios_usuario = request.user.negocios.all()
    notificaciones = NotificacionNegocio.objects.filter(negocio__in=negocios_usuario).order_by('-fecha_creacion')
    return render(request, 'negocios/notificaciones.html', {'notificaciones': notificaciones})

@login_required
def solicitudes_ausencia(request):
    """Vista para que el negocio vea las solicitudes de ausencia pendientes"""
    if getattr(request.user, 'tipo', None) != 'negocio':
        messages.error(request, 'Solo negocios pueden ver esta página.')
        return redirect('inicio')
    
    # Obtener solicitudes de ausencia de todos los negocios del usuario
    negocios_usuario = request.user.negocios.all()
    
    # Debug: verificar todos los estados de solicitudes
    todas_solicitudes = SolicitudAusencia.objects.filter(
        negocio__in=negocios_usuario
    ).select_related('profesional', 'negocio')
    
    print(f"DEBUG: Total de solicitudes encontradas: {todas_solicitudes.count()}")
    for solicitud in todas_solicitudes:
        print(f"DEBUG: Solicitud {solicitud.id} - Estado: {solicitud.estado} - Profesional: {solicitud.profesional.nombre_completo}")
    
    solicitudes_pendientes = todas_solicitudes.filter(estado='pendiente').order_by('-fecha_solicitud')
    solicitudes_aprobadas = todas_solicitudes.filter(estado='aprobada').order_by('-fecha_respuesta')
    solicitudes_rechazadas = todas_solicitudes.filter(estado='rechazada').order_by('-fecha_respuesta')
    
    print(f"DEBUG: Pendientes: {solicitudes_pendientes.count()}, Aprobadas: {solicitudes_aprobadas.count()}, Rechazadas: {solicitudes_rechazadas.count()}")
    
    return render(request, 'negocios/solicitudes_ausencia.html', {
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_aprobadas': solicitudes_aprobadas,
        'solicitudes_rechazadas': solicitudes_rechazadas,
    })

@login_required
def revisar_solicitud_ausencia(request, solicitud_id):
    """Vista para que el negocio revise una solicitud específica de ausencia"""
    if getattr(request.user, 'tipo', None) != 'negocio':
        messages.error(request, 'Solo negocios pueden ver esta página.')
        return redirect('inicio')
    
    solicitud = get_object_or_404(
        SolicitudAusencia, 
        id=solicitud_id,
        negocio__propietario=request.user,
        estado='pendiente'
    )
    
    if request.method == 'POST':
        print(f"DEBUG: POST recibido para solicitud {solicitud_id}")
        print(f"DEBUG: POST data: {request.POST}")
        
        accion = request.POST.get('accion')
        comentario = request.POST.get('comentario', '')
        
        print(f"DEBUG: Acción extraída: '{accion}'")
        print(f"DEBUG: Comentario extraído: '{comentario}'")

        if not accion:
            print(f"DEBUG: No se recibió acción, mostrando error")
            messages.error(request, 'Debes elegir una acción (Aprobar o Rechazar) usando los botones.')
            return redirect(request.path)
        
        print(f"DEBUG: Procesando acción '{accion}' para solicitud {solicitud_id}")
        print(f"DEBUG: Estado actual de la solicitud: {solicitud.estado}")
        
        if accion == 'aprobar':
            # Aprobar la solicitud
            solicitud.aprobar(comentario)
            
            # Verificar que el estado se actualizó correctamente
            solicitud.refresh_from_db()
            print(f"DEBUG: Estado después de aprobar: {solicitud.estado}")
            
            # Crear notificación para el profesional
            Notificacion.objects.create(
                profesional=solicitud.profesional,
                tipo='solicitud_ausencia',
                titulo='Solicitud de ausencia aprobada',
                mensaje=f'Tu solicitud de ausencia del {solicitud.fecha_inicio} al {solicitud.fecha_fin} ha sido aprobada por {solicitud.negocio.nombre}.',
                url_relacionada='/profesionales/gestionar-ausencias/',
            )
            
            messages.success(request, f'Solicitud de ausencia aprobada correctamente. La solicitud de {solicitud.profesional.nombre_completo} ahora aparece en la lista de aprobadas.')
            
        elif accion == 'rechazar':
            # Rechazar la solicitud
            solicitud.rechazar(comentario)
            
            # Verificar que el estado se actualizó correctamente
            solicitud.refresh_from_db()
            print(f"DEBUG: Estado después de rechazar: {solicitud.estado}")
            
            # Crear notificación para el profesional
            Notificacion.objects.create(
                profesional=solicitud.profesional,
                tipo='solicitud_ausencia',
                titulo='Solicitud de ausencia rechazada',
                mensaje=f'Tu solicitud de ausencia del {solicitud.fecha_inicio} al {solicitud.fecha_fin} ha sido rechazada por {solicitud.negocio.nombre}.',
                url_relacionada='/profesionales/gestionar-ausencias/',
            )
            
            messages.success(request, f'Solicitud de ausencia rechazada correctamente. La solicitud de {solicitud.profesional.nombre_completo} ahora aparece en la lista de rechazadas.')
        
        # Forzar un refresh de la página para mostrar los cambios
        return redirect('negocios:solicitudes_ausencia')
    
    return render(request, 'negocios/revisar_solicitud_ausencia.html', {
        'solicitud': solicitud,
    })

@login_required
def listar_dias_descanso(request):
    """Vista para que el negocio vea sus días de descanso"""
    if getattr(request.user, 'tipo', None) != 'negocio':
        messages.error(request, 'Solo negocios pueden ver esta página.')
        return redirect('inicio')
    
    # Obtener días de descanso de todos los negocios del usuario
    negocios_usuario = request.user.negocios.all()
    dias_descanso = DiaDescanso.objects.filter(
        negocio__in=negocios_usuario
    ).select_related('negocio').order_by('-fecha')
    
    dias_activos = dias_descanso.filter(activo=True).count()
    dias_futuros = dias_descanso.filter(fecha__gte=date.today()).count()
    
    context = {
        'dias_descanso': dias_descanso,
        'negocios': negocios_usuario,
        'dias_activos': dias_activos,
        'dias_futuros': dias_futuros,
    }
    return render(request, 'negocios/listar_dias_descanso.html', context)

@login_required
def crear_dia_descanso(request):
    """Vista para que el negocio cree un nuevo día de descanso"""
    if getattr(request.user, 'tipo', None) != 'negocio':
        messages.error(request, 'Solo negocios pueden ver esta página.')
        return redirect('inicio')
    
    if request.method == 'POST':
        negocio_id = request.POST.get('negocio')
        fecha = request.POST.get('fecha')
        tipo = request.POST.get('tipo')
        motivo = request.POST.get('motivo', '')
        descripcion = request.POST.get('descripcion', '')
        
        try:
            negocio = request.user.negocios.get(id=negocio_id)
            
            # Verificar que no exista ya un día de descanso para esa fecha
            if DiaDescanso.objects.filter(negocio=negocio, fecha=fecha).exists():
                messages.error(request, f'Ya existe un día de descanso programado para el {fecha}.')
                return redirect('negocios:listar_dias_descanso')
            
            # Crear el día de descanso
            dia_descanso = DiaDescanso.objects.create(
                negocio=negocio,
                fecha=fecha,
                tipo=tipo,
                motivo=motivo,
                descripcion=descripcion
            )
            
            messages.success(request, f'Día de descanso programado para el {fecha} correctamente.')
            return redirect('negocios:listar_dias_descanso')
            
        except Negocio.DoesNotExist:
            messages.error(request, 'Negocio no válido.')
        except Exception as e:
            logger.error(f"Error al crear día de descanso: {str(e)}")
            messages.error(request, f'Error al crear el día de descanso: {str(e)}')
            # Log detallado para debugging
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
    
    # Obtener negocios del usuario para el formulario
    negocios = request.user.negocios.all()
    
    context = {
        'negocios': negocios,
        'tipos': DiaDescanso.TIPO_CHOICES,
    }
    return render(request, 'negocios/crear_dia_descanso.html', context)

@login_required
def editar_dia_descanso(request, dia_id):
    """Vista para que el negocio edite un día de descanso"""
    if getattr(request.user, 'tipo', None) != 'negocio':
        messages.error(request, 'Solo negocios pueden ver esta página.')
        return redirect('inicio')
    
    dia_descanso = get_object_or_404(
        DiaDescanso, 
        id=dia_id,
        negocio__propietario=request.user
    )
    
    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        tipo = request.POST.get('tipo')
        motivo = request.POST.get('motivo', '')
        descripcion = request.POST.get('descripcion', '')
        activo = request.POST.get('activo') == 'on'
        
        try:
            # Verificar que no exista otro día de descanso para esa fecha (excluyendo el actual)
            if DiaDescanso.objects.filter(negocio=dia_descanso.negocio, fecha=fecha).exclude(id=dia_id).exists():
                messages.error(request, f'Ya existe un día de descanso programado para el {fecha}.')
                return redirect('negocios:listar_dias_descanso')
            
            # Actualizar el día de descanso
            dia_descanso.fecha = fecha
            dia_descanso.tipo = tipo
            dia_descanso.motivo = motivo
            dia_descanso.descripcion = descripcion
            dia_descanso.activo = activo
            dia_descanso.save()
            
            messages.success(request, 'Día de descanso actualizado correctamente.')
            return redirect('negocios:listar_dias_descanso')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el día de descanso: {str(e)}')
    
    context = {
        'dia_descanso': dia_descanso,
        'tipos': DiaDescanso.TIPO_CHOICES,
    }
    return render(request, 'negocios/editar_dia_descanso.html', context)

@login_required
def eliminar_dia_descanso(request, dia_id):
    """Vista para que el negocio elimine un día de descanso"""
    if getattr(request.user, 'tipo', None) != 'negocio':
        messages.error(request, 'Solo negocios pueden ver esta página.')
        return redirect('inicio')
    
    dia_descanso = get_object_or_404(
        DiaDescanso, 
        id=dia_id,
        negocio__propietario=request.user
    )
    
    if request.method == 'POST':
        dia_descanso.delete()
        messages.success(request, 'Día de descanso eliminado correctamente.')
        return redirect('negocios:listar_dias_descanso')
    
    context = {
        'dia_descanso': dia_descanso,
    }
    return render(request, 'negocios/eliminar_dia_descanso.html', context)