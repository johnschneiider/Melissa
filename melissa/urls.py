from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from clientes.models import Reserva  # Importar el modelo

def inicio(request):
    total_reservas = Reserva.objects.count()
    return render(request, 'inicio.html', {'total_reservas': total_reservas})

def custom_429(request, exception=None):
    return render(request, "429.html", status=429)

handler429 = "melissa.urls.custom_429"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('cuentas/', include('cuentas.urls')),
    path('', inicio, name='inicio'),
    path('negocios/', include(('negocios.urls', 'negocios'), namespace='negocios')),
    path('clientes/', include('clientes.urls')),
    path('profesionales/', include(('profesionales.urls', 'profesionales'), namespace='profesionales')),
    path('chat/', include('chat.urls')),
    path('ia-visagismo/', include('ia_visagismo.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)