from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Conversacion, Mensaje

User = get_user_model()

class MensajesNoLeidosAPITest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass1')
        self.user2 = User.objects.create_user(username='user2', password='pass2')
        self.conversacion = Conversacion.objects.create(participante1=self.user1, participante2=self.user2)
        # Mensajes de user2 a user1 (no leídos)
        for i in range(3):
            Mensaje.objects.create(conversacion=self.conversacion, remitente=self.user2, texto=f"Hola {i}")
        # Mensajes de user1 a user2 (no cuentan como no leídos para user1)
        for i in range(2):
            Mensaje.objects.create(conversacion=self.conversacion, remitente=self.user1, texto=f"Hey {i}")

    def test_api_mensajes_no_leidos(self):
        self.client.login(username='user1', password='pass1')
        url = reverse('chat:api_mensajes_no_leidos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('no_leidos', data)
        self.assertEqual(data['no_leidos'], 3)

    def test_api_mensajes_no_leidos_0(self):
        self.client.login(username='user2', password='pass2')
        url = reverse('chat:api_mensajes_no_leidos')
        response = self.client.get(url)
        data = response.json()
        # user2 tiene 2 mensajes no leídos de user1
        self.assertEqual(data['no_leidos'], 2)

    def test_api_mensajes_no_leidos_marca_leido(self):
        # Marcar uno como leído
        mensaje = Mensaje.objects.filter(remitente=self.user2).first()
        mensaje.leido = True
        mensaje.save()
        self.client.login(username='user1', password='pass1')
        url = reverse('chat:api_mensajes_no_leidos')
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(data['no_leidos'], 2)
