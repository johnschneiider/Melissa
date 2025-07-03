from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class UsuarioPersonalizado(AbstractUser):
    TIPO_USUARIO = (
        ('cliente', 'Cliente'),
        ('negocio', 'Negocio'),
        ('profesional', 'Profesional'),
        ('super_admin', 'Super Administrador'),
    )
    tipo = models.CharField(max_length=15, choices=TIPO_USUARIO, default='cliente')
    telefono = models.CharField(max_length=15, blank=True) 

class Feedback(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    )
    
    PRIORIDAD_CHOICES = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    )
    
    # Información del ticket
    numero_ticket = models.CharField(max_length=20, unique=True, blank=True)
    titulo = models.CharField(max_length=200, blank=True)
    usuario = models.ForeignKey('UsuarioPersonalizado', on_delete=models.CASCADE, related_name='feedbacks_enviados')
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default='media')
    categoria = models.CharField(max_length=50, blank=True, help_text='Ej: Bug, Sugerencia, Consulta, etc.')
    
    # Archivos adjuntos
    imagen = models.ImageField(upload_to='feedback/', blank=True, null=True)
    archivos_adjuntos = models.JSONField(default=list, blank=True, help_text='Lista de archivos adjuntos')
    
    # Metadatos
    asignado_a = models.ForeignKey('UsuarioPersonalizado', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_asignados')
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    tiempo_resolucion = models.DurationField(null=True, blank=True)
    
    # Etiquetas y seguimiento
    etiquetas = models.ManyToManyField('UsuarioPersonalizado', related_name='feedback_etiquetado', blank=True)
    leido_por_admin = models.BooleanField(default=False)
    leido_por_usuario = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Ticket de Feedback'
        verbose_name_plural = 'Tickets de Feedback'

    def __str__(self):
        return f"Ticket #{self.numero_ticket} - {self.usuario.username} - {self.estado}"

    def save(self, *args, **kwargs):
        if not self.numero_ticket:
            # Generar número de ticket único
            ultimo_ticket = Feedback.objects.order_by('-id').first()
            if ultimo_ticket:
                parte = ultimo_ticket.numero_ticket.split('-')[1] if '-' in ultimo_ticket.numero_ticket else '0'
                try:
                    ultimo_numero = int(parte)
                except ValueError:
                    try:
                        ultimo_numero = int(parte, 16)  # intenta como hexadecimal
                    except ValueError:
                        ultimo_numero = 0  # valor por defecto si no es número
                self.numero_ticket = f"TICKET-{ultimo_numero + 1:06d}"
            else:
                self.numero_ticket = "TICKET-000001"
        
        if not self.titulo:
            self.titulo = f"Feedback de {self.usuario.username}"
        
        super().save(*args, **kwargs)

    def cambiar_estado(self, nuevo_estado, usuario_admin=None):
        """Cambiar el estado del ticket y registrar la acción"""
        print(f"cambiar_estado called: {self.estado} -> {nuevo_estado}")  # Debug
        self.estado = nuevo_estado
        if nuevo_estado in ['resuelto', 'cerrado'] and not self.fecha_resolucion:
            self.fecha_resolucion = timezone.now()
            if self.fecha:
                self.tiempo_resolucion = self.fecha_resolucion - self.fecha
        print(f"Saving ticket with estado: {self.estado}")  # Debug
        self.save()
        print(f"Ticket saved successfully. Current estado: {self.estado}")  # Debug
        
        # Crear respuesta automática del sistema
        RespuestaTicket.objects.create(
            ticket=self,
            autor=usuario_admin or self.asignado_a,
            mensaje=f"Estado del ticket cambiado a: {dict(self.ESTADO_CHOICES)[nuevo_estado]}",
            es_sistema=True
        )
        print(f"System response created for state change")  # Debug

class RespuestaTicket(models.Model):
    """Modelo para las respuestas en el sistema de tickets"""
    ticket = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='respuestas')
    autor = models.ForeignKey('UsuarioPersonalizado', on_delete=models.CASCADE, related_name='respuestas_ticket')
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    es_sistema = models.BooleanField(default=False, help_text='Si es una respuesta automática del sistema')
    archivos_adjuntos = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['fecha']
        verbose_name = 'Respuesta de Ticket'
        verbose_name_plural = 'Respuestas de Tickets'

    def __str__(self):
        return f"Respuesta en {self.ticket.numero_ticket} - {self.autor.username}"

class NotificacionAdmin(models.Model):
    TIPO_CHOICES = (
        ('feedback', 'Nuevo Feedback'),
        ('sistema', 'Notificación del Sistema'),
        ('ticket', 'Nuevo Ticket'),
        ('respuesta_ticket', 'Nueva Respuesta en Ticket'),
    )
    destinatario = models.ForeignKey('UsuarioPersonalizado', on_delete=models.CASCADE, related_name='notificaciones_admin')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    url_relacionada = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Notificación Admin'
        verbose_name_plural = 'Notificaciones Admin'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{str(self.destinatario)} - {self.titulo}"

    def marcar_como_leida(self):
        self.leida = True
        self.fecha_lectura = timezone.now()
        self.save() 
