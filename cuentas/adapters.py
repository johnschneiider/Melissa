from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.shortcuts import redirect
from .models import UsuarioPersonalizado

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Adaptador personalizado para manejar la redirección después del registro/login
    """
    
    def get_login_redirect_url(self, request):
        """
        Redirige al usuario según su tipo después del login
        """
        if request.user.is_authenticated:
            try:
                # Como UsuarioPersonalizado extiende User, accedemos directamente
                if hasattr(request.user, 'tipo'):
                    if request.user.tipo == 'cliente':
                        return reverse('inicio')  # Redirige a la raíz
                    elif request.user.tipo == 'negocio':
                        return reverse('negocios:panel')  # Redirige al panel de negocio
                    elif request.user.tipo == 'profesional':
                        return reverse('profesionales:panel')
                    elif request.user.tipo == 'super_admin':
                        return reverse('dashboard_super_admin')
                    else:
                        return reverse('inicio')
                else:
                    # Si no tiene tipo, redirigir a seleccionar
                    return reverse('cuentas:seleccionar_tipo_google')
            except Exception:
                # Si hay algún error, redirigir a seleccionar tipo
                return reverse('cuentas:seleccionar_tipo_google')
        
        return super().get_login_redirect_url(request)

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adaptador personalizado para manejar la redirección después del login social
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Se ejecuta antes del login social
        """
        # Verificar si el usuario ya existe
        if sociallogin.is_existing:
            user = sociallogin.user
            # Verificar si el usuario tiene tipo asignado
            if hasattr(user, 'tipo') and user.tipo:
                # Si tiene tipo, no hacer nada especial
                pass
            else:
                # Si no tiene tipo, redirigir a seleccionar
                sociallogin.state['next'] = reverse('cuentas:seleccionar_tipo_google')
        else:
            # Usuario nuevo, redirigir a seleccionar tipo después del registro
            sociallogin.state['next'] = reverse('cuentas:seleccionar_tipo_google')
    
    def save_user(self, request, sociallogin, form=None):
        """
        Se ejecuta cuando se guarda un usuario social
        """
        user = super().save_user(request, sociallogin, form)
        
        # Verificar si el usuario ya tiene tipo asignado
        if not hasattr(user, 'tipo') or not user.tipo:
            # Asignar tipo por defecto
            user.tipo = 'cliente'
            user.save()
        
        return user 