from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def enviar_email_reserva_confirmada(reserva):
    """Envía email de confirmación cuando se crea una nueva reserva"""
    try:
        cliente = reserva.cliente
        negocio = reserva.peluquero
        profesional = reserva.profesional
        
        # Preparar contexto
        context = {
            'cliente': cliente,
            'reserva': reserva,
            'negocio': negocio,
            'profesional': profesional,
            'fecha_formateada': reserva.fecha.strftime('%A, %d de %B de %Y'),
            'hora_formateada': reserva.hora_inicio.strftime('%H:%M'),
            'request': None,  # Para compatibilidad con templates
        }
        
        # Renderizar templates
        html_content = render_to_string('emails/reserva_confirmada.html', context)
        text_content = render_to_string('emails/reserva_confirmada.txt', context)
        
        # Enviar email
        send_mail(
            subject=f'¡Reserva Confirmada! - {negocio.nombre}',
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cliente.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Email de confirmación enviado a {cliente.email} para reserva #{reserva.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email de confirmación a {cliente.email}: {str(e)}")
        return False

def enviar_email_reserva_cancelada(reserva):
    """Envía email de cancelación cuando se cancela una reserva"""
    try:
        cliente = reserva.cliente
        negocio = reserva.peluquero
        
        # Preparar contexto
        context = {
            'cliente': cliente,
            'reserva': reserva,
            'negocio': negocio,
            'fecha_formateada': reserva.fecha.strftime('%A, %d de %B de %Y'),
            'hora_formateada': reserva.hora_inicio.strftime('%H:%M'),
        }
        
        # Renderizar templates
        html_content = render_to_string('emails/reserva_cancelada.html', context)
        text_content = render_to_string('emails/reserva_cancelada.txt', context)
        
        # Enviar email
        send_mail(
            subject=f'Reserva Cancelada - {negocio.nombre}',
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cliente.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Email de cancelación enviado a {cliente.email} para reserva #{reserva.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email de cancelación a {cliente.email}: {str(e)}")
        return False

def enviar_email_reserva_reagendada(reserva):
    """Envía email de reagendamiento cuando se reagenda una reserva"""
    try:
        cliente = reserva.cliente
        negocio = reserva.peluquero
        
        # Preparar contexto
        context = {
            'cliente': cliente,
            'reserva': reserva,
            'negocio': negocio,
            'fecha_formateada': reserva.fecha.strftime('%A, %d de %B de %Y'),
            'hora_formateada': reserva.hora_inicio.strftime('%H:%M'),
        }
        
        # Renderizar templates
        html_content = render_to_string('emails/reserva_reagendada.html', context)
        text_content = render_to_string('emails/reserva_reagendada.txt', context)
        
        # Enviar email
        send_mail(
            subject=f'Reserva Reagendada - {negocio.nombre}',
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cliente.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Email de reagendamiento enviado a {cliente.email} para reserva #{reserva.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email de reagendamiento a {cliente.email}: {str(e)}")
        return False 