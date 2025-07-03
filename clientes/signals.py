from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Reserva, MetricaCliente
from negocios.models import MetricaNegocio, ReporteMensual, Negocio
from profesionales.models import MetricaProfesional
from datetime import date
from django.db import transaction
from collections import Counter
from decimal import Decimal

@receiver([post_save, post_delete], sender=Reserva)
def actualizar_metricas_reserva(sender, instance, **kwargs):
    negocio = instance.peluquero
    fecha = instance.fecha
    # Actualizar métrica diaria
    metrica, _ = MetricaNegocio.objects.get_or_create(negocio=negocio, fecha=fecha)
    reservas = Reserva.objects.filter(peluquero=negocio, fecha=fecha)
    metrica.total_reservas = reservas.count()
    metrica.reservas_completadas = reservas.filter(estado='completado').count()
    metrica.reservas_canceladas = reservas.filter(estado='cancelado').count()
    metrica.reservas_no_show = reservas.filter(estado='no_show').count() if 'no_show' in dict(Reserva._meta.get_field('estado').choices) else 0
    # Ingresos y promedio ticket
    total_ingresos = 0
    for r in reservas:
        if r.servicio and hasattr(r.servicio, 'servicionegocio_set'):
            sn = r.servicio.servicionegocio_set.filter(negocio=negocio).first()
            if sn and sn.precio:
                total_ingresos += float(sn.precio)
    metrica.ingresos_totales = total_ingresos
    metrica.promedio_ticket = (total_ingresos / reservas.count()) if reservas.count() else 0
    metrica.save()
    # Actualizar reporte mensual
    año = fecha.year
    mes = fecha.month
    reporte, _ = ReporteMensual.objects.get_or_create(negocio=negocio, año=año, mes=mes)
    reservas_mes = Reserva.objects.filter(peluquero=negocio, fecha__year=año, fecha__month=mes)
    reporte.total_reservas = reservas_mes.count()
    reporte.reservas_completadas = reservas_mes.filter(estado='completado').count()
    reporte.ingresos_totales = 0
    for r in reservas_mes:
        if r.servicio and hasattr(r.servicio, 'servicionegocio_set'):
            sn = r.servicio.servicionegocio_set.filter(negocio=negocio).first()
            if sn and sn.precio:
                reporte.ingresos_totales += float(sn.precio)
    reporte.promedio_ticket = (reporte.ingresos_totales / reservas_mes.count()) if reservas_mes.count() else 0
    reporte.save()

@receiver([post_save, post_delete], sender=Reserva)
def actualizar_metricas_profesional_cliente(sender, instance, **kwargs):
    # Profesional
    if instance.profesional:
        profesional = instance.profesional
        fecha = instance.fecha
        metricap, _ = MetricaProfesional.objects.get_or_create(profesional=profesional, fecha=fecha)
        reservas_prof = Reserva.objects.filter(profesional=profesional, fecha=fecha)
        metricap.total_turnos = reservas_prof.count()
        metricap.turnos_completados = reservas_prof.filter(estado='completado').count()
        metricap.turnos_cancelados = reservas_prof.filter(estado='cancelado').count()
        # Ingresos
        total_ingresos = Decimal('0.00')
        for r in reservas_prof:
            if r.servicio and hasattr(r.servicio, 'servicionegocio_set'):
                sn = r.servicio.servicionegocio_set.filter(negocio=r.peluquero).first()
                if sn and sn.precio:
                    total_ingresos += Decimal(str(sn.precio))
        metricap.ingresos_totales = total_ingresos
        # Calificación promedio y horas trabajadas pueden calcularse aquí si se desea
        metricap.save()
    # Cliente
    cliente = instance.cliente
    fecha = instance.fecha
    metricac, _ = MetricaCliente.objects.get_or_create(cliente=cliente, fecha=fecha)
    reservas_cli = Reserva.objects.filter(cliente=cliente, fecha=fecha)
    metricac.total_turnos = reservas_cli.count()
    metricac.turnos_completados = reservas_cli.filter(estado='completado').count()
    metricac.turnos_cancelados = reservas_cli.filter(estado='cancelado').count()
    # Servicios más solicitados y profesionales más reservados (solo del día)
    servicios = [r.servicio.servicio.nombre for r in reservas_cli if r.servicio]
    profesionales = [r.profesional.nombre_completo for r in reservas_cli if r.profesional]
    metricac.servicios_mas_solicitados = ', '.join([s for s, _ in Counter(servicios).most_common(3)])
    metricac.profesionales_mas_reservados = ', '.join([p for p, _ in Counter(profesionales).most_common(3)])
    metricac.save() 