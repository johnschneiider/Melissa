import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melissa.settings')
django.setup()

from profesionales.models import Profesional, HorarioProfesional
from datetime import date, time

print("=== DIAGNÓSTICO DEL PROBLEMA DE RESERVAS ===")

# Verificar profesional 604
try:
    profesional = Profesional.objects.get(id=604)
    print(f"✅ Profesional encontrado: {profesional.nombre_completo}")
except Profesional.DoesNotExist:
    print("❌ Profesional 604 no encontrado")
    exit()

# Verificar horarios
horarios = HorarioProfesional.objects.filter(profesional=profesional)
print(f"\n📅 Horarios configurados:")
if horarios.exists():
    for h in horarios:
        print(f"   {h.dia_semana}: {h.hora_inicio} - {h.hora_fin} (disponible: {h.disponible})")
else:
    print("   ❌ NO HAY HORARIOS CONFIGURADOS")

# Verificar jueves específicamente
jueves = HorarioProfesional.objects.filter(profesional=profesional, dia_semana='jueves', disponible=True).first()
if jueves:
    print(f"\n✅ Jueves configurado: {jueves.hora_inicio} - {jueves.hora_fin}")
    hora_10 = time(10, 0)
    if jueves.hora_inicio <= hora_10 < jueves.hora_fin:
        print(f"✅ Hora 10:00 está dentro del horario")
    else:
        print(f"❌ Hora 10:00 NO está dentro del horario")
else:
    print(f"\n❌ Jueves NO configurado o no disponible")

print("\n=== FIN DIAGNÓSTICO ===") 