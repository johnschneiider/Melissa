from django.db import models
from django.conf import settings
import json

class AnalisisVisagismo(models.Model):
    """Modelo para almacenar análisis de visagismo"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analisis_visagismo')
    imagen_original = models.ImageField(upload_to='visagismo/originales/')
    imagen_procesada = models.ImageField(upload_to='visagismo/procesadas/', blank=True, null=True)
    
    # Análisis facial
    forma_cara = models.CharField(max_length=50, blank=True)  # ovalada, redonda, cuadrada, etc.
    tipo_cabello = models.CharField(max_length=50, blank=True)  # liso, ondulado, rizado
    color_cabello = models.CharField(max_length=50, blank=True)
    color_ojos = models.CharField(max_length=50, blank=True)
    tono_piel = models.CharField(max_length=50, blank=True)
    
    # Medidas faciales (JSON)
    medidas_faciales = models.JSONField(default=dict, blank=True)
    
    # Recomendaciones
    recomendaciones = models.JSONField(default=list, blank=True)
    
    # Estado del procesamiento
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('procesando', 'Procesando'),
            ('completado', 'Completado'),
            ('error', 'Error')
        ],
        default='pendiente'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Análisis de {self.usuario.username} - {self.fecha_creacion.strftime('%d/%m/%Y')}"

class RecomendacionCorte(models.Model):
    """Modelo para almacenar recomendaciones específicas de cortes"""
    analisis = models.ForeignKey(AnalisisVisagismo, on_delete=models.CASCADE, related_name='cortes_recomendados')
    nombre_corte = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen_ejemplo = models.ImageField(upload_to='visagismo/cortes/', blank=True, null=True)
    confianza = models.FloatField(default=0.0)  # Porcentaje de confianza de la IA
    categoria = models.CharField(
        max_length=50,
        choices=[
            ('corto', 'Corto'),
            ('medio', 'Medio'),
            ('largo', 'Largo'),
            ('asimetrico', 'Asimétrico'),
            ('capas', 'Capas'),
            ('degradado', 'Degradado')
        ]
    )
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre_corte} - {self.analisis.usuario.username}"

class HistorialVisagismo(models.Model):
    """Modelo para guardar historial de consultas"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='historial_visagismo')
    analisis = models.ForeignKey(AnalisisVisagismo, on_delete=models.CASCADE, related_name='historiales')
    corte_seleccionado = models.ForeignKey(RecomendacionCorte, on_delete=models.SET_NULL, null=True, blank=True, related_name='historiales_corte')
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    satisfaccion = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True
    )
    comentarios = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_consulta']
    
    def __str__(self):
        return f"Consulta de {self.usuario.username} - {self.fecha_consulta.strftime('%d/%m/%Y')}"
