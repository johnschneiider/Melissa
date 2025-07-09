from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Negocio, ServicioNegocio, Servicio

User = get_user_model()

class NegocioServicioTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_negocio = User.objects.create_user(username='negocio1', password='test1234', tipo='negocio')
        self.client.login(username='negocio1', password='test1234')

    def test_crear_negocio(self):
        response = self.client.post(reverse('negocios:crear_negocio'), {
            'nombre': 'Negocio Test',
            'direccion': 'Calle 123',
            'ciudad': 'Ciudad Test',
            'barrio': 'Barrio Test',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Negocio.objects.filter(nombre='Negocio Test').exists())

    def test_editar_negocio(self):
        negocio = Negocio.objects.create(nombre='Negocio Edit', direccion='Calle 1', propietario=self.user_negocio)
        response = self.client.post(reverse('negocios:editar_negocio', args=[negocio.id]), {
            'nombre': 'Negocio Editado',
            'direccion': 'Calle 2',
            'ciudad': 'Ciudad Editada',
            'barrio': 'Barrio Editado',
        })
        self.assertEqual(response.status_code, 302)
        negocio.refresh_from_db()
        self.assertEqual(negocio.nombre, 'Negocio Editado')
        self.assertEqual(negocio.direccion, 'Calle 2')

    def test_crear_servicio(self):
        negocio = Negocio.objects.create(
            nombre='Negocio Test',
            direccion='Calle 123',
            ciudad='Ciudad Test',
            barrio='Barrio Test',
            propietario=self.user_negocio
        )
        servicio = Servicio.objects.create(nombre='Corte', descripcion='Corte básico')
        
        response = self.client.post(reverse('negocios:gestionar_servicios', args=[negocio.id]), {
            'form-0-servicio': servicio.id,
            'form-0-duracion': 30,
            'form-0-precio': '150.00',
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ServicioNegocio.objects.filter(negocio=negocio, servicio=servicio).exists())

    def test_editar_servicio(self):
        negocio = Negocio.objects.create(
            nombre='Negocio Test',
            direccion='Calle 123',
            ciudad='Ciudad Test',
            barrio='Barrio Test',
            propietario=self.user_negocio
        )
        servicio = Servicio.objects.create(nombre='Color', descripcion='Coloración')
        servicio_negocio = ServicioNegocio.objects.create(
            negocio=negocio,
            servicio=servicio,
            duracion=60,
            precio=100.00,
            activo=True
        )
        
        response = self.client.post(reverse('negocios:gestionar_servicios', args=[negocio.id]), {
            'form-0-id': servicio_negocio.id,
            'form-0-servicio': servicio.id,
            'form-0-duracion': 90,
            'form-0-precio': '200.00',
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        })
        self.assertEqual(response.status_code, 302)
        servicio_negocio.refresh_from_db()
        self.assertEqual(float(servicio_negocio.precio), 200.00)
