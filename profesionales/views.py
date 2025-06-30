from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProfesionalPerfilForm
from .models import Profesional, Matriculacion, Notificacion
from negocios.models import Negocio

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
    notis_no_leidas = profesional.notificaciones.filter(leida=False).count() if profesional else 0
    servicios = profesional.servicios.all() if profesional else []
    # Malla de turnos: suponemos que está en profesional.horarios.all()
    horarios = profesional.horarios.all() if profesional else []
    return render(request, 'profesionales/panel.html', {
        'profesional': profesional,
        'notis_no_leidas': notis_no_leidas,
        'servicios': servicios,
        'horarios': horarios,
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
                Matriculacion.objects.create(profesional=profesional, negocio=negocio, mensaje_solicitud=mensaje)
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
