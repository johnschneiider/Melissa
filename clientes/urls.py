from django.urls import path
from .views import (
    ListaNegociosView,
    DetallePeluqueroView,
    reservar_turno,
    confirmacion_reserva,
    horarios_disponibles,
    horarios_disponibles_reagendar,
    mis_reservas,
    dashboard_cliente,
    reservar_negocio,
    confirmar_reserva,
    cancelar_reserva,
    completar_reserva,
    reagendar_reserva,
    notificaciones_cliente,
    eliminar_notificacion_cliente,
    crear_calificacion,
    editar_calificacion,
    eliminar_calificacion,
    proximamente_app,
    autocompletar_servicios,
    negocios_cercanos,
    autocompletar_negocios,
    buscar_negocios,
    disponibilidad_dias,
    api_negocios_vistos_recientes,
    api_buscar_negocios,
    google_places_autocomplete,
    google_places_details,
)

app_name = 'clientes'

urlpatterns = [
    path('dashboard/', dashboard_cliente, name='dashboard'),
    path('', ListaNegociosView.as_view(), name='lista_negocios'),
    path('buscar/', buscar_negocios, name='buscar_negocios'),
    path('peluquero/<int:pk>/', DetallePeluqueroView.as_view(), name='detalle_peluquero'),
    path('peluquero/<int:peluquero_id>/reservar/', reservar_turno, name='reservar_turno'),
    path('reserva/<int:reserva_id>/confirmacion/', confirmacion_reserva, name='confirmacion_reserva'),
    path('api/horarios-disponibles/<int:negocio_id>/', horarios_disponibles, name='horarios_disponibles'),
    path('api/horarios-disponibles-reagendar/<int:reserva_id>/', horarios_disponibles_reagendar, name='horarios_disponibles_reagendar'),
    path('mis-reservas/', mis_reservas, name='mis_reservas'),
    path('negocio/<int:negocio_id>/reservar/', reservar_negocio, name='reservar_negocio'),
    path('notificaciones/', notificaciones_cliente, name='notificaciones'),
    path('notificaciones/eliminar/<int:notificacion_id>/', eliminar_notificacion_cliente, name='eliminar_notificacion'),
    path('reserva/<int:reserva_id>/confirmar/', confirmar_reserva, name='confirmar_reserva'),
    path('reserva/<int:reserva_id>/cancelar/', cancelar_reserva, name='cancelar_reserva'),
    path('reserva/<int:reserva_id>/completar/', completar_reserva, name='completar_reserva'),
    path('reserva/<int:reserva_id>/reagendar/', reagendar_reserva, name='reagendar_reserva'),
    
    # URLs de calificaciones
    path('calificar/<int:negocio_id>/<int:profesional_id>/', crear_calificacion, name='crear_calificacion'),
    path('editar-calificacion/<int:calificacion_id>/', editar_calificacion, name='editar_calificacion'),
    path('eliminar-calificacion/<int:calificacion_id>/', eliminar_calificacion, name='eliminar_calificacion'),
    path('proximamente-app/', proximamente_app, name='proximamente_app'),
    path('api/autocompletar-servicios/', autocompletar_servicios, name='autocompletar_servicios'),
    path('api/negocios-cercanos/', negocios_cercanos, name='negocios_cercanos'),
    path('api/autocompletar-negocios/', autocompletar_negocios, name='autocompletar_negocios'),
]

urlpatterns += [
    path('api/disponibilidad-dias/', disponibilidad_dias, name='api_disponibilidad_dias'),
    path('api/negocios-vistos-recientes/', api_negocios_vistos_recientes, name='api_negocios_vistos_recientes'),
    path('api/buscar-negocios/', api_buscar_negocios, name='api_buscar_negocios'),
    path('api/google-places-autocomplete/', google_places_autocomplete, name='google_places_autocomplete'),
    path('api/google-places-details/', google_places_details, name='google_places_details'),
]