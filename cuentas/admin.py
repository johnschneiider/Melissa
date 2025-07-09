from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPersonalizado
from .models import RateLimitConfig

class UsuarioAdmin(UserAdmin):
    model = UsuarioPersonalizado
    list_display = ['username', 'email', 'tipo', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('tipo', 'telefono',)}),
    )

admin.site.register(UsuarioPersonalizado, UsuarioAdmin)

@admin.register(RateLimitConfig)
class RateLimitConfigAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'clave', 'limite', 'activo', 'fecha_modificacion']
    list_filter = ['activo', 'fecha_creacion', 'fecha_modificacion']
    search_fields = ['nombre', 'clave', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'clave', 'limite', 'activo')
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('nombre')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Limpiar caché de rate limiting después de cambios
        from django.core.cache import cache
        cache.clear()
