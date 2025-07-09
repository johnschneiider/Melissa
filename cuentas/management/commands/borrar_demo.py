from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from negocios.models import Negocio
from profesionales.models import Profesional, Matriculacion
from clientes.models import Reserva, Calificacion

User = get_user_model()

class Command(BaseCommand):
    help = 'Elimina profesionales, clientes, cuentas tipo negocio y los negocios asociados. Solo para desarrollo.'

    def handle(self, *args, **options):
        # Eliminar reservas y calificaciones primero (dependen de negocio/profesional/cliente)
        Reserva.objects.all().delete()
        Calificacion.objects.all().delete()
        Matriculacion.objects.all().delete()
        # Eliminar negocios y profesionales
        Negocio.objects.all().delete()
        Profesional.objects.all().delete()
        # Eliminar clientes (usuarios tipo cliente)
        clientes = User.objects.filter(tipo='cliente')
        count_clientes = clientes.count()
        clientes.delete()
        # Eliminar negocios (usuarios tipo negocio)
        negocios = User.objects.filter(tipo='negocio')
        count_negocios = negocios.count()
        negocios.delete()
        self.stdout.write(self.style.SUCCESS(f'Eliminados {count_clientes} clientes, {count_negocios} cuentas de negocio, todos los negocios, profesionales, reservas y calificaciones.')) 