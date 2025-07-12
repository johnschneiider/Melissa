from django.db import models
from negocios.models import Negocio, ServicioNegocio
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

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
    
    # Campos para recordatorios
    recordatorio_dia_enviado = models.BooleanField(default=False, help_text='Recordatorio de 1 día antes enviado')
    recordatorio_tres_horas_enviado = models.BooleanField(default=False, help_text='Recordatorio de 3 horas antes enviado')

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f"Reserva de {self.cliente} con {self.profesional or self.peluquero} el {self.fecha} a las {self.hora_inicio}"
    
    def confirmar(self, notas_adicionales=""):
        """
        Confirma una reserva pendiente
        """
        if self.estado != 'pendiente':
            raise ValidationError(f"No se puede confirmar una reserva en estado '{self.estado}'")
        
        self.estado = 'confirmado'
        if notas_adicionales:
            self.notas = f"{self.notas}\n[Confirmado] {notas_adicionales}" if self.notas else f"[Confirmado] {notas_adicionales}"
        self.save()
        
        # Crear notificación para el cliente
        self._crear_notificacion_cliente(
            'reserva',
            'Reserva Confirmada',
            f'Tu reserva del {self.fecha} a las {self.hora_inicio} ha sido confirmada.',
            '/clientes/mis_reservas/'
        )
        
        # Crear notificación para el profesional
        self._crear_notificacion_profesional(
            'reserva',
            'Reserva Confirmada',
            f'Nueva reserva confirmada para el {self.fecha} a las {self.hora_inicio} con {self.cliente.username}.',
            '/profesionales/panel/'
        )
        
        return True
    
    def cancelar(self, motivo="", cancelado_por="sistema"):
        """
        Cancela una reserva (pendiente o confirmada)
        """
        logger = logging.getLogger(__name__)
        
        logger.info(f"Intentando cancelar reserva {self.id}, estado actual: {self.estado}")
        
        if self.estado not in ['pendiente', 'confirmado']:
            error_msg = f"No se puede cancelar una reserva en estado '{self.estado}'"
            logger.error(f"Error al cancelar reserva {self.id}: {error_msg}")
            raise ValidationError(error_msg)
        
        try:
            estado_anterior = self.estado
            self.estado = 'cancelado'
            
            # Agregar motivo de cancelación
            cancelacion_texto = f"\n[Cancelado por {cancelado_por}] {motivo}" if motivo else f"\n[Cancelado por {cancelado_por}]"
            self.notas = f"{self.notas}{cancelacion_texto}" if self.notas else cancelacion_texto
            
            logger.info(f"Guardando reserva {self.id} con estado cancelado")
            self.save()
            
            # Crear notificación para el cliente
            mensaje = f'Tu reserva del {self.fecha} a las {self.hora_inicio} ha sido cancelada.'
            if motivo:
                mensaje += f' Motivo: {motivo}'
            
            logger.info(f"Creando notificación para cliente {self.cliente.username}")
            self._crear_notificacion_cliente(
                'reserva',
                'Reserva Cancelada',
                mensaje,
                '/clientes/mis_reservas/'
            )
            
            # Crear notificación para el profesional
            mensaje_profesional = f'Reserva cancelada para el {self.fecha} a las {self.hora_inicio} con {self.cliente.username}.'
            if motivo:
                mensaje_profesional += f' Motivo: {motivo}'
            
            self._crear_notificacion_profesional(
                'reserva',
                'Reserva Cancelada',
                mensaje_profesional,
                '/profesionales/panel/'
            )
            
            logger.info(f"Reserva {self.id} cancelada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inesperado al cancelar reserva {self.id}: {str(e)}")
            raise
    
    def completar(self, notas_adicionales=""):
        """
        Marca una reserva confirmada como completada
        """
        if self.estado != 'confirmado':
            raise ValidationError(f"No se puede completar una reserva en estado '{self.estado}'")
        
        self.estado = 'completado'
        if notas_adicionales:
            self.notas = f"{self.notas}\n[Completado] {notas_adicionales}" if self.notas else f"[Completado] {notas_adicionales}"
        self.save()
        
        # Crear notificación para el cliente
        self._crear_notificacion_cliente(
            'reserva',
            'Reserva Completada',
            f'Tu reserva del {self.fecha} a las {self.hora_inicio} ha sido marcada como completada.',
            '/clientes/mis_reservas/'
        )
        
        # Crear notificación para el profesional
        self._crear_notificacion_profesional(
            'reserva',
            'Reserva Completada',
            f'Reserva completada para el {self.fecha} a las {self.hora_inicio} con {self.cliente.username}.',
            '/profesionales/panel/'
        )
        
        return True
    
    def reagendar(self, nueva_fecha, nueva_hora_inicio, nueva_hora_fin, motivo=""):
        """
        Reagenda una reserva confirmada o pendiente
        """
        if self.estado not in ['pendiente', 'confirmado']:
            raise ValidationError(f"No se puede reagendar una reserva en estado '{self.estado}'")
        
        fecha_anterior = self.fecha
        hora_anterior = self.hora_inicio
        
        self.fecha = nueva_fecha
        self.hora_inicio = nueva_hora_inicio
        self.hora_fin = nueva_hora_fin
        self.estado = 'confirmado'  # Reagendar confirma la reserva
        
        if motivo:
            self.notas = f"{self.notas}\n[Reagendado] {motivo}" if self.notas else f"[Reagendado] {motivo}"
        
        self.save()
        
        # Crear notificación para el cliente
        self._crear_notificacion_cliente(
            'reserva',
            'Reserva Reagendada',
            f'Tu reserva ha sido reagendada del {fecha_anterior} a las {hora_anterior} al {nueva_fecha} a las {nueva_hora_inicio}.',
            '/clientes/mis_reservas/'
        )
        
        # Crear notificación para el profesional
        self._crear_notificacion_profesional(
            'reserva',
            'Reserva Reagendada',
            f'Reserva reagendada de {fecha_anterior} a las {hora_anterior} al {nueva_fecha} a las {nueva_hora_inicio} con {self.cliente.username}.',
            '/profesionales/panel/'
        )
        
        return True
    
    def _crear_notificacion_cliente(self, tipo, titulo, mensaje, url=""):
        """
        Método privado para crear notificaciones para el cliente
        """
        NotificacionCliente.objects.create(
            cliente=self.cliente,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            url_relacionada=url
        )
    
    def _crear_notificacion_profesional(self, tipo, titulo, mensaje, url=""):
        """
        Método privado para crear notificaciones para el profesional
        """
        if self.profesional:
            from profesionales.models import Notificacion
            Notificacion.objects.create(
                profesional=self.profesional,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                url_relacionada=url
            )
    
    @property
    def puede_ser_cancelada(self):
        """
        Verifica si la reserva puede ser cancelada
        """
        return self.estado in ['pendiente', 'confirmado']
    
    @property
    def puede_ser_completada(self):
        """
        Verifica si la reserva puede ser completada
        """
        return self.estado == 'confirmado'
    
    @property
    def puede_ser_reagendada(self):
        """
        Verifica si la reserva puede ser reagendada
        """
        return self.estado in ['pendiente', 'confirmado']
    
    @property
    def es_pasada(self):
        """
        Verifica si la reserva es de una fecha pasada
        """
        from django.utils import timezone
        return self.fecha < timezone.now().date()
    
    @property
    def es_hoy(self):
        """
        Verifica si la reserva es para hoy
        """
        from django.utils import timezone
        return self.fecha == timezone.now().date()

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