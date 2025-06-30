from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea un superusuario con tipo de usuario personalizado'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True)
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)
        parser.add_argument('--tipo', type=str, choices=['cliente', 'negocio'], default='cliente')
        parser.add_argument('--first-name', type=str, default='')
        parser.add_argument('--last-name', type=str, default='')
        parser.add_argument('--telefono', type=str, default='')

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Verificar si el usuario ya existe
                if User.objects.filter(username=options['username']).exists():
                    self.stdout.write(
                        self.style.WARNING(f'El usuario {options["username"]} ya existe.')
                    )
                    return

                # Crear el superusuario
                user = User.objects.create_superuser(
                    username=options['username'],
                    email=options['email'],
                    password=options['password'],
                    first_name=options['first_name'],
                    last_name=options['last_name'],
                    tipo=options['tipo'],
                    telefono=options['telefono']
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Superusuario {user.username} creado exitosamente con tipo: {user.get_tipo_display()}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear superusuario: {e}')
            ) 