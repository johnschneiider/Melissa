from django.db import models
from django.conf import settings

# Create your models here.

class Conversacion(models.Model):
    participante1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='conversaciones_iniciadas', on_delete=models.CASCADE
    )
    participante2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='conversaciones_recibidas', on_delete=models.CASCADE
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('participante1', 'participante2')

    def __str__(self):
        return f"Conversación entre {self.participante1} y {self.participante2}"

class Mensaje(models.Model):
    conversacion = models.ForeignKey(Conversacion, related_name='mensajes', on_delete=models.CASCADE)
    remitente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    texto = models.TextField(blank=True)
    archivo = models.FileField(upload_to='chat_adjuntos/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensaje de {self.remitente} en {self.conversacion} ({self.timestamp})"
