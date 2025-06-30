from django.urls import path
from .views import (
    ListaNegociosView,
    DetallePeluqueroView,
    reservar_turno,
    confirmacion_reserva,
    horarios_disponibles,
    mis_reservas,
    dashboard_cliente,
    reservar_negocio,
    notificaciones,
)

app_name = 'clientes'

urlpatterns = [
    path('dashboard/', dashboard_cliente, name='dashboard'),
    path('', ListaNegociosView.as_view(), name='lista_negocios'),
    path('peluquero/<int:pk>/', DetallePeluqueroView.as_view(), name='detalle_peluquero'),
    path('peluquero/<int:peluquero_id>/reservar/', reservar_turno, name='reservar_turno'),
    path('reserva/<int:reserva_id>/confirmacion/', confirmacion_reserva, name='confirmacion_reserva'),
    path('api/horarios-disponibles/<int:peluquero_id>/', horarios_disponibles, name='horarios_disponibles'),
    path('mis-reservas/', mis_reservas, name='mis_reservas'),
    path('negocio/<int:negocio_id>/reservar/', reservar_negocio, name='reservar_negocio'),
    path('notificaciones/', notificaciones, name='notificaciones'),
]