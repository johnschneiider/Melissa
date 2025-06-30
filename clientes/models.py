from django.db import models
from negocios.models import Negocio, Servicio
from django.conf import settings

class Reserva(models.Model):
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    peluquero = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    profesional = models.ForeignKey('profesionales.Profesional', on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True, blank=True)
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
        return f"Reserva de {self.cliente} con {self.profesional or self.peluquero} el {self.fecha} a las {self.hora_inicio}"

class Calificacion(models.Model):
    negocio = models.ForeignKey('negocios.Negocio', on_delete=models.CASCADE, related_name='calificaciones')
    profesional = models.ForeignKey('profesionales.Profesional', on_delete=models.CASCADE, related_name='calificaciones')
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calificaciones')
    puntaje = models.PositiveSmallIntegerField(default=5)
    comentario = models.TextField(blank=True)
    fecha_calificacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_calificacion']
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'

    def __str__(self):
        return f"{self.negocio} - {self.profesional} - {self.puntaje}"