from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from clientes.models import Reserva
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envía recordatorios de reservas por email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['dia_antes', 'tres_horas'],
            help='Tipo de recordatorio a enviar'
        )

    def handle(self, *args, **options):
        tipo = options.get('tipo')
        
        if tipo == 'dia_antes':
            self.enviar_recordatorios_dia_antes()
        elif tipo == 'tres_horas':
            self.enviar_recordatorios_tres_horas()
        else:
            # Si no se especifica tipo, enviar ambos
            self.enviar_recordatorios_dia_antes()
            self.enviar_recordatorios_tres_horas()

    def enviar_recordatorios_dia_antes(self):
        """Envía recordatorios 1 día antes de la cita"""
        self.stdout.write("Enviando recordatorios de 1 día antes...")
        
        # Calcular fecha objetivo (mañana)
        manana = timezone.now().date() + timedelta(days=1)
        
        # Buscar reservas para mañana que no han recibido recordatorio de 1 día
        reservas = Reserva.objects.filter(
            fecha=manana,
            estado__in=['pendiente', 'confirmado'],
            recordatorio_dia_enviado=False
        ).select_related('cliente', 'peluquero', 'profesional', 'servicio')
        
        enviados = 0
        for reserva in reservas:
            try:
                self.enviar_email_recordatorio(reserva, 'dia_antes')
                reserva.recordatorio_dia_enviado = True
                reserva.save()
                enviados += 1
                self.stdout.write(f"✓ Recordatorio enviado a {reserva.cliente.email} para {reserva.fecha}")
            except Exception as e:
                logger.error(f"Error enviando recordatorio a {reserva.cliente.email}: {str(e)}")
                self.stdout.write(f"✗ Error enviando recordatorio a {reserva.cliente.email}")
        
        self.stdout.write(f"Recordatorios de 1 día enviados: {enviados}")

    def enviar_recordatorios_tres_horas(self):
        """Envía recordatorios 3 horas antes de la cita"""
        self.stdout.write("Enviando recordatorios de 3 horas antes...")
        
        # Calcular hora objetivo (3 horas desde ahora)
        ahora = timezone.now()
        hora_objetivo = ahora + timedelta(hours=3)
        
        # Buscar reservas en las próximas 3 horas que no han recibido recordatorio de 3 horas
        reservas = Reserva.objects.filter(
            fecha=hora_objetivo.date(),
            hora_inicio__hour=hora_objetivo.hour,
            estado__in=['pendiente', 'confirmado'],
            recordatorio_tres_horas_enviado=False
        ).select_related('cliente', 'peluquero', 'profesional', 'servicio')
        
        enviados = 0
        for reserva in reservas:
            try:
                self.enviar_email_recordatorio(reserva, 'tres_horas')
                reserva.recordatorio_tres_horas_enviado = True
                reserva.save()
                enviados += 1
                self.stdout.write(f"✓ Recordatorio enviado a {reserva.cliente.email} para {reserva.fecha} {reserva.hora_inicio}")
            except Exception as e:
                logger.error(f"Error enviando recordatorio a {reserva.cliente.email}: {str(e)}")
                self.stdout.write(f"✗ Error enviando recordatorio a {reserva.cliente.email}")
        
        self.stdout.write(f"Recordatorios de 3 horas enviados: {enviados}")

    def enviar_email_recordatorio(self, reserva, tipo):
        """Envía el email de recordatorio"""
        cliente = reserva.cliente
        negocio = reserva.peluquero
        profesional = reserva.profesional
        
        # Preparar datos del contexto
        context = {
            'cliente': cliente,
            'reserva': reserva,
            'negocio': negocio,
            'profesional': profesional,
            'tipo': tipo,
            'fecha_formateada': reserva.fecha.strftime('%A, %d de %B de %Y'),
            'hora_formateada': reserva.hora_inicio.strftime('%H:%M'),
        }
        
        # Renderizar templates
        if tipo == 'dia_antes':
            subject = f'Recordatorio: Tu cita mañana en {negocio.nombre}'
            html_template = 'emails/recordatorio_dia_antes.html'
            text_template = 'emails/recordatorio_dia_antes.txt'
        else:  # tres_horas
            subject = f'Recordatorio: Tu cita en 3 horas en {negocio.nombre}'
            html_template = 'emails/recordatorio_tres_horas.html'
            text_template = 'emails/recordatorio_tres_horas.txt'
        
        # Renderizar contenido
        html_content = render_to_string(html_template, context)
        text_content = render_to_string(text_template, context)
        
        # Enviar email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cliente.email],
            html_message=html_content,
            fail_silently=False,
        ) 