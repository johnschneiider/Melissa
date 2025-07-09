from django.core.management.base import BaseCommand
from cuentas.models import RateLimitConfig

class Command(BaseCommand):
    help = 'Poblar configuraciones iniciales de rate limiting'

    def handle(self, *args, **options):
        configuraciones = [
            {
                'nombre': 'Login - Intentos por minuto',
                'clave': 'login_rate',
                'limite': '5/m',
                'descripcion': 'Número máximo de intentos de login por minuto por IP'
            },
            {
                'nombre': 'Registro - Intentos por hora',
                'clave': 'register_rate',
                'limite': '3/h',
                'descripcion': 'Número máximo de intentos de registro por hora por IP'
            },
            {
                'nombre': 'Reservas - Creación por hora',
                'clave': 'reservation_rate',
                'limite': '10/h',
                'descripcion': 'Número máximo de reservas que se pueden crear por hora por usuario'
            },
            {
                'nombre': 'API General - Requests por hora',
                'clave': 'api_rate',
                'limite': '100/h',
                'descripcion': 'Número máximo de requests a APIs por hora por IP'
            },
            {
                'nombre': 'Test Rate Limit - Requests por minuto',
                'clave': 'test_rate',
                'limite': '10/m',
                'descripcion': 'Número máximo de requests a la vista de prueba por minuto'
            },
            {
                'nombre': 'Cancelar Reserva - Intentos por minuto',
                'clave': 'cancel_reservation_rate',
                'limite': '5/m',
                'descripcion': 'Número máximo de intentos de cancelar reservas por minuto'
            },
            {
                'nombre': 'Reagendar Reserva - Intentos por minuto',
                'clave': 'reschedule_reservation_rate',
                'limite': '5/m',
                'descripcion': 'Número máximo de intentos de reagendar reservas por minuto'
            },
        ]

        creados = 0
        actualizados = 0

        for config in configuraciones:
            obj, created = RateLimitConfig.objects.get_or_create(
                clave=config['clave'],
                defaults={
                    'nombre': config['nombre'],
                    'limite': config['limite'],
                    'descripcion': config['descripcion'],
                    'activo': True
                }
            )
            
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Creada configuración: {config["nombre"]}')
                )
            else:
                # Actualizar si ya existe
                obj.nombre = config['nombre']
                obj.limite = config['limite']
                obj.descripcion = config['descripcion']
                obj.activo = True
                obj.save()
                actualizados += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Actualizada configuración: {config["nombre"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Proceso completado:\n'
                f'   ✅ Configuraciones creadas: {creados}\n'
                f'   🔄 Configuraciones actualizadas: {actualizados}\n'
                f'   📊 Total configuraciones activas: {RateLimitConfig.objects.filter(activo=True).count()}'
            )
        ) 