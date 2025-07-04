# Generated by Django 5.2.3 on 2025-07-01 01:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalisisVisagismo",
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
                (
                    "imagen_original",
                    models.ImageField(upload_to="visagismo/originales/"),
                ),
                (
                    "imagen_procesada",
                    models.ImageField(
                        blank=True, null=True, upload_to="visagismo/procesadas/"
                    ),
                ),
                ("forma_cara", models.CharField(blank=True, max_length=50)),
                ("tipo_cabello", models.CharField(blank=True, max_length=50)),
                ("color_cabello", models.CharField(blank=True, max_length=50)),
                ("color_ojos", models.CharField(blank=True, max_length=50)),
                ("tono_piel", models.CharField(blank=True, max_length=50)),
                ("medidas_faciales", models.JSONField(blank=True, default=dict)),
                ("recomendaciones", models.JSONField(blank=True, default=list)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("procesando", "Procesando"),
                            ("completado", "Completado"),
                            ("error", "Error"),
                        ],
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-fecha_creacion"],
            },
        ),
        migrations.CreateModel(
            name="RecomendacionCorte",
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
                ("nombre_corte", models.CharField(max_length=100)),
                ("descripcion", models.TextField()),
                (
                    "imagen_ejemplo",
                    models.ImageField(
                        blank=True, null=True, upload_to="visagismo/cortes/"
                    ),
                ),
                ("confianza", models.FloatField(default=0.0)),
                (
                    "categoria",
                    models.CharField(
                        choices=[
                            ("corto", "Corto"),
                            ("medio", "Medio"),
                            ("largo", "Largo"),
                            ("asimetrico", "Asimétrico"),
                            ("capas", "Capas"),
                            ("degradado", "Degradado"),
                        ],
                        max_length=50,
                    ),
                ),
                ("activo", models.BooleanField(default=True)),
                (
                    "analisis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cortes_recomendados",
                        to="ia_visagismo.analisisvisagismo",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HistorialVisagismo",
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
                ("fecha_consulta", models.DateTimeField(auto_now_add=True)),
                (
                    "satisfaccion",
                    models.IntegerField(
                        blank=True,
                        choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)],
                        null=True,
                    ),
                ),
                ("comentarios", models.TextField(blank=True)),
                (
                    "analisis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ia_visagismo.analisisvisagismo",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "corte_seleccionado",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="ia_visagismo.recomendacioncorte",
                    ),
                ),
            ],
            options={
                "ordering": ["-fecha_consulta"],
            },
        ),
    ]
