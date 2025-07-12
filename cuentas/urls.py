from django.urls import path
from . import views
from .views import api_notificaciones, redireccion_dashboard, dashboard_super_admin, analiticas_negocios, analiticas_profesionales, analiticas_clientes, analiticas_general, ejecutar_tests, poblar_demo, borrar_demo, reiniciar_servidor, ver_logs_servidor, test_rate_limit, gestionar_rate_limiting

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
    path('dashboard/', redireccion_dashboard, name='dashboard'),
    path('dashboard/super-admin/', dashboard_super_admin, name='dashboard_super_admin'),
    path('enviar-feedback/', views.enviar_feedback, name='enviar_feedback'),
    path('analiticas/negocios/', analiticas_negocios, name='analiticas_negocios'),
    path('analiticas/profesionales/', analiticas_profesionales, name='analiticas_profesionales'),
    path('analiticas/clientes/', analiticas_clientes, name='analiticas_clientes'),
    path('analiticas/general/', analiticas_general, name='analiticas_general'),
    path('notificaciones/super-admin/', views.notificaciones_super_admin, name='notificaciones_super_admin'),
    path('tickets/', views.lista_tickets, name='lista_tickets'),
    path('ticket/<int:ticket_id>/', views.detalle_ticket, name='detalle_ticket'),
    path('mis-tickets/', views.mis_tickets, name='mis_tickets'),
    path('mi-ticket/<int:ticket_id>/', views.detalle_mi_ticket, name='detalle_mi_ticket'),
    path('ajustes/', views.ajustes_usuario, name='ajustes'),
    path('politica-datos/', views.politica_datos, name='politica_datos'),
    path('ejecutar-tests/', ejecutar_tests, name='ejecutar_tests'),
    path('poblar-demo/', poblar_demo, name='poblar_demo'),
    path('borrar-demo/', borrar_demo, name='borrar_demo'),
    path('reiniciar-servidor/', reiniciar_servidor, name='reiniciar_servidor'),
    path('ver-logs-servidor/', ver_logs_servidor, name='ver_logs_servidor'),
    path('test-rate-limit/', test_rate_limit, name='test_rate_limit'),
    path('gestionar-rate-limiting/', gestionar_rate_limiting, name='gestionar_rate_limiting'),
    path('control-reservas/', views.control_reservas, name='control_reservas'),
]
