from django.urls import path
from .views import registro_cliente, registro_negocio, LoginUsuario
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('registro/cliente/', registro_cliente, name='registro_cliente'),
    path('registro/negocio/', registro_negocio, name='registro_negocio'),
    path('login/', LoginUsuario.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
