from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import JSONField
import os
import json

class Negocio(models.Model):
    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='negocios')
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    logo = models.ImageField(upload_to='logos_negocios/', blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    horario_atencion = models.JSONField(default=dict, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre


Usuario = get_user_model()
class Peluquero(models.Model):
    negocio = models.ForeignKey('Negocio', on_delete=models.CASCADE, related_name='peluqueros')
    nombre = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to="peluqueros/", blank=True, null=True)
    portada = models.ImageField(upload_to="portadas_peluqueros/", blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    horario = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    def clean_horario(self):
        """Validar y limpiar la estructura del horario"""
        if isinstance(self.horario, str):
            try:
                self.horario = json.loads(self.horario)
            except json.JSONDecodeError:
                self.horario = {}
        
        if not isinstance(self.horario, dict):
            self.horario = {}
        
        # Estructura básica para días de la semana
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        horario_validado = {}
        
        for dia in dias_semana:
            if dia in self.horario and isinstance(self.horario[dia], dict):
                turnos_validados = []
                for turno in self.horario[dia].get('turnos', []):
                    if all(key in turno for key in ['inicio', 'fin', 'duracion']):
                        turnos_validados.append({
                            'inicio': turno['inicio'],
                            'fin': turno['fin'],
                            'duracion': int(turno['duracion']),
                            'disponible': turno.get('disponible', True)
                        })
                horario_validado[dia] = {'turnos': turnos_validados}
        
        return horario_validado

    def save(self, *args, **kwargs):
        self.horario = self.clean_horario()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
    
class ImagenPeluquero(models.Model):
    peluquero = models.ForeignKey(Peluquero, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='cortes/')
    nombre = models.CharField(max_length=100, blank=True)  # Nombre del corte
    descripcion = models.TextField(blank=True)
    duracion = models.PositiveIntegerField(default=30)  # minutos

    def __str__(self):
        return self.nombre or "Corte sin nombre"


# models.py

class ImagenGaleria(models.Model):
    peluquero = models.ForeignKey(
        Peluquero,
        on_delete=models.CASCADE,
        related_name='galeria'
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    duracion = models.PositiveIntegerField(default=30)
    imagen = models.ImageField(upload_to='galeria/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre or "Corte sin nombre"

