from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import JSONField
import os
import json
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone

class Servicio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

class Negocio(models.Model):
    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='negocios')
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    barrio = models.CharField(max_length=100, blank=True, null=True)
    latitud = models.FloatField(blank=True, null=True)
    longitud = models.FloatField(blank=True, null=True)
    logo = models.ImageField(upload_to='logos_negocios/', blank=True, null=True)
    portada = models.ImageField(upload_to='portadas_negocios/', blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    horario_atencion = models.JSONField(default=dict, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre


Usuario = get_user_model()

class MetricaNegocio(models.Model):
    """Modelo para almacenar métricas diarias del negocio"""
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='metricas')
    fecha = models.DateField()
    
    # Métricas de reservas
    total_reservas = models.IntegerField(default=0)
    reservas_completadas = models.IntegerField(default=0)
    reservas_canceladas = models.IntegerField(default=0)
    reservas_no_show = models.IntegerField(default=0)
    
    # Métricas financieras
    ingresos_totales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promedio_ticket = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Métricas de clientes
    clientes_nuevos = models.IntegerField(default=0)
    clientes_recurrentes = models.IntegerField(default=0)
    
    # El campo 'peluqueros_activos' ha sido eliminado
    horas_trabajadas = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['negocio', 'fecha']
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.negocio.nombre} - {self.fecha}"

class ReporteMensual(models.Model):
    """Modelo para reportes mensuales consolidados"""
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='reportes_mensuales')
    año = models.IntegerField()
    mes = models.IntegerField()
    
    # Resumen mensual
    total_reservas = models.IntegerField(default=0)
    reservas_completadas = models.IntegerField(default=0)
    ingresos_totales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    promedio_ticket = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Métricas de clientes
    clientes_unicos = models.IntegerField(default=0)
    clientes_nuevos = models.IntegerField(default=0)
    tasa_retencion = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Porcentaje
    
    # Días más ocupados
    dia_mas_ocupado = models.CharField(max_length=20, blank=True)
    hora_pico = models.CharField(max_length=10, blank=True)
    
    class Meta:
        unique_together = ['negocio', 'año', 'mes']
        ordering = ['-año', '-mes']
    
    def __str__(self):
        return f"{self.negocio.nombre} - {self.año}/{self.mes:02d}"

class ImagenNegocio(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='galeria_negocio/')
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.titulo

# Servicios iniciales fijos
SERVICIOS_FIJOS = [
    'Corte de cabello',
    'Coloración',
    'Peinado',
    'Manicura',
    'Pedicura',
    'Depilación',
    'Barbería',
    'Tratamiento capilar',
    'Maquillaje',
]

def crear_servicios_iniciales():
    for nombre in SERVICIOS_FIJOS:
        Servicio.objects.get_or_create(nombre=nombre)

# Crear servicios base automáticamente después de migraciones
@receiver(post_migrate)
def ensure_servicios_fijos(sender, **kwargs):
    if sender.name == 'negocios':
        crear_servicios_iniciales()

class ServicioNegocio(models.Model):
    negocio = models.ForeignKey('Negocio', on_delete=models.CASCADE, related_name='servicios_negocio')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    duracion = models.PositiveIntegerField(default=30, help_text='Duración en minutos')
    precio = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    activo = models.BooleanField(default=True, help_text='¿El servicio está activo/ofrecido por el negocio?')

    class Meta:
        unique_together = ('negocio', 'servicio')
        verbose_name = 'Servicio del Negocio'
        verbose_name_plural = 'Servicios del Negocio'

    def __str__(self):
        return f"{self.negocio.nombre} - {self.servicio.nombre} ({self.duracion} min)"

class NotificacionNegocio(models.Model):
    TIPO_CHOICES = (
        ('matriculacion', 'Nueva Solicitud de Matriculación'),
        ('reserva', 'Nueva Reserva'),
        ('solicitud_ausencia', 'Nueva Solicitud de Ausencia'),
        ('sistema', 'Notificación del Sistema'),
    )
    negocio = models.ForeignKey('Negocio', on_delete=models.CASCADE, related_name='notificaciones_negocio')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    url_relacionada = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Notificación Negocio'
        verbose_name_plural = 'Notificaciones Negocio'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.negocio.nombre} - {self.titulo}"

    def marcar_como_leida(self):
        self.leida = True
        self.fecha_lectura = timezone.now()
        self.save()

class DiaDescanso(models.Model):
    """Modelo para gestionar días de descanso de los negocios"""
    TIPO_CHOICES = [
        ('feriado', 'Feriado'),
        ('cierre_especial', 'Cierre Especial'),
        ('mantenimiento', 'Mantenimiento'),
        ('vacaciones', 'Vacaciones'),
        ('otro', 'Otro'),
    ]
    
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='dias_descanso')
    fecha = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='feriado')
    motivo = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['negocio', 'fecha']
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.negocio.nombre} - {self.fecha} ({self.get_tipo_display()})"
    
    def save(self, *args, **kwargs):
        # Si es un día nuevo, notificar a los profesionales
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.activo:
            self.notificar_profesionales()
    
    def notificar_profesionales(self):
        """Notificar a todos los profesionales del negocio sobre el día de descanso"""
        from profesionales.models import Notificacion, Matriculacion
        
        # Obtener profesionales matriculados y aprobados en este negocio
        matriculaciones_aprobadas = Matriculacion.objects.filter(
            negocio=self.negocio,
            estado='aprobada'
        ).select_related('profesional')
        
        for matriculacion in matriculaciones_aprobadas:
            Notificacion.objects.create(
                profesional=matriculacion.profesional,
                tipo='dia_descanso',
                titulo=f'Día de descanso programado - {self.negocio.nombre}',
                mensaje=f'El negocio {self.negocio.nombre} ha programado un día de descanso el {self.fecha} ({self.get_tipo_display()}). No se podrán realizar reservas en esa fecha.',
                url_relacionada='/profesionales/panel/',
            )

