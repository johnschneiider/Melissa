# Melissa - Sistema de Gestión de Citas para Peluquerías

Melissa es una plataforma SaaS para la gestión de reservas en peluquerías, con módulos para clientes, negocios, profesionales y administración. Incluye autenticación social, análisis de visagismo con IA, sistema de notificaciones y paneles diferenciados.

---

## 🚀 Características principales
- Gestión de negocios y peluqueros
- Sistema de reservas y calendario
- Autenticación social (Google, Facebook)
- Paneles diferenciados para cada tipo de usuario
- Chat en tiempo real
- Análisis de visagismo con IA
- Sistema de feedback y soporte
- Seguridad avanzada y validación de archivos

## 🏗️ Estructura del Proyecto
- `melissa/`: Configuración principal de Django
- `cuentas/`: Gestión de usuarios, autenticación, feedback y tickets
- `negocios/`: Gestión de negocios, peluqueros y servicios
- `clientes/`: Reservas, calificaciones y dashboard de clientes
- `profesionales/`: Panel y perfil de profesionales
- `chat/`: Mensajería y chat en tiempo real
- `ia_visagismo/`: Análisis de rostro y recomendaciones de cortes con IA
- `static/` y `media/`: Archivos estáticos y subidos
- `templates/`: Plantillas HTML para cada módulo

## 👤 Tipos de Usuario
- Cliente
- Negocio
- Profesional
- Super Admin

## 🚦 Flujos Principales
1. Registro y autenticación (tradicional y social)
2. Gestión de negocios y profesionales
3. Reservas y calendario
4. Chat y notificaciones
5. IA Visagismo
6. Feedback y soporte

## ⚙️ Instalación y Configuración
1. Clona el repositorio y crea un entorno virtual.
2. Instala dependencias: `pip install -r requirements.txt`
3. Crea y configura el archivo `.env` con tus variables sensibles.
4. Ejecuta migraciones: `python manage.py migrate`
5. Crea un superusuario: `python manage.py createsuperuser`
6. Ejecuta el servidor: `python manage.py runserver`

## 🔒 Seguridad
- CSRF, XSS y HSTS habilitados
- Validación de archivos y límites de tamaño
- Cookies seguras y sesiones protegidas
- Variables sensibles fuera del código fuente

## 🧪 Testing
- Pruebas unitarias básicas en cada app
- Scripts de debug para reservas y horarios
- Logging de errores y actividades críticas

## 🤝 Contribuir
1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaFeature`)
3. Commit tus cambios (`git commit -m 'Agrega NuevaFeature'`)
4. Push a la rama (`git push origin feature/NuevaFeature`)
5. Abre un Pull Request

## 📄 Licencia
Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ⚠️ Notas Importantes
- Nunca subas el archivo `.env` al repositorio
- Siempre usa HTTPS en producción
- Mantén actualizadas las dependencias
- Revisa regularmente los logs de seguridad
- Haz backups regulares de la base de datos

## 🚀 Despliegue en Producción

### 1. Configuración del servidor
```bash
# Instalar dependencias del sistema
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql

# Crear usuario para la aplicación
sudo adduser melissa
sudo usermod -aG sudo melissa
```

### 2. Configurar PostgreSQL
```bash
sudo -u postgres createuser melissa
sudo -u postgres createdb melissa_db
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE melissa_db TO melissa;
\q
```

### 3. Configurar Gunicorn
```bash
pip install gunicorn
```

Crear archivo `gunicorn.service`:
```ini
[Unit]
Description=Melissa Gunicorn daemon
After=network.target

[Service]
User=melissa
Group=www-data
WorkingDirectory=/home/melissa/melissa
ExecStart=/home/melissa/melissa/env/bin/gunicorn --workers 3 --bind unix:/home/melissa/melissa/melissa.sock melissa.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 4. Configurar Nginx
```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/melissa/melissa;
    }

    location /media/ {
        root /home/melissa/melissa;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/melissa/melissa/melissa.sock;
    }
}
```

### 5. Configuraciones de seguridad adicionales
```bash
# Configurar firewall
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Configurar SSL con Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

## 🔒 Medidas de Seguridad Implementadas

### 1. Configuración de Django
- ✅ CSRF Protection habilitado
- ✅ XSS Protection con headers de seguridad
- ✅ Content Type Sniffing deshabilitado
- ✅ Frame Options configurado
- ✅ HSTS habilitado
- ✅ Cookies seguras configuradas

### 2. Validación de Entrada
- ✅ Sanitización de datos de entrada
- ✅ Validación de archivos de imagen
- ✅ Límites de tamaño de archivo
- ✅ Validación de tipos de archivo

### 3. Autenticación y Autorización
- ✅ Login requerido para funciones críticas
- ✅ Verificación de permisos por usuario
- ✅ Protección contra acceso no autorizado
- ✅ Logging de actividades importantes

### 4. Manejo de Archivos
- ✅ Validación de tipos de imagen
- ✅ Límites de tamaño (5MB máximo)
- ✅ Almacenamiento seguro en directorios específicos
- ✅ Eliminación segura de archivos

## 📁 Estructura del Proyecto

```
melissa/
├── melissa/              # Configuración principal de Django
├── cuentas/              # Gestión de usuarios y autenticación
├── negocios/             # Gestión de negocios y peluqueros
├── clientes/             # Sistema de reservas para clientes
├── templates/            # Plantillas HTML
├── static/               # Archivos estáticos (CSS, JS, imágenes)
├── media/                # Archivos subidos por usuarios
├── logs/                 # Archivos de log
├── requirements.txt      # Dependencias de Python
├── manage.py            # Script de gestión de Django
└── .env                 # Variables de entorno (no incluir en git)
```

## 🐛 Solución de Problemas

### Error de migraciones
```bash
python manage.py makemigrations --empty app_name
python manage.py migrate
```

### Error de permisos de archivos
```bash
sudo chown -R www-data:www-data /home/melissa/melissa/media/
sudo chmod -R 755 /home/melissa/melissa/media/
```

### Error de conexión a la base de datos
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar conexión
sudo -u postgres psql -d melissa_db
```

## 📞 Soporte

- **Email**: soporte@melissa.com
- **Teléfono**: +57 300 123 4567
- **Documentación**: [docs.melissa.com](https://docs.melissa.com)

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## ⚠️ Notas Importantes

- **Nunca** subas el archivo `.env` al repositorio
- **Siempre** usa HTTPS en producción
- **Mantén** actualizadas las dependencias
- **Revisa** regularmente los logs de seguridad
- **Haz** backups regulares de la base de datos 