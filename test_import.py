#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melissa.settings')
django.setup()

# Probar la importación
try:
    from profesionales.models import Notificacion
    print("✅ Importación exitosa de Notificacion desde profesionales.models")
    
    # Verificar que el tipo 'dia_descanso' está disponible
    tipos_disponibles = [choice[0] for choice in Notificacion.TIPO_CHOICES]
    if 'dia_descanso' in tipos_disponibles:
        print("✅ Tipo 'dia_descanso' disponible en Notificacion")
    else:
        print("❌ Tipo 'dia_descanso' NO disponible en Notificacion")
        print(f"Tipos disponibles: {tipos_disponibles}")
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")

print("Prueba completada") 