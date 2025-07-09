from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from negocios.models import Negocio, Servicio, ServicioNegocio
from profesionales.models import Profesional, Matriculacion
from clientes.models import Reserva, Calificacion
from datetime import date, time, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de ejemplo para demo/pruebas'

    def handle(self, *args, **options):
        # Superadmin
        if not User.objects.filter(username='superadmin').exists():
            User.objects.create_superuser(username='superadmin', email='super@demo.com', password='Malware01', tipo='super_admin')
            self.stdout.write(self.style.SUCCESS('Superadmin creado'))

        # Negocios y usuarios tipo negocio
        negocios = []
        for i in range(1, 11):
            neg_user, _ = User.objects.get_or_create(username=f'negocio{i}', defaults={
                'email': f'negocio{i}@demo.com', 'tipo': 'negocio', 'password': 'Malware01'})
            negocio, _ = Negocio.objects.get_or_create(nombre=f'Peluquería Demo {i}', propietario=neg_user, defaults={'direccion': f'Calle {i*10}'})
            negocios.append(negocio)
        self.stdout.write(self.style.SUCCESS('10 negocios y usuarios tipo negocio creados'))

        # Profesionales y usuarios tipo profesional
        profesionales = []
        for i in range(1, 101):
            user_prof, _ = User.objects.get_or_create(username=f'profesional{i}', defaults={
                'email': f'profesional{i}@demo.com', 'tipo': 'profesional', 'password': 'Malware01'})
            prof, _ = Profesional.objects.get_or_create(usuario=user_prof, defaults={'nombre_completo': f'Profesional Demo {i}'})
            profesionales.append(prof)
        self.stdout.write(self.style.SUCCESS('100 profesionales y usuarios tipo profesional creados'))

        # Matriculación de profesionales en negocios (1 a 1)
        for i, prof in enumerate(profesionales):
            negocio = negocios[i % len(negocios)]
            # Simular solicitud y aprobación
            matricula, _ = Matriculacion.objects.get_or_create(profesional=prof, negocio=negocio, defaults={'estado': 'pendiente'})
            matricula.estado = 'aprobada'
            matricula.save()
        self.stdout.write(self.style.SUCCESS('Profesionales matriculados y aprobados en negocios'))

        # Crear clientes ficticios
        clientes = []
        for i in range(1, 11):
            cli, _ = User.objects.get_or_create(username=f'cliente{i}', defaults={
                'email': 'johnsneiider@gmail.com', 'tipo': 'cliente', 'password': 'Malware01'})
            clientes.append(cli)
        self.stdout.write(self.style.SUCCESS('10 clientes creados'))

        # Servicios
        servicios = []
        for nombre in ['Corte', 'Color', 'Peinado']:
            serv, _ = Servicio.objects.get_or_create(nombre=nombre)
            servicios.append(serv)
        for negocio in negocios:
            for serv in servicios:
                ServicioNegocio.objects.get_or_create(negocio=negocio, servicio=serv, defaults={'precio': 100})
        self.stdout.write(self.style.SUCCESS('Servicios creados y asociados a negocios'))

        # Reservas demo (opcional, solo para los primeros clientes y profesionales)
        for i, cli in enumerate(clientes):
            prof = profesionales[i % len(profesionales)]
            negocio = negocios[i % len(negocios)]
            Reserva.objects.get_or_create(
                cliente=cli,
                peluquero=negocio,
                profesional=prof,
                fecha=date.today() + timedelta(days=i),
                hora_inicio=time(10+i, 0),
                hora_fin=time(10+i, 30),
                servicio=ServicioNegocio.objects.filter(negocio=negocio).first(),
                estado='pendiente',
            )
        self.stdout.write(self.style.SUCCESS('Reservas de ejemplo creadas'))

        self.stdout.write(self.style.SUCCESS('¡Base de datos de demo lista!')) 