from django.core.management.base import BaseCommand
from negocios.models import Negocio
from profesionales.models import Profesional, Matriculacion
from clientes.models import Reserva, Calificacion
from cuentas.models import UsuarioPersonalizado

class Command(BaseCommand):
    help = 'Elimina todos los clientes, negocios y profesionales (¡IRREVERSIBLE!)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Eliminando todas las reservas, calificaciones, matriculaciones, negocios, profesionales y clientes...'))
        # Eliminar reservas y calificaciones primero (dependen de negocio/profesional/cliente)
        Reserva.objects.all().delete()
        Calificacion.objects.all().delete()
        Matriculacion.objects.all().delete()
        # Eliminar negocios y profesionales
        Negocio.objects.all().delete()
        Profesional.objects.all().delete()
        # Eliminar clientes (usuarios tipo cliente)
        clientes = UsuarioPersonalizado.objects.filter(tipo='cliente')
        count_clientes = clientes.count()
        clientes.delete()
        self.stdout.write(self.style.SUCCESS(f'¡Eliminación completada! Se eliminaron todos los clientes ({count_clientes}), negocios y profesionales.'))
