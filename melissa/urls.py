from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from clientes.models import Reserva, Calificacion
from negocios.models import Negocio
from django.utils import timezone
from django.db.models import Count, Avg

def inicio(request):
    if request.user.is_authenticated and hasattr(request.user, 'tipo') and request.user.tipo == 'cliente':
        # Próximas reservas (hoy o futuras, estado pendiente/confirmado)
        proximas_reservas = Reserva.objects.filter(
            cliente=request.user,
            fecha__gte=timezone.now().date(),
            estado__in=['pendiente', 'confirmado']
        ).select_related('peluquero', 'profesional', 'servicio').order_by('fecha', 'hora_inicio')[:3]

        # Historial de reservas (completadas o canceladas, más recientes)
        historial_reservas = Reserva.objects.filter(
            cliente=request.user
        ).exclude(estado__in=['pendiente', 'confirmado']).select_related('peluquero', 'profesional', 'servicio').order_by('-fecha', '-hora_inicio')[:5]

        # Negocios vistos recientemente (por reservas recientes)
        negocios_vistos_ids = Reserva.objects.filter(
            cliente=request.user
        ).order_by('-creado_en').values_list('peluquero', flat=True).distinct()[:5]
        negocios_vistos = Negocio.objects.filter(id__in=negocios_vistos_ids)

        # Negocios recomendados (top rating, excluyendo los ya vistos)
        negocios_recomendados = Negocio.objects.filter(activo=True).exclude(id__in=negocios_vistos_ids).annotate(
            rating=Avg('calificaciones__puntaje'),
            total_resenias=Count('calificaciones')
        ).order_by('-rating', '-total_resenias')[:5]

        context = {
            'is_cliente': True,
            'proximas_reservas': proximas_reservas,
            'historial_reservas': historial_reservas,
            'negocios_vistos': negocios_vistos,
            'negocios_recomendados': negocios_recomendados,
        }
        return render(request, 'inicio.html', context)
    else:
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