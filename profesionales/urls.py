from django.urls import path
from . import views
from .views import publica_profesional

app_name = 'profesionales'

urlpatterns = [
    path('completar-perfil/', views.completar_perfil, name='completar_perfil'),
    path('panel/', views.panel, name='panel'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('buscar-negocio/', views.buscar_negocio, name='buscar_negocio'),
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path('cancelar-matricula/<int:matricula_id>/', views.cancelar_matricula, name='cancelar_matricula'),
    path('notificaciones/eliminar/<int:notificacion_id>/', views.eliminar_notificacion, name='eliminar_notificacion'),
    path('gestionar-ausencias/', views.gestionar_ausencias, name='gestionar_ausencias'),
]

urlpatterns += [
    path('publico/<int:pk>/', publica_profesional, name='publica_profesional'),
] 