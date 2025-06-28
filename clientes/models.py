from django.db import models
from negocios.models import Negocio, Peluquero
from django.conf import settings

class Reserva(models.Model):
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    peluquero = models.ForeignKey(Peluquero, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    servicio = models.ForeignKey('negocios.ImagenGaleria', on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
        ('completado', 'Completado'),
    ], default='pendiente')
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f"Reserva de {self.cliente} con {self.peluquero} el {self.fecha} a las {self.hora_inicio}"