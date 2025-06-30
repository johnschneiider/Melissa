from django.urls import path
from . import views
from .views import api_notificaciones

app_name = 'cuentas'

urlpatterns = [
    path('registro/', views.registro_unificado, name='registro_unificado'),
    path('login/', views.LoginPersonalizadoView.as_view(), name='login_personalizado'),
    path('logout/', views.logout_personalizado, name='logout_personalizado'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('cambiar-tipo/', views.cambiar_tipo_usuario, name='cambiar_tipo_usuario'),
    path('seleccionar-tipo-google/', views.seleccionar_tipo_cuenta_google, name='seleccionar_tipo_google'),
    path('completar-perfil-google/', views.completar_perfil_google, name='completar_perfil_google'),
    path('api/notificaciones/', api_notificaciones, name='api_notificaciones'),
]
