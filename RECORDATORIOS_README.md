# Sistema de Recordatorios - Melissa

## 📋 Descripción

Sistema automático de recordatorios por email para citas en peluquerías. Envía recordatorios:
- **1 día antes** de la cita
- **3 horas antes** de la cita

## 🚀 Instalación

### 1. Configurar Email

Asegúrate de que el email esté configurado en `settings.py`:

```python
# Configuración de Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # O tu servidor SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-de-aplicacion'
DEFAULT_FROM_EMAIL = 'Melissa <tu-email@gmail.com>'
```

### 2. Crear Migración

```bash
python manage.py makemigrations clientes
python manage.py migrate
```

### 3. Configurar Cron Jobs

#### En Linux/Mac:
```bash
python setup_cron.py
crontab melissa_cron.txt
```

#### En Windows:
1. Abre "Programador de tareas"
2. Crea dos tareas programadas:
   - **Recordatorios 3 horas**: Cada hora
   - **Recordatorios 1 día**: Diariamente a las 9:00 AM

## 🧪 Pruebas

### Probar manualmente:
```bash
# Enviar todos los recordatorios
python manage.py enviar_recordatorios

# Solo recordatorios de 1 día
python manage.py enviar_recordatorios --tipo dia_antes

# Solo recordatorios de 3 horas
python manage.py enviar_recordatorios --tipo tres_horas
```

### Ver logs:
```bash
# Ver logs en tiempo real
tail -f logs/recordatorios.log

# Ver últimos logs
cat logs/recordatorios.log
```

## 📧 Templates de Email

### Recordatorio 1 día antes:
- **HTML**: `templates/emails/recordatorio_dia_antes.html`
- **Texto**: `templates/emails/recordatorio_dia_antes.txt`

### Recordatorio 3 horas antes:
- **HTML**: `templates/emails/recordatorio_tres_horas.html`
- **Texto**: `templates/emails/recordatorio_tres_horas.txt`

## 🔧 Configuración

### Campos agregados al modelo Reserva:
- `recordatorio_dia_enviado`: Boolean - Controla si se envió el recordatorio de 1 día
- `recordatorio_tres_horas_enviado`: Boolean - Controla si se envió el recordatorio de 3 horas

### Comando de gestión:
- **Archivo**: `clientes/management/commands/enviar_recordatorios.py`
- **Funcionalidad**: Busca reservas pendientes y envía emails automáticamente

## 📊 Monitoreo

### Logs disponibles:
- **Ubicación**: `logs/recordatorios.log`
- **Contenido**: Registro de emails enviados y errores

### Métricas:
- Número de recordatorios enviados por tipo
- Errores de envío
- Reservas procesadas

## 🛠️ Mantenimiento

### Verificar estado:
```bash
# Ver reservas con recordatorios pendientes
python manage.py shell
>>> from clientes.models import Reserva
>>> Reserva.objects.filter(recordatorio_dia_enviado=False).count()
>>> Reserva.objects.filter(recordatorio_tres_horas_enviado=False).count()
```

### Limpiar logs antiguos:
```bash
# Mantener solo últimos 30 días
find logs/ -name "*.log" -mtime +30 -delete
```

## 🔒 Seguridad

- Los emails se envían solo a reservas confirmadas o pendientes
- Se evita el envío duplicado con campos de control
- Logs detallados para auditoría
- Manejo de errores robusto

## 📝 Personalización

### Modificar horarios:
Edita `setup_cron.py` para cambiar:
- Frecuencia de recordatorios de 3 horas
- Hora del recordatorio diario

### Personalizar emails:
Modifica los templates en `templates/emails/` para:
- Cambiar diseño y contenido
- Agregar información específica del negocio
- Incluir enlaces personalizados

## 🆘 Solución de Problemas

### Email no se envía:
1. Verificar configuración SMTP en `settings.py`
2. Revisar logs en `logs/recordatorios.log`
3. Probar manualmente con el comando

### Cron jobs no funcionan:
1. Verificar que el cron esté activo: `crontab -l`
2. Revisar permisos del archivo `manage.py`
3. Verificar ruta absoluta en el cron job

### Recordatorios duplicados:
1. Verificar campos de control en la base de datos
2. Revisar lógica de filtrado en el comando
3. Limpiar campos de control si es necesario

## 📞 Soporte

Para problemas o preguntas:
1. Revisar logs primero
2. Probar comandos manualmente
3. Verificar configuración de email
4. Consultar documentación de Django para email 