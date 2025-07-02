#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melissa.settings')
django.setup()

from clientes.models import Reserva
from negocios.models import Negocio, ServicioNegocio
from profesionales.models import Profesional
from django.contrib.auth import get_user_model
from datetime import date, time

User = get_user_model()

def test_reserva():
    print("=== TEST RESERVA ===")
    
    try:
        # Buscar datos de prueba
        cliente = User.objects.filter(tipo='cliente').first()
        if not cliente:
            print("❌ No hay usuarios tipo cliente")
            return
        
        negocio = Negocio.objects.filter(activo=True).first()
        if not negocio:
            print("❌ No hay negocios activos")
            return
        
        profesional = Profesional.objects.first()
        if not profesional:
            print("❌ No hay profesionales")
            return
        
        servicio_negocio = ServicioNegocio.objects.filter(negocio=negocio).first()
        if not servicio_negocio:
            print("❌ No hay servicios en el negocio")
            return
        
        print(f"✅ Cliente: {cliente.username}")
        print(f"✅ Negocio: {negocio.nombre}")
        print(f"✅ Profesional: {profesional.nombre_completo}")
        print(f"✅ Servicio: {servicio_negocio.servicio.nombre}")
        
        # Intentar crear una reserva de prueba
        reserva = Reserva(
            cliente=cliente,
            peluquero=negocio,
            profesional=profesional,
            fecha=date.today(),
            hora_inicio=time(10, 0),  # 10:00
            hora_fin=time(10, 30),    # 10:30
            servicio=servicio_negocio,
            estado='pendiente',
            notas='Reserva de prueba'
        )
        
        print(f"✅ Objeto Reserva creado: {reserva}")
        print(f"   - cliente_id: {reserva.cliente.id}")
        print(f"   - peluquero_id: {reserva.peluquero.id}")
        print(f"   - profesional_id: {reserva.profesional.id}")
        print(f"   - servicio_id: {reserva.servicio.id}")
        
        # Intentar guardar
        reserva.save()
        print("✅ Reserva guardada exitosamente!")
        
        # Limpiar
        reserva.delete()
        print("✅ Reserva de prueba eliminada")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_reserva() 