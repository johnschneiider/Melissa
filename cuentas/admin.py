from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPersonalizado

class UsuarioAdmin(UserAdmin):
    model = UsuarioPersonalizado
    list_display = ['username', 'email', 'tipo', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('tipo', 'telefono',)}),
    )

admin.site.register(UsuarioPersonalizado, UsuarioAdmin)
