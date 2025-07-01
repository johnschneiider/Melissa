from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.lista_conversaciones, name='lista_conversaciones'),
    path('buscar/', views.buscar_usuarios, name='buscar_usuarios'),
    path('iniciar/<int:usuario_id>/', views.iniciar_chat, name='iniciar_chat'),
    path('conversacion/<int:conversacion_id>/', views.chat_individual, name='chat_individual'),
    path('api/mensajes/<int:conversacion_id>/', views.api_mensajes, name='api_mensajes'),
    path('api/enviar/<int:conversacion_id>/', views.enviar_mensaje, name='enviar_mensaje'),
] 