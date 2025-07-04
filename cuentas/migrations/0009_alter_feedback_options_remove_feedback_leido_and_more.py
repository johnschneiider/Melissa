# Generated by Django 5.2.3 on 2025-07-01 23:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0008_alter_feedback_usuario_notificacionadmin"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="feedback",
            options={
                "ordering": ["-fecha"],
                "verbose_name": "Ticket de Feedback",
                "verbose_name_plural": "Tickets de Feedback",
            },
        ),
        migrations.RemoveField(
            model_name="feedback",
            name="leido",
        ),
        migrations.AddField(
            model_name="feedback",
            name="archivos_adjuntos",
            field=models.JSONField(
                blank=True, default=list, help_text="Lista de archivos adjuntos"
            ),
        ),
        migrations.AddField(
            model_name="feedback",
            name="asignado_a",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tickets_asignados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="feedback",
            name="categoria",
            field=models.CharField(
                blank=True,
                help_text="Ej: Bug, Sugerencia, Consulta, etc.",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="feedback",
            name="estado",
            field=models.CharField(
                choices=[
                    ("pendiente", "Pendiente"),
                    ("en_proceso", "En Proceso"),
                    ("resuelto", "Resuelto"),
                    ("cerrado", "Cerrado"),
                ],
                default="pendiente",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="feedback",
            name="fecha_resolucion",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="feedback",
            name="fecha_ultima_actualizacion",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="feedback",
            name="leido_por_admin",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="feedback",
            name="leido_por_usuario",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="feedback",
            name="numero_ticket",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="feedback",
            name="prioridad",
            field=models.CharField(
                choices=[
                    ("baja", "Baja"),
                    ("media", "Media"),
                    ("alta", "Alta"),
                    ("urgente", "Urgente"),
                ],
                default="media",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="feedback",
            name="tiempo_resolucion",
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="feedback",
            name="titulo",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="notificacionadmin",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("feedback", "Nuevo Feedback"),
                    ("sistema", "Notificación del Sistema"),
                    ("ticket", "Nuevo Ticket"),
                    ("respuesta_ticket", "Nueva Respuesta en Ticket"),
                ],
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="RespuestaTicket",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("mensaje", models.TextField()),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                (
                    "es_sistema",
                    models.BooleanField(
                        default=False,
                        help_text="Si es una respuesta automática del sistema",
                    ),
                ),
                ("archivos_adjuntos", models.JSONField(blank=True, default=list)),
                (
                    "autor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respuestas_ticket",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "ticket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="respuestas",
                        to="cuentas.feedback",
                    ),
                ),
            ],
            options={
                "verbose_name": "Respuesta de Ticket",
                "verbose_name_plural": "Respuestas de Tickets",
                "ordering": ["fecha"],
            },
        ),
    ]
