from django.core.management.base import BaseCommand
from django.db import transaction
from negocios.models import Negocio, ServicioNegocio, ImagenNegocio, MetricaNegocio, ReporteMensual, NotificacionNegocio
from profesionales.models import Matriculacion
from clientes.models import Reserva, Calificacion

class Command(BaseCommand):
    help = 'Limpia registros huérfanos relacionados con negocios eliminados.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Buscando y eliminando registros huérfanos relacionados con Negocio...'))
        # IDs de negocios existentes
        negocios_ids = set(Negocio.objects.values_list('id', flat=True))
        total = 0

        # Reservas
        reservas_huerfanas = Reserva.objects.exclude(peluquero_id__in=negocios_ids)
        total += reservas_huerfanas.count()
        reservas_huerfanas.delete()

        # Calificaciones
        calificaciones_huerfanas = Calificacion.objects.exclude(negocio_id__in=negocios_ids)
        total += calificaciones_huerfanas.count()
        calificaciones_huerfanas.delete()

        # Servicios del negocio
        servicios_huerfanos = ServicioNegocio.objects.exclude(negocio_id__in=negocios_ids)
        total += servicios_huerfanos.count()
        servicios_huerfanos.delete()

        # Imágenes
        imagenes_huerfanas = ImagenNegocio.objects.exclude(negocio_id__in=negocios_ids)
        total += imagenes_huerfanas.count()
        imagenes_huerfanas.delete()

        # Métricas
        metricas_huerfanas = MetricaNegocio.objects.exclude(negocio_id__in=negocios_ids)
        total += metricas_huerfanas.count()
        metricas_huerfanas.delete()

        # Reportes mensuales
        reportes_huerfanos = ReporteMensual.objects.exclude(negocio_id__in=negocios_ids)
        total += reportes_huerfanos.count()
        reportes_huerfanos.delete()

        # Notificaciones
        notificaciones_huerfanas = NotificacionNegocio.objects.exclude(negocio_id__in=negocios_ids)
        total += notificaciones_huerfanas.count()
        notificaciones_huerfanas.delete()

        # Matriculaciones
        matriculaciones_huerfanas = Matriculacion.objects.exclude(negocio_id__in=negocios_ids)
        total += matriculaciones_huerfanas.count()
        matriculaciones_huerfanas.delete()

        self.stdout.write(self.style.SUCCESS(f'¡Limpieza completada! Se eliminaron {total} registros huérfanos relacionados con negocios.'))
