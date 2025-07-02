from django.db import models
from negocios.models import Negocio, ServicioNegocio
from django.conf import settings
from django.utils import timezone

class Reserva(models.Model):
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas_cliente')
    peluquero = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='reservas_peluquero')
    profesional = models.ForeignKey('profesionales.Profesional', on_delete=models.CASCADE, null=True, blank=True, related_name='reservas_profesional')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    servicio = models.ForeignKey(ServicioNegocio, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas_servicio')
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

class MetricaCliente(models.Model):
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='metricas_cliente')
    fecha = models.DateField()
    total_turnos = models.IntegerField(default=0)
    turnos_completados = models.IntegerField(default=0)
    turnos_cancelados = models.IntegerField(default=0)
    servicios_mas_solicitados = models.CharField(max_length=200, blank=True)
    profesionales_mas_reservados = models.CharField(max_length=200, blank=True)
    class Meta:
        unique_together = ['cliente', 'fecha']
        ordering = ['-fecha']
    def __str__(self):
        return f"{str(self.cliente)} - {self.fecha}"

class NotificacionCliente(models.Model):
    TIPO_CHOICES = (
        ('reserva', 'Nueva Reserva'),
        ('sistema', 'Notificación del Sistema'),
    )
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones_cliente')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    url_relacionada = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Notificación Cliente'
        verbose_name_plural = 'Notificaciones Cliente'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{str(self.cliente)} - {self.titulo}"

    def marcar_como_leida(self):
        self.leida = True
        self.fecha_lectura = timezone.now()
        self.save()