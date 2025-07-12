from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProfesionalPerfilForm
from .models import Profesional, Matriculacion, Notificacion
from negocios.models import Negocio, NotificacionNegocio
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Profesional
from clientes.models import Calificacion
from .models import AusenciaProfesional, SolicitudAusencia
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

# Create your views here.

@login_required
def completar_perfil(request):
    user = request.user
    if user.tipo != 'profesional':
        messages.error(request, 'Solo los profesionales pueden completar este perfil.')
        return redirect('inicio')

    # Si ya tiene perfil, redirigir al panel
    if hasattr(user, 'perfil_profesional'):
        return redirect('profesionales:panel')

    if request.method == 'POST':
        form = ProfesionalPerfilForm(request.POST, request.FILES)
        if form.is_valid():
            profesional = form.save(commit=False)
            profesional.usuario = user
            profesional.save()
            messages.success(request, '¡Perfil profesional completado exitosamente!')
            return redirect('profesionales:panel')
    else:
        form = ProfesionalPerfilForm()
    return render(request, 'profesionales/completar_perfil.html', {'form': form})

@login_required
def editar_perfil(request):
    user = request.user
    if user.tipo != 'profesional':
        messages.error(request, 'Acceso solo para profesionales.')
        return redirect('inicio')
    profesional = get_object_or_404(Profesional, usuario=user)
    if request.method == 'POST':
        form = ProfesionalPerfilForm(request.POST, request.FILES, instance=profesional)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('profesionales:panel')
    else:
        form = ProfesionalPerfilForm(instance=profesional)
    return render(request, 'profesionales/editar_perfil.html', {'form': form, 'profesional': profesional})

@login_required
def panel(request):
    user = request.user
    if user.tipo != 'profesional':
        messages.error(request, 'Acceso solo para profesionales.')
        return redirect('inicio')
    profesional = getattr(user, 'perfil_profesional', None)
    
    if not profesional:
        messages.error(request, 'No tienes un perfil profesional configurado.')
        return redirect('profesionales:completar_perfil')
    
    notis_no_leidas = profesional.notificaciones.filter(leida=False).count()
    servicios = profesional.servicios.all()
    
    # Obtener horarios del modelo HorarioProfesional
    horarios = profesional.horarios.filter(disponible=True).order_by('dia_semana')
    matricula_activa = profesional.matriculaciones.filter(estado='aprobada').last()
    
    return render(request, 'profesionales/panel.html', {
        'profesional': profesional,
        'notis_no_leidas': notis_no_leidas,
        'servicios': servicios,
        'horarios': horarios,
        'matricula_activa': matricula_activa,
    })

@login_required
def buscar_negocio(request):
    user = request.user
    if user.tipo != 'profesional':
        messages.error(request, 'Acceso solo para profesionales.')
        return redirect('inicio')
    profesional = getattr(user, 'perfil_profesional', None)
    matricula_activa = profesional.matriculaciones.filter(estado__in=['pendiente', 'aprobada']).first() if profesional else None
    negocios = Negocio.objects.filter(activo=True)
    if request.method == 'POST':
        negocio_id = request.POST.get('negocio_id')
        mensaje = request.POST.get('mensaje', '')
        negocio = Negocio.objects.get(id=negocio_id)
        existe_activa = Matriculacion.objects.filter(profesional=profesional, negocio=negocio, estado__in=['pendiente', 'aprobada']).exists()
        if existe_activa:
            messages.warning(request, 'Ya tienes una solicitud activa o aprobada con este negocio.')
        else:
            # Buscar si existe una solicitud previa (cancelada o rechazada)
            matricula_existente = Matriculacion.objects.filter(profesional=profesional, negocio=negocio).first()
            if matricula_existente:
                matricula_existente.estado = 'pendiente'
                matricula_existente.mensaje_solicitud = mensaje
                matricula_existente.save()
                messages.success(request, f'Solicitud reenviada a {negocio.nombre}.')
            else:
                matricula = Matriculacion.objects.create(profesional=profesional, negocio=negocio, mensaje_solicitud=mensaje)
                # Crear notificación para el negocio
                NotificacionNegocio.objects.create(
                    negocio=negocio,
                    tipo='matriculacion',
                    titulo='Nueva solicitud de matriculación',
                    mensaje=f'El profesional {profesional.nombre_completo} ha enviado una solicitud para unirse a tu negocio.',
                    url_relacionada='',
                )
                messages.success(request, f'Solicitud enviada a {negocio.nombre}.')
        return redirect('profesionales:buscar_negocio')
    return render(request, 'profesionales/buscar_negocio.html', {
        'negocios': negocios,
        'profesional': profesional,
        'matricula_activa': matricula_activa
    })

@login_required
def cancelar_matricula(request, matricula_id):
    user = request.user
    if user.tipo != 'profesional':
        messages.error(request, 'Acceso solo para profesionales.')
        return redirect('inicio')
    profesional = getattr(user, 'perfil_profesional', None)
    matricula = get_object_or_404(Matriculacion, id=matricula_id, profesional=profesional, estado='pendiente')
    if request.method == 'POST':
        matricula.estado = 'cancelada'
        matricula.save()
        messages.success(request, 'Solicitud cancelada correctamente.')
        return redirect('profesionales:panel')
    return render(request, 'profesionales/cancelar_matricula.html', {'matricula': matricula})

@login_required
def notificaciones(request):
    user = request.user
    if user.tipo != 'profesional':
        messages.error(request, 'Acceso solo para profesionales.')
        return redirect('inicio')
    profesional = getattr(user, 'perfil_profesional', None)
    notificaciones = Notificacion.objects.filter(profesional=profesional).order_by('-fecha_creacion')
    return render(request, 'profesionales/notificaciones.html', {'notificaciones': notificaciones})

@require_POST
@login_required
def eliminar_notificacion(request, notificacion_id):
    user = request.user
    if user.tipo != 'profesional':
        return JsonResponse({'ok': False, 'error': 'Solo profesionales.'}, status=403)
    profesional = getattr(user, 'perfil_profesional', None)
    try:
        noti = Notificacion.objects.get(id=notificacion_id, profesional=profesional)
        noti.delete()
        return JsonResponse({'ok': True})
    except Notificacion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrada'}, status=404)

def publica_profesional(request, pk):
    profesional = get_object_or_404(Profesional, pk=pk)
    calificaciones = profesional.usuario.calificaciones_recibidas.all() if hasattr(profesional.usuario, 'calificaciones_recibidas') else []
    servicios = profesional.servicios.all()
    if calificaciones:
        promedio_calificacion = sum([c.puntaje for c in calificaciones]) / len(calificaciones)
    else:
        promedio_calificacion = None
    matricula = profesional.matriculaciones.filter(estado='aprobada').select_related('negocio').first()
    negocio = matricula.negocio if matricula else None
    return render(request, 'profesionales/publica_profesional.html', {
        'profesional': profesional,
        'calificaciones': calificaciones,
        'servicios': servicios,
        'promedio_calificacion': promedio_calificacion,
        'negocio': negocio,
    })

@login_required
def gestionar_ausencias(request):
    profesional = getattr(request.user, 'perfil_profesional', None)
    if not profesional:
        messages.error(request, 'Solo los profesionales pueden gestionar ausencias.')
        return redirect('profesionales:panel')
    
    # Obtener el negocio donde trabaja el profesional
    matricula_activa = profesional.matriculaciones.filter(estado='aprobada').first()
    if not matricula_activa:
        messages.error(request, 'Debes estar matriculado en un negocio para solicitar ausencias.')
        return redirect('profesionales:panel')
    
    negocio = matricula_activa.negocio
    
    if request.method == 'POST':
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        motivo = request.POST.get('motivo', '')
        
        if fecha_inicio and fecha_fin:
            try:
                fi = timezone.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                ff = timezone.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                
                if fi > ff:
                    messages.error(request, 'La fecha de inicio no puede ser posterior a la de fin.')
                elif fi < timezone.now().date():
                    messages.error(request, 'No puedes solicitar ausencias en fechas pasadas.')
                else:
                    # Verificar si ya existe una solicitud pendiente para estas fechas
                    solicitud_existente = SolicitudAusencia.objects.filter(
                        profesional=profesional,
                        negocio=negocio,
                        estado='pendiente',
                        fecha_inicio=fi,
                        fecha_fin=ff
                    ).first()
                    
                    if solicitud_existente:
                        messages.warning(request, 'Ya tienes una solicitud pendiente para estas fechas.')
                    else:
                        # Crear la solicitud de ausencia
                        solicitud = SolicitudAusencia.objects.create(
                            profesional=profesional,
                            negocio=negocio,
                            fecha_inicio=fi,
                            fecha_fin=ff,
                            motivo=motivo
                        )
                        
                        # Crear notificación para el negocio
                        NotificacionNegocio.objects.create(
                            negocio=negocio,
                            tipo='solicitud_ausencia',
                            titulo='Nueva solicitud de ausencia',
                            mensaje=f'El profesional {profesional.nombre_completo} ha solicitado ausencia del {fi} al {ff}.',
                            url_relacionada=f'/negocios/revisar-solicitud-ausencia/{solicitud.id}/',
                        )
                        
                        messages.success(request, 'Solicitud de ausencia enviada al negocio. Espera la aprobación.')
                        return redirect('profesionales:gestionar_ausencias')
                        
            except Exception:
                messages.error(request, 'Fechas inválidas.')
        else:
            messages.error(request, 'Debes completar ambas fechas.')
    
    # Eliminar solicitud pendiente
    if request.GET.get('cancelar_solicitud'):
        try:
            solicitud = SolicitudAusencia.objects.get(
                id=request.GET['cancelar_solicitud'], 
                profesional=profesional,
                estado='pendiente'
            )
            solicitud.estado = 'cancelada'
            solicitud.save()
            messages.success(request, 'Solicitud cancelada.')
            return redirect('profesionales:gestionar_ausencias')
        except SolicitudAusencia.DoesNotExist:
            messages.error(request, 'Solicitud no encontrada.')
    
    # Eliminar ausencia aprobada
    if request.GET.get('eliminar_ausencia'):
        try:
            ausencia = AusenciaProfesional.objects.get(
                id=request.GET['eliminar_ausencia'], 
                profesional=profesional
            )
            ausencia.delete()
            messages.success(request, 'Ausencia eliminada.')
            return redirect('profesionales:gestionar_ausencias')
        except AusenciaProfesional.DoesNotExist:
            messages.error(request, 'Ausencia no encontrada.')
    
    # Obtener datos para la plantilla
    solicitudes_pendientes = profesional.solicitudes_ausencia.filter(estado='pendiente').order_by('-fecha_solicitud')
    solicitudes_aprobadas = profesional.solicitudes_ausencia.filter(estado='aprobada').order_by('-fecha_respuesta')
    solicitudes_rechazadas = profesional.solicitudes_ausencia.filter(estado='rechazada').order_by('-fecha_respuesta')
    ausencias_activas = profesional.ausencias.filter(activo=True).order_by('-fecha_inicio')
    
    return render(request, 'profesionales/gestionar_ausencias.html', {
        'negocio': negocio,
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_aprobadas': solicitudes_aprobadas,
        'solicitudes_rechazadas': solicitudes_rechazadas,
        'ausencias_activas': ausencias_activas,
    })
