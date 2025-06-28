from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.utils import timezone
from datetime import timedelta, datetime, time
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from negocios.models import Negocio, Peluquero, ImagenGaleria
from .models import Reserva
from .forms import ReservaForm
import json
import holidays

class ListaNegociosView(ListView):
    model = Negocio
    template_name = 'clientes/lista_negocios.html'
    context_object_name = 'negocios'
    
    def get_queryset(self):
        return Negocio.objects.filter(activo=True).prefetch_related('peluqueros')

class DetallePeluqueroView(DetailView):
    model = Peluquero
    template_name = 'clientes/detalle_peluquero.html'
    context_object_name = 'peluquero'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        peluquero = self.object
        
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
            
            # Obtener horario del peluquero para este día
            horario_peluquero = peluquero.horario.get(nombre_dia_es, {})
            turnos = horario_peluquero.get('turnos', [])
            
            # Verificar reservas existentes para este día
            reservas_dia = Reserva.objects.filter(
                peluquero=peluquero,
                fecha=dia,
                estado__in=['pendiente', 'confirmado']
            ).values_list('hora_inicio', 'hora_fin')
            
            # Calcular intervalos disponibles
            intervalos_disponibles = []
            for turno in turnos:
                if turno.get('disponible', True) and not es_festivo:
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
            
            dias_disponibilidad.append({
                'fecha': dia,
                'nombre_dia': nombre_dia_es,
                'festivo': es_festivo,
                'intervalos': intervalos_disponibles
            })
        
        context['dias_disponibilidad'] = dias_disponibilidad
        context['galeria'] = ImagenGaleria.objects.filter(peluquero=peluquero)
        context['hoy'] = hoy
        
        return context

from django.utils import timezone

@login_required
def reservar_turno(request, peluquero_id):
    peluquero = get_object_or_404(Peluquero, id=peluquero_id, negocio__activo=True)
    
    if request.method == 'POST':
        form = ReservaForm(request.POST, peluquero=peluquero)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.cliente = request.user
            reserva.peluquero = peluquero
            
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
            messages.success(request, '¡Reserva realizada con éxito!')
            return redirect('clientes:confirmacion_reserva', reserva_id=reserva.id) 
    else:
        form = ReservaForm(peluquero=peluquero)
    
    return render(request, 'clientes/reservar_turno.html', {
        'peluquero': peluquero,
        'form': form
    })
    
def confirmacion_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, cliente=request.user)
    return render(request, 'clientes/confirmacion_reserva.html', {'reserva': reserva})

def horarios_disponibles(request, peluquero_id):
    peluquero = get_object_or_404(Peluquero, id=peluquero_id)
    fecha = request.GET.get('fecha')
    
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
    
    # Obtener horario del peluquero para este día
    horario_peluquero = peluquero.horario.get(nombre_dia_es, {})
    turnos = horario_peluquero.get('turnos', [])
    
    # Obtener reservas existentes para este día
    reservas = Reserva.objects.filter(
        peluquero=peluquero,
        fecha=fecha_obj,
        estado__in=['pendiente', 'confirmado']
    ).values_list('hora_inicio', 'hora_fin')
    
    # Calcular horarios disponibles
    horarios_disponibles = []
    for turno in turnos:
        if turno.get('disponible', True):
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
                
                # Verificar disponibilidad
                disponible = True
                for reserva_inicio, reserva_fin in reservas:
                    if not (hora_fin <= reserva_inicio or hora_inicio >= reserva_fin):
                        disponible = False
                        break
                
                if disponible:
                    horarios_disponibles.append({
                        'hora': hora_inicio.strftime('%H:%M'),
                        'duracion': duracion
                    })
                
                tiempo_actual += duracion
    
    return JsonResponse({'disponibles': horarios_disponibles, 'festivo': False})