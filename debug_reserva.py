#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melissa.settings')
django.setup()

from profesionales.models import Profesional, HorarioProfesional, Matriculacion
from negocios.models import Negocio, ServicioNegocio
from datetime import datetime, date, timedelta, time

def debug_reserva():
    print("=== DEBUG RESERVA ===")
    
    # Buscar profesional "prof4"
    profesional = Profesional.objects.filter(nombre_completo__icontains='prof4').first()
    if not profesional:
        print("❌ Profesional 'prof4' no encontrado")
        return
    
    print(f"✅ Profesional encontrado: {profesional.nombre_completo}")
    
    # Buscar negocio "Barber 44"
    negocio = Negocio.objects.filter(nombre__icontains='Barber 44').first()
    if not negocio:
        print("❌ Negocio 'Barber 44' no encontrado")
        return
    
    print(f"✅ Negocio encontrado: {negocio.nombre}")
    
    # Verificar matriculación
    matriculacion = Matriculacion.objects.filter(profesional=profesional, negocio=negocio).first()
    if not matriculacion:
        print("❌ No hay matriculación entre el profesional y el negocio")
        return
    
    print(f"✅ Matriculación: {matriculacion.estado}")
    
    if matriculacion.estado != 'aprobada':
        print("❌ La matriculación no está aprobada")
        return
    
    # Verificar servicios del negocio
    servicios_negocio = ServicioNegocio.objects.filter(negocio=negocio)
    print(f"✅ Servicios del negocio: {servicios_negocio.count()}")
    for sn in servicios_negocio:
        print(f"   - {sn.servicio.nombre} (duración: {sn.duracion} min)")
    
    # Verificar servicios asignados al profesional
    servicios_profesional = profesional.servicios.all()
    print(f"✅ Servicios del profesional: {servicios_profesional.count()}")
    for s in servicios_profesional:
        print(f"   - {s.nombre}")
    
    # Verificar horarios del profesional
    horarios = HorarioProfesional.objects.filter(profesional=profesional)
    print(f"✅ Horarios del profesional: {horarios.count()}")
    for h in horarios:
        print(f"   - {h.dia_semana}: {h.hora_inicio} - {h.hora_fin} (disponible: {h.disponible})")
    
    # Probar con una fecha específica (mañana)
    tomorrow = date.today() + timedelta(days=1)
    nombre_dia = tomorrow.strftime('%A')
    nombre_dia_es = {
        'Monday': 'lunes',
        'Tuesday': 'martes',
        'Wednesday': 'miercoles',
        'Thursday': 'jueves',
        'Friday': 'viernes',
        'Saturday': 'sabado',
        'Sunday': 'domingo'
    }.get(nombre_dia, nombre_dia)
    
    print(f"\n=== PRUEBA CON FECHA {tomorrow} ({nombre_dia_es}) ===")
    
    horario_mañana = HorarioProfesional.objects.filter(
        profesional=profesional, 
        dia_semana=nombre_dia_es, 
        disponible=True
    ).first()
    
    if horario_mañana:
        print(f"✅ Horario para mañana: {horario_mañana.hora_inicio} - {horario_mañana.hora_fin}")
        
        # Simular generación de slots
        inicio = horario_mañana.hora_inicio
        fin = horario_mañana.hora_fin
        duracion_turno = 30  # 30 minutos por defecto
        
        inicio_minutos = inicio.hour * 60 + inicio.minute
        fin_minutos = fin.hour * 60 + fin.minute
        tiempo_actual = inicio_minutos
        
        slots = []
        while tiempo_actual + duracion_turno <= fin_minutos:
            hora_inicio = time(tiempo_actual // 60, tiempo_actual % 60)
            hora_fin = time((tiempo_actual + duracion_turno) // 60, (tiempo_actual + duracion_turno) % 60)
            slots.append(f"{hora_inicio.strftime('%H:%M')} - {hora_fin.strftime('%H:%M')}")
            tiempo_actual += duracion_turno
        
        print(f"✅ Slots generados: {len(slots)}")
        for slot in slots:
            print(f"   - {slot}")
    else:
        print(f"❌ No hay horario configurado para {nombre_dia_es}")

if __name__ == '__main__':
    debug_reserva() 