#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, time, timedelta, date
import random
import string

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melissa.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from clientes.models import Reserva
from negocios.models import Negocio, ServicioNegocio, Servicio
from profesionales.models import Profesional, Matriculacion
from clientes.forms import ReservaForm

Usuario = get_user_model()

def random_username(prefix):
    return prefix + '_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def random_service_name():
    return 'Corte de cabello ' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

def test_reserva():
    print("=== TEST RESERVA ===")
    
    # Crear datos de prueba
    try:
        # Crear usuario cliente
        cliente = Usuario.objects.create_user(
            username=random_username('cliente_test'),
            email=f"cliente{random.randint(1, 100000)}@test.com",
            password='testpass123',
            tipo='cliente'
        )
        print(f"✅ Cliente creado: {cliente}")
        
        # Crear negocio
        negocio = Negocio.objects.create(
            nombre='Peluquería Test',
            direccion='Calle Test 123',
            ciudad='Bogotá',
            barrio='Chapinero',
            propietario=cliente,
            activo=True
        )
        print(f"✅ Negocio creado: {negocio}")
        
        # Crear servicio
        servicio = Servicio.objects.create(
            nombre=random_service_name(),
            descripcion='Corte básico'
        )
        print(f"✅ Servicio creado: {servicio}")
        
        # Crear servicio del negocio
        servicio_negocio = ServicioNegocio.objects.create(
            negocio=negocio,
            servicio=servicio,
            duracion=30,
            precio=25000,
            activo=True
        )
        print(f"✅ ServicioNegocio creado: {servicio_negocio}")
        
        # Crear usuario para el profesional
        usuario_profesional = Usuario.objects.create_user(
            username=random_username('pro_ana'),
            email=f"pro_ana{random.randint(1, 100000)}@test.com",
            password='testpass123',
            tipo='profesional'
        )
        # Crear profesional
        profesional = Profesional.objects.create(
            usuario=usuario_profesional,
            nombre_completo='Ana García',
            especialidad='Cortes y coloración'
        )
        print(f"✅ Profesional creado: {profesional}")
        
        # Crear matriculación
        matricula = Matriculacion.objects.create(
            profesional=profesional,
            negocio=negocio,
            estado='aprobada'
        )
        print(f"✅ Matriculación creada: {matricula}")
        
        # Intentar crear una reserva de prueba
        reserva = Reserva(
            cliente=cliente,
            peluquero=negocio,
            profesional=profesional,
            fecha=date.today() + timedelta(days=1),
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            servicio=servicio_negocio,
            estado='pendiente',
            notas='Reserva de prueba'
        )
        
        print(f"✅ Objeto Reserva creado: {reserva}")
        print(f"   - cliente_id: {reserva.cliente.id}")
        print(f"   - peluquero_id: {reserva.peluquero.id}")
        print(f"   - profesional_id: {reserva.profesional.id}")
        print(f"   - servicio_id: {reserva.servicio.id}")
        
        reserva.save()
        print("✅ Reserva guardada exitosamente!")
        
        # Limpiar datos de prueba
        reserva.delete()
        print("✅ Reserva de prueba eliminada")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_validacion_solapamiento():
    print("\n=== TEST VALIDACIÓN SOLAPAMIENTO ===")
    
    try:
        # Crear datos de prueba
        cliente = Usuario.objects.create_user(
            username=random_username('cliente_solapamiento'),
            email=f"cliente_solapamiento{random.randint(1, 100000)}@test.com",
            password='testpass123',
            tipo='cliente'
        )
        
        negocio = Negocio.objects.create(
            nombre='Peluquería Solapamiento',
            direccion='Calle Test 456',
            ciudad='Bogotá',
            barrio='Chapinero',
            propietario=cliente,
            activo=True
        )
        
        servicio = Servicio.objects.create(
            nombre=random_service_name(),
            descripcion='Corte básico'
        )
        
        servicio_negocio = ServicioNegocio.objects.create(
            negocio=negocio,
            servicio=servicio,
            duracion=30,
            precio=25000,
            activo=True
        )
        
        # Crear usuario para el profesional
        usuario_profesional = Usuario.objects.create_user(
            username=random_username('pro_carlos'),
            email=f"pro_carlos{random.randint(1, 100000)}@test.com",
            password='testpass123',
            tipo='profesional'
        )
        profesional = Profesional.objects.create(
            usuario=usuario_profesional,
            nombre_completo='Carlos López',
            especialidad='Cortes y coloración'
        )
        
        Matriculacion.objects.create(
            profesional=profesional,
            negocio=negocio,
            estado='aprobada'
        )
        
        # Crear primera reserva
        fecha_reserva = date.today() + timedelta(days=1)
        reserva1 = Reserva.objects.create(
            cliente=cliente,
            peluquero=negocio,
            profesional=profesional,
            fecha=fecha_reserva,
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            servicio=servicio_negocio,
            estado='pendiente'
        )
        print(f"✅ Primera reserva creada: {reserva1.hora_inicio} - {reserva1.hora_fin}")
        
        # Intentar crear segunda reserva que se solape
        form_data = {
            'fecha': fecha_reserva,
            'hora_inicio': time(10, 15),  # Se solapa con la primera
            'servicio': servicio_negocio.id,
            'profesional': profesional.id,
            'notas': 'Reserva que se solapa'
        }
        
        form = ReservaForm(data=form_data, negocio=negocio)
        is_valid = form.is_valid()
        
        if not is_valid:
            print("✅ Validación funcionó correctamente - Formulario rechazado por solapamiento")
            print(f"   Errores: {form.errors}")
        else:
            print("❌ ERROR: El formulario debería haber sido rechazado por solapamiento")
        
        # Intentar crear tercera reserva que NO se solape
        form_data2 = {
            'fecha': fecha_reserva,
            'hora_inicio': time(11, 0),  # No se solapa
            'servicio': servicio_negocio.id,
            'profesional': profesional.id,
            'notas': 'Reserva que NO se solapa'
        }
        
        form2 = ReservaForm(data=form_data2, negocio=negocio)
        is_valid2 = form2.is_valid()
        
        if is_valid2:
            print("✅ Validación funcionó correctamente - Formulario aceptado (sin solapamiento)")
        else:
            print(f"❌ ERROR: El formulario debería haber sido aceptado. Errores: {form2.errors}")
        
        # Limpiar
        reserva1.delete()
        print("✅ Datos de prueba eliminados")
        
    except Exception as e:
        print(f"❌ Error en test de solapamiento: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_reserva()
    test_validacion_solapamiento() 