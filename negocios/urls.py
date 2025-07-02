from django.urls import path
from . import views
from .views import api_responder_matricula

app_name = 'negocios'

urlpatterns = [
    path('mis/', views.mis_negocios, name='mis_negocios'),
    path('crear/', views.crear_negocio, name='crear_negocio'),
    path('<int:negocio_id>/', views.detalle_negocio, name='detalle_negocio'),
    path('<int:negocio_id>/editar/', views.editar_negocio, name='editar_negocio'),
    path('<int:negocio_id>/eliminar/', views.eliminar_negocio, name='eliminar_negocio'),
    path('<int:negocio_id>/configurar/', views.configurar_negocio, name='configurar_negocio'),
    path('<int:negocio_id>/panel/', views.panel_negocio, name='panel_negocio'),
    path('<int:negocio_id>/dashboard/', views.dashboard_negocio, name='dashboard_negocio'),
    path('solicitudes-matricula/', views.solicitudes_matricula, name='solicitudes_matricula'),
    path('perfil-profesional/<int:profesional_id>/', views.ver_perfil_profesional, name='ver_perfil_profesional'),
    path('desvincular-profesional/<int:matricula_id>/', views.desvincular_profesional, name='desvincular_profesional'),
    path('api/matricula/<int:solicitud_id>/<str:accion>/', api_responder_matricula, name='api_responder_matricula'),
    path('api/matricula/<int:solicitud_id>/aceptar/', api_responder_matricula, {'accion': 'aceptar'}, name='api_aceptar_matricula'),
    path('api/matricula/<int:solicitud_id>/rechazar/', api_responder_matricula, {'accion': 'rechazar'}, name='api_rechazar_matricula'),
    path('<int:negocio_id>/galeria/', views.galeria_negocio, name='galeria_negocio'),
    path('<int:negocio_id>/profesional/<int:profesional_id>/editar/', views.editar_profesional_negocio, name='editar_profesional_negocio'),
    path('<int:negocio_id>/calendario/', views.calendario_reservas, name='calendario_reservas'),
    path('<int:negocio_id>/api/reservas/', views.api_reservas_negocio, name='api_reservas_negocio'),
    path('<int:negocio_id>/servicios/', views.gestionar_servicios, name='gestionar_servicios'),
    path('notificaciones/', views.notificaciones_negocio, name='notificaciones'),
]
