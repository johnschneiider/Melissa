# Generated manually for recordatorio fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0004_alter_reserva_cliente_alter_reserva_peluquero_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='recordatorio_dia_enviado',
            field=models.BooleanField(default=False, help_text='Recordatorio de 1 día antes enviado'),
        ),
        migrations.AddField(
            model_name='reserva',
            name='recordatorio_tres_horas_enviado',
            field=models.BooleanField(default=False, help_text='Recordatorio de 3 horas antes enviado'),
        ),
    ] 