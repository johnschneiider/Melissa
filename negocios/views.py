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
import holidays
import json
from .forms import NegocioForm, PeluqueroForm, ImagenGaleriaForm
from .models import Negocio, Peluquero, ImagenGaleria
from datetime import datetime, timedelta, time



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
    peluquero = get_object_or_404(
        Peluquero, 
        id=peluquero_id, 
        negocio_id=negocio_id, 
        negocio__propietario=request.user
    )
    
    # Configuración de días de la semana
    DIAS_SEMANA = [
        {'nombre': 'Lunes', 'festivo': False},
        {'nombre': 'Martes', 'festivo': False},
        {'nombre': 'Miércoles', 'festivo': False},
        {'nombre': 'Jueves', 'festivo': False},
        {'nombre': 'Viernes', 'festivo': False},
        {'nombre': 'Sábado', 'festivo': False},
        {'nombre': 'Domingo', 'festivo': True}
    ]
    
    # Procesar formulario
    if request.method == 'POST':
        form = PeluqueroForm(request.POST, request.FILES, instance=peluquero)
        if form.is_valid():
            # Procesar horario
            horario_json = request.POST.get('horario_json', '{}')
            try:
                horario_data = json.loads(horario_json)
                peluquero.horario = horario_data
                form.save()
                messages.success(request, "Datos del peluquero actualizados correctamente.")
                return redirect('detalle_peluquero', negocio_id=negocio_id, peluquero_id=peluquero_id)
            except json.JSONDecodeError as e:
                messages.error(request, f"Error en el formato del horario: {str(e)}")
    else:
        form = PeluqueroForm(instance=peluquero)
    
    # Preparar datos para la plantilla
    horario_data = peluquero.horario or {}
    for dia in DIAS_SEMANA:
        dia['turnos'] = horario_data.get(dia['nombre'], {}).get('turnos', [])
    
    # Generar próxima semana con intervalos calculados
    co_holidays = holidays.CountryHoliday('CO')
    today = datetime.now().date()
    proximos_7_dias = []
    
    for delta in range(0, 7):
        fecha = today + timedelta(days=delta)
        nombre_dia = fecha.strftime('%A')
        nombre_dia_es = {
            'Monday': 'Lunes', 
            'Tuesday': 'Martes', 
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 
            'Friday': 'Viernes', 
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }.get(nombre_dia, nombre_dia)
        
        es_festivo = fecha in co_holidays or nombre_dia_es == 'Domingo'
        turnos_config = horario_data.get(nombre_dia_es, {}).get('turnos', [])
        turnos_dia = []
        
        for turno in turnos_config:
            try:
                # Parsear horas y duración
                hora_inicio = datetime.strptime(turno['inicio'], '%H:%M').time()
                hora_fin = datetime.strptime(turno['fin'], '%H:%M').time()
                duracion = int(turno.get('duracion', 30))
                
                # Calcular intervalos para este turno
                intervalos = calcular_intervalos(hora_inicio, hora_fin, duracion)
                
                turnos_dia.append({
                    'inicio': hora_inicio,
                    'fin': hora_fin,
                    'duracion': duracion,
                    'disponible': turno.get('disponible', True),
                    'intervalos': intervalos
                })
            except (ValueError, KeyError) as e:
                print(f"Error procesando turno: {e}")
                continue
        
        proximos_7_dias.append({
            'fecha': fecha,
            'nombre_dia': nombre_dia_es,
            'festivo': es_festivo,
            'turnos': turnos_dia
        })
    
    return render(request, 'negocios/detalle_peluquero.html', {
        'peluquero': peluquero,
        'form': form,
        'form_imagen': ImagenGaleriaForm(),
        'dias_semana': DIAS_SEMANA,
        'proximos_7_dias': proximos_7_dias,
        'horario_json': json.dumps(horario_data),
    })

def calcular_intervalos(inicio, fin, duracion_minutos):
    """Calcula los intervalos de tiempo basados en la duración configurada"""
    intervalos = []
    
    # Convertir a minutos desde medianoche para facilitar cálculos
    inicio_minutos = inicio.hour * 60 + inicio.minute
    fin_minutos = fin.hour * 60 + fin.minute
    
    # Validar que la duración sea positiva
    duracion_minutos = max(1, duracion_minutos)
    
    tiempo_actual = inicio_minutos
    
    while tiempo_actual + duracion_minutos <= fin_minutos:
        # Calcular hora inicio y fin para este intervalo
        h_inicio = tiempo_actual // 60
        m_inicio = tiempo_actual % 60
        h_fin = (tiempo_actual + duracion_minutos) // 60
        m_fin = (tiempo_actual + duracion_minutos) % 60
        
        # Crear objetos time para el intervalo
        inicio_intervalo = time(h_inicio, m_inicio)
        fin_intervalo = time(h_fin, m_fin)
        
        intervalos.append({
            'inicio': inicio_intervalo,
            'fin': fin_intervalo
        })
        
        # Avanzar al siguiente intervalo
        tiempo_actual += duracion_minutos
    
    return intervalos


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
    
    try:
        horario = json.loads(peluquero.horario) if peluquero.horario else {}
    except json.JSONDecodeError:
        horario = {}
    
    # Obtener días festivos
    co_holidays = holidays.CountryHoliday('CO')
    
    # Generar eventos para el calendario
    eventos = []
    base_date = datetime.today().date()
    
    # Para cada día de las próximas 4 semanas
    for delta in range(0, 28):
        fecha = base_date + timedelta(days=delta)
        dia_semana = fecha.strftime('%A')
        
        # Traducir día de la semana al español
        dias_traduccion = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes',
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        nombre_dia = dias_traduccion.get(dia_semana, dia_semana)
        
        # Verificar si es festivo
        es_festivo = fecha in co_holidays or nombre_dia == 'Domingo'
        
        # Si hay horario para este día y no es festivo
        if nombre_dia in horario and not es_festivo:
            for turno in horario[nombre_dia]['turnos']:
                try:
                    hora_inicio = datetime.strptime(turno['inicio'], '%H:%M').time()
                    hora_fin = datetime.strptime(turno['fin'], '%H:%M').time()
                    
                    start = datetime.combine(fecha, hora_inicio).isoformat()
                    end = datetime.combine(fecha, hora_fin).isoformat()
                    
                    eventos.append({
                        "title": "Disponible",
                        "start": start,
                        "end": end,
                        "color": "#28a745",  # verde
                        "extendedProps": {
                            "duracion": turno.get('duracion', 30)
                        }
                    })
                except (ValueError, KeyError):
                    continue
    
    return JsonResponse(eventos, safe=False)