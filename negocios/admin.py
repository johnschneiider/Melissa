from django.contrib import admin
from .models import Negocio, ImagenNegocio, Servicio

@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'propietario', 'activo', 'creado_en')
    list_filter = ('activo', 'creado_en')
    search_fields = ('nombre', 'propietario__username')
    readonly_fields = ('creado_en',)
