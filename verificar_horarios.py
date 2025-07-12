#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melissa.settings')
django.setup()

from profesionales.models import Profesional, HorarioProfesional
from datetime import datetime, date
from datetime import time

def verificar_horarios_profesional():
    print("=== VERIFICACIÓN DE HORARIOS DEL PROFESIONAL ===")
    
    # Buscar el profesional con ID 604 (del error)
    try:
        profesional = Profesional.objects.get(id=604)
        print(f"✅ Profesional encontrado: {profesional.nombre_completo}")
    except Profesional.DoesNotExist:
        print("❌ Profesional con ID 604 no encontrado")
        return
    
    # Verificar horarios del profesional
    horarios = HorarioProfesional.objects.filter(profesional=profesional)
    print(f"\n📅 Horarios configurados para {profesional.nombre_completo}:")
    
    if not horarios.exists():
        print("❌ NO HAY HORARIOS CONFIGURADOS")
        print("   El profesional necesita tener horarios configurados para poder recibir reservas.")
        return
    
    for horario in horarios:
        print(f"   {horario.get_dia_semana_display()}: {horario.hora_inicio} - {horario.hora_fin} ({'Disponible' if horario.disponible else 'No disponible'})")
    
    # Verificar específicamente el jueves
    jueves = HorarioProfesional.objects.filter(profesional=profesional, dia_semana='jueves', disponible=True).first()
    if jueves:
        print(f"\n✅ Jueves configurado: {jueves.hora_inicio} - {jueves.hora_fin}")
    else:
        print(f"\n❌ Jueves NO configurado o no disponible")
    
    # Verificar la fecha del error (2025-07-24 es jueves)
    fecha_error = date(2025, 7, 24)
    dia_semana = fecha_error.strftime('%A').lower()
    print(f"\n📅 Fecha del error: {fecha_error} ({dia_semana})")
    
    # Verificar horario para ese día específico
    horario_dia = HorarioProfesional.objects.filter(
        profesional=profesional, 
        dia_semana='jueves', 
        disponible=True
    ).first()
    
    if horario_dia:
        print(f"✅ Horario para jueves: {horario_dia.hora_inicio} - {horario_dia.hora_fin}")
        
        # Verificar si la hora 10:00 está dentro del horario
        hora_intento = time(10, 0)
        if horario_dia.hora_inicio <= hora_intento < horario_dia.hora_fin:
            print(f"✅ Hora 10:00 está dentro del horario")
        else:
            print(f"❌ Hora 10:00 NO está dentro del horario ({horario_dia.hora_inicio} - {horario_dia.hora_fin})")
    else:
        print(f"❌ No hay horario configurado para jueves")

if __name__ == "__main__":
    verificar_horarios_profesional() 