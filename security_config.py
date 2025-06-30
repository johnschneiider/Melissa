"""
Configuraciones de seguridad para Melissa
Este archivo contiene configuraciones adicionales de seguridad que pueden ser
importadas en settings.py según el entorno (desarrollo/producción).
"""

import os

def get_security_settings(debug=False):
    """
    Retorna configuraciones de seguridad según el entorno
    
    Args:
        debug (bool): True para desarrollo, False para producción
    
    Returns:
        dict: Configuraciones de seguridad
    """
    
    base_security = {
        # Headers de seguridad
        'SECURE_BROWSER_XSS_FILTER': True,
        'SECURE_CONTENT_TYPE_NOSNIFF': True,
        'X_FRAME_OPTIONS': 'DENY',
        'SECURE_HSTS_SECONDS': 31536000,
        'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
        'SECURE_HSTS_PRELOAD': True,
        
        # Configuración de sesiones
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'CSRF_COOKIE_HTTPONLY': True,
        
        # Configuración de archivos
        'FILE_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
        'DATA_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
        
        # Configuración de logging
        'LOGGING': {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                    'style': '{',
                },
                'security': {
                    'format': 'SECURITY: {levelname} {asctime} {module} {message}',
                    'style': '{',
                },
            },
            'handlers': {
                'file': {
                    'level': 'INFO',
                    'class': 'logging.FileHandler',
                    'filename': 'logs/django.log',
                    'formatter': 'verbose',
                },
                'security_file': {
                    'level': 'WARNING',
                    'class': 'logging.FileHandler',
                    'filename': 'logs/security.log',
                    'formatter': 'security',
                },
            },
            'loggers': {
                'django.security': {
                    'handlers': ['security_file'],
                    'level': 'WARNING',
                    'propagate': False,
                },
            },
            'root': {
                'handlers': ['file'],
                'level': 'INFO',
            },
        },
    }
    
    if not debug:  # Configuraciones solo para producción
        production_security = {
            # HTTPS forzado
            'SECURE_SSL_REDIRECT': True,
            'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
            
            # Cookies seguras
            'SESSION_COOKIE_SECURE': True,
            'CSRF_COOKIE_SECURE': True,
            
            # Headers adicionales
            'SECURE_REFERRER_POLICY': 'strict-origin-when-cross-origin',
            
            # Configuración de CORS más estricta
            'CORS_ALLOWED_ORIGINS': [
                'https://tu-dominio.com',
                'https://www.tu-dominio.com',
            ],
            'CORS_ALLOW_CREDENTIALS': True,
            'CORS_ALLOW_METHODS': [
                'GET',
                'POST',
                'PUT',
                'PATCH',
                'DELETE',
                'OPTIONS',
            ],
            'CORS_ALLOW_HEADERS': [
                'accept',
                'accept-encoding',
                'authorization',
                'content-type',
                'dnt',
                'origin',
                'user-agent',
                'x-csrftoken',
                'x-requested-with',
            ],
        }
        base_security.update(production_security)
    
    return base_security

def get_allowed_hosts():
    """
    Retorna la lista de hosts permitidos según el entorno
    """
    allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
    return [host.strip() for host in allowed_hosts.split(',')]

def get_database_config():
    """
    Retorna la configuración de base de datos según el entorno
    """
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and not os.getenv('DEBUG', 'True').lower() == 'true':
        # Configuración para PostgreSQL en producción
        try:
            import dj_database_url
            return dj_database_url.parse(database_url)
        except ImportError:
            pass
    
    # Configuración para SQLite en desarrollo
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }

def get_email_config():
    """
    Retorna la configuración de email
    """
    return {
        'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'EMAIL_HOST': os.getenv('EMAIL_HOST', 'smtp.gmail.com'),
        'EMAIL_PORT': int(os.getenv('EMAIL_PORT', '587')),
        'EMAIL_USE_TLS': os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true',
        'EMAIL_HOST_USER': os.getenv('EMAIL_HOST_USER', ''),
        'EMAIL_HOST_PASSWORD': os.getenv('EMAIL_HOST_PASSWORD', ''),
        'DEFAULT_FROM_EMAIL': os.getenv('DEFAULT_FROM_EMAIL', 'Melissa <noreply@melissa.com>'),
    }

def get_cache_config():
    """
    Retorna la configuración de caché
    """
    cache_url = os.getenv('CACHE_URL')
    
    if cache_url and not os.getenv('DEBUG', 'True').lower() == 'true':
        # Configuración para Redis en producción
        import django_cache_url
        return django_cache_url.parse(cache_url)
    else:
        # Configuración local en desarrollo
        return {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }

# Configuraciones de validación de archivos
ALLOWED_IMAGE_TYPES = ['jpeg', 'jpg', 'png', 'gif', 'webp']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2MB

# Configuraciones de autenticación
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Configuraciones de Allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# Configuraciones de proveedores sociales
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'verified',
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v13.0',
    }
}

# Configuraciones de validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configuraciones de middleware de seguridad
SECURITY_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Configuraciones de templates
TEMPLATE_CONTEXT_PROCESSORS = [
    'django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
]

# Configuraciones de archivos estáticos
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Configuraciones de internacionalización
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Configuraciones de archivos de media
MEDIA_URL = '/media/'
MEDIA_ROOT = 'media/'

# Configuraciones de archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = 'staticfiles/'
STATICFILES_DIRS = [
    'static/',
] 