from .forms import NegocioForm
from django.contrib.auth.decorators import login_required
from .models import Negocio, Peluquero
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .forms import PeluqueroForm
from .forms import ImagenGaleriaForm
from datetime import datetime, timedelta
from django.http import JsonResponse



@login_required
def crear_negocio(request):
    print("¿Usuario autenticado?", request.user.is_authenticated)
    print("Tipo de usuario:", repr(request.user.tipo))

    if request.user.tipo.strip().lower() != 'cliente':
        messages.error(request, "Solo los clientes pueden crear negocios.")
        return redirect('inicio')

    if request.method == 'POST':
        form = NegocioForm(request.POST, request.FILES)
        if form.is_valid():
            negocio = form.save(commit=False)
            negocio.propietario = request.user
            negocio.save()
            messages.success(request, "Negocio creado exitosamente.")
            return redirect('panel_negocio', negocio_id=negocio.id)
    else:
        form = NegocioForm()

    return render(request, 'negocios/crear_negocio.html', {'form': form})




@login_required
def mis_negocios(request):
    negocios_activos = request.user.negocios.filter(activo=True)
    negocios_eliminados = request.user.negocios.filter(activo=False)
    tiene_eliminados = negocios_eliminados.exists()

    return render(request, 'negocios/mis_negocios.html', {
        'negocios': negocios_activos,
        'negocios_eliminados': negocios_eliminados,
        'tiene_eliminados': tiene_eliminados,
    })


@require_POST
@login_required
def eliminar_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)
    negocio.activo = False
    negocio.save()
    messages.success(request, "Negocio eliminado correctamente.")
    return redirect('mis_negocios')

@require_POST
@login_required
def restaurar_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user, activo=False)
    negocio.activo = True
    negocio.save()
    messages.success(request, f"El negocio '{negocio.nombre}' ha sido restaurado.")
    return redirect('mis_negocios')



@login_required
def configurar_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)

    if request.method == 'POST':
        form = NegocioForm(request.POST, request.FILES, instance=negocio)
        if form.is_valid():
            form.save()
            messages.success(request, "Negocio actualizado.")
            return redirect('configurar_negocio', negocio_id=negocio.id)
    else:
        form = NegocioForm(instance=negocio)

    return render(request, 'negocios/configurar_negocio.html', {'form': form, 'negocio': negocio})



@login_required
def panel_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)

    if request.method == 'POST' and 'logo' in request.FILES:
        negocio.logo = request.FILES['logo']
        negocio.save()
        messages.success(request, "Logo actualizado correctamente.")
        return redirect('panel_negocio', negocio_id=negocio.id)

    peluqueros = negocio.peluqueros.filter(activo=True)
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    horario_guardado = {}
    for dia in dias:
        base = negocio.horario_atencion.get(dia, {})
        horario_guardado[f"{dia}_inicio"] = base.get("inicio", "")
        horario_guardado[f"{dia}_fin"] = base.get("fin", "")
        horario_guardado[f"{dia}_activo"] = bool(base)

    return render(request, 'negocios/panel_negocio.html', {
        'negocio': negocio,
        'peluqueros': peluqueros,
        'dias': dias,
        'horario_guardado': horario_guardado,
    })



@login_required
def crear_peluquero(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)

    #if negocio.peluqueros.exists():
    #    messages.info(request, "Este negocio ya tiene un peluquero asignado.")
    #    return redirect('panel_negocio', negocio_id=negocio.id)

    Peluquero.objects.create(
        negocio=negocio,
        nombre="Peluquero Default",
        horario="Lunes a Viernes de 9am a 6pm"
    )

    messages.success(request, "Peluquero creado correctamente.")
    return redirect('panel_negocio', negocio_id=negocio.id)


from .models import Peluquero

@login_required
def detalle_peluquero(request, negocio_id, peluquero_id):
    peluquero = get_object_or_404(Peluquero, id=peluquero_id, negocio_id=negocio_id, negocio__propietario=request.user)

    if request.method == 'POST':
        if 'nueva_imagen' in request.POST:
            form_imagen = ImagenGaleriaForm(request.POST, request.FILES)
            if form_imagen.is_valid():
                nueva = form_imagen.save(commit=False)
                nueva.peluquero = peluquero
                nueva.save()
                messages.success(request, "Imagen agregada a la galería.")
                return redirect('detalle_peluquero', negocio_id=negocio_id, peluquero_id=peluquero_id)
        else:
            form = PeluqueroForm(request.POST, request.FILES, instance=peluquero)
            if form.is_valid():
                form.save()
                messages.success(request, "Peluquero actualizado correctamente.")
                return redirect('detalle_peluquero', negocio_id=negocio_id, peluquero_id=peluquero_id)
    else:
        form = PeluqueroForm(instance=peluquero)
        form_imagen = ImagenGaleriaForm()

    return render(request, 'negocios/detalle_peluquero.html', {
        'peluquero': peluquero,
        'form': form,
        'form_imagen': form_imagen,
    })




from django.views.decorators.http import require_POST

@login_required
def eliminar_peluquero(request, negocio_id, peluquero_id):
    peluquero = get_object_or_404(Peluquero, id=peluquero_id, negocio_id=negocio_id, negocio__propietario=request.user)

    if request.method == 'POST':
        confirmar = request.POST.get('confirmar')
        if confirmar == 'SI':
            peluquero.activo = False
            peluquero.save()
            messages.success(request, "Peluquero desactivado correctamente.")
            return redirect('panel_negocio', negocio_id=negocio_id)
        else:
            messages.info(request, "Operación cancelada.")
            return redirect('panel_negocio', negocio_id=negocio_id)

    return render(request, 'negocios/confirmar_eliminacion_peluquero.html', {
        'peluquero': peluquero,
        'negocio_id': negocio_id
    })  
    
import holidays

def festivos_colombia():
    co_holidays = holidays.CountryHoliday('CO')
    return [date for date in co_holidays]


@require_POST
@login_required
def asignar_horario_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, id=negocio_id, propietario=request.user)

    dias_activos = request.POST.getlist('dias_activos')
    horarios = {}

    for dia in dias_activos:
        inicio = request.POST.get(f'inicio_{dia}')
        fin = request.POST.get(f'fin_{dia}')
        if inicio and fin:
            horarios[dia] = {'inicio': inicio, 'fin': fin}

    # Suponiendo que tienes un campo JSON o TextField en el modelo para almacenar esto:
    negocio.horario_atencion = horarios
    negocio.save()

    messages.success(request, "Horario asignado correctamente.")
    return redirect('panel_negocio', negocio_id=negocio.id)



def perfil_peluquero(request, id):
    peluquero = get_object_or_404(Peluquero, id=id)
    
    if request.method == 'POST' and 'nueva_imagen' in request.POST:
        form_imagen = ImagenGaleriaForm(request.POST, request.FILES)
        if form_imagen.is_valid():
            nueva = form_imagen.save(commit=False)
            nueva.peluquero = peluquero
            nueva.save()
            return redirect(request.path_info)
    else:
        form_imagen = ImagenGaleriaForm()

    return render(request, 'tu_template.html', {
        'peluquero': peluquero,
        'form_imagen': form_imagen,
        # otros contextos
    })


@login_required
def api_turnos_peluquero(request, peluquero_id):
    peluquero = get_object_or_404(Peluquero, id=peluquero_id, negocio__propietario=request.user)
    
    # Simulación: generar horarios libres de lunes a viernes, 9am a 6pm, cada 1 hora
    eventos = []
    base_date = datetime.today()
    for i in range(0, 7):
        dia = base_date + timedelta(days=i)
        if dia.weekday() < 5:  # solo lunes a viernes
            for hora in range(9, 17):
                eventos.append({
                    "title": "Disponible",
                    "start": dia.replace(hour=hora, minute=0, second=0).isoformat(),
                    "end": dia.replace(hour=hora+1, minute=0, second=0).isoformat(),
                    "color": "#198754"  # verde
                })

    return JsonResponse(eventos, safe=False)