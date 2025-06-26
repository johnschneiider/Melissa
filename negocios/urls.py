from django.urls import path
from . import views

urlpatterns = [
    path('crear/', views.crear_negocio, name='crear_negocio'),
    path('mis/', views.mis_negocios, name='mis_negocios'),
    path('configurar/<int:negocio_id>/', views.configurar_negocio, name='configurar_negocio'),
    path('<int:negocio_id>/panel/', views.panel_negocio, name='panel_negocio'),
    path('<int:negocio_id>/crear-peluquero/', views.crear_peluquero, name='crear_peluquero'),
    path('<int:negocio_id>/peluquero/<int:peluquero_id>/', views.detalle_peluquero, name='detalle_peluquero'),
    path('<int:negocio_id>/peluquero/<int:peluquero_id>/eliminar/', views.eliminar_peluquero, name='eliminar_peluquero'),
    path('<int:negocio_id>/asignar-horario/', views.asignar_horario_negocio, name='asignar_horario_negocio'),
    path('negocios/<int:negocio_id>/eliminar/', views.eliminar_negocio, name='eliminar_negocio'),
    path('negocios/<int:negocio_id>/restaurar/', views.restaurar_negocio, name='restaurar_negocio'),
    path('api/turnos_peluquero/<int:peluquero_id>/', views.api_turnos_peluquero, name='api_turnos_peluquero'),



]
