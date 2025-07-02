from django.urls import path
from . import views

app_name = 'ia_visagismo'

urlpatterns = [
    path('', views.visagismo_home, name='home'),
    path('subir-foto/', views.subir_foto, name='subir_foto'),
    path('resultado/<int:analisis_id>/', views.resultado_analisis, name='resultado'),
    path('historial/', views.historial_visagismo, name='historial'),
    path('api/guardar-seleccion/', views.guardar_seleccion, name='guardar_seleccion'),
    path('api/estado/<int:analisis_id>/', views.api_estado_analisis, name='api_estado'),
    path('api/generar-imagen/', views.generar_imagen_corte, name='api_generar_imagen'),
    path('api/estado-tarea/<str:task_id>/', views.estado_tarea_generar_imagen, name='api_estado_tarea_generar_imagen'),
] 