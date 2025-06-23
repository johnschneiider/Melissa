from django.contrib.auth.models import AbstractUser
from django.db import models

class UsuarioPersonalizado(AbstractUser):
    TIPO_USUARIO = (
        ('cliente', 'Cliente'),
        ('negocio', 'Negocio'),
    )
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO)
    telefono = models.CharField(max_length=15, blank=True) 
