# Melissa - Sistema de Gestión de Citas para Peluquerías

Melissa es una plataforma web moderna para la gestión de citas y turnos en peluquerías, con un enfoque en la experiencia del usuario y la seguridad.

## 🚀 Características

- **Gestión de Negocios**: Los propietarios pueden crear y administrar sus peluquerías
- **Sistema de Reservas**: Clientes pueden reservar citas con peluqueros específicos
- **Calendario Intuitivo**: Interfaz moderna para visualizar y gestionar horarios
- **Autenticación Social**: Login con Google y Facebook
- **Galería de Trabajos**: Los peluqueros pueden mostrar sus trabajos
- **Notificaciones**: Sistema de mensajes para confirmaciones y recordatorios

## 🛠️ Tecnologías

- **Backend**: Django 5.2.3
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Autenticación**: Django Allauth
- **Imágenes**: Pillow
- **Calendario**: FullCalendar.js

## 📋 Requisitos Previos

- Python 3.8+
- pip
- virtualenv (recomendado)

## 🔧 Instalación

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd melissa
```

### 2. Crear entorno virtual
```bash
python -m venv env
# En Windows:
env\Scripts\activate
# En macOS/Linux:
source env/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
```

### 5. Configurar la base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear superusuario
```bash
python manage.py createsuperuser
```

### 7. Ejecutar el servidor
```bash
python manage.py runserver
```

## 🔐 Configuración de Seguridad

### Variables de Entorno Requeridas

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Django
SECRET_KEY=tu-secret-key-muy-segura
DEBUG=False  # En producción
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-de-aplicacion
DEFAULT_FROM_EMAIL=Melissa <tu-email@gmail.com>

# Google OAuth
GOOGLE_CLIENT_ID=tu-google-client-id
GOOGLE_CLIENT_SECRET=tu-google-client-secret
```

### Configuración de Google OAuth

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google+ 
4. Crea credenciales OAuth 2.0
5. Agrega las URLs autorizadas:
   - `http://localhost:8000/accounts/google/login/callback/` (desarrollo)
   - `https://tu-dominio.com/accounts/google/login/callback/` (producción)

### Configuración de Email

Para Gmail:
1. Activa la verificación en dos pasos
2. Genera una contraseña de aplicación
3. Usa esa contraseña en `EMAIL_HOST_PASSWORD`

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