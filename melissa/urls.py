from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static

def inicio(request):
    return render(request, 'inicio.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuentas/', include('cuentas.urls')),
    path('accounts/', include('allauth.urls')),
    path('', inicio, name='inicio'), 
    path('negocios/', include('negocios.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
