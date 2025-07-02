from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import pre_social_login
from django.conf import settings
from .models import UsuarioPersonalizado

@receiver(user_signed_up)
def handle_user_signed_up(sender, request, user, **kwargs):
    """
    Signal que se ejecuta cuando un usuario se registra con Google
    """
    # Verificar si el usuario tiene una cuenta social (Google)
    if hasattr(user, 'socialaccount_set') and user.socialaccount_set.filter(provider='google').exists():
        # Asignar tipo por defecto si no tiene
        if not hasattr(user, 'tipo') or not user.tipo:
            user.tipo = 'cliente'
            user.save()

@receiver(pre_social_login)
def handle_pre_social_login(sender, request, sociallogin, **kwargs):
    """
    Signal que se ejecuta antes del login social
    """
    if sociallogin.is_existing:
        # Usuario existente, verificar si tiene tipo asignado
        user = sociallogin.user
        if not hasattr(user, 'tipo') or not user.tipo:
            # Si no tiene tipo, redirigir a seleccionar
            sociallogin.state['next'] = reverse('cuentas:seleccionar_tipo_google')
    else:
        # Usuario nuevo, redirigir a seleccionar tipo después del registro
        sociallogin.state['next'] = reverse('cuentas:seleccionar_tipo_google')

@receiver(post_save, sender=UsuarioPersonalizado)
def ensure_super_admin(sender, instance, **kwargs):
    if instance.is_superuser and instance.tipo != 'super_admin':
        instance.tipo = 'super_admin'
        instance.save(update_fields=['tipo']) 