# Configuración de Google OAuth para Melissa

## Resumen de Cambios Realizados

### ✅ **Problemas Solucionados:**

1. **Plantilla de confirmación de email sin estilos**
   - ✅ Creada plantilla `email_confirm.html` con estilos modernos
   - ✅ Diseño responsive y profesional

2. **Autenticación simplificada**
   - ✅ Desactivada verificación de email obligatoria (`ACCOUNT_EMAIL_VERIFICATION = 'none'`)
   - ✅ Login simplificado: solo usuario/email + contraseña
   - ✅ Plantilla de login rediseñada y más intuitiva

3. **Google OAuth mejorado**
   - ✅ Configuraciones actualizadas en `settings.py`
   - ✅ Plantillas con botón de Google OAuth funcional

## 🔧 **Configuración de Google OAuth**

### Paso 1: Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google+ (si no está habilitada)

### Paso 2: Configurar Credenciales OAuth

1. Ve a **APIs & Services** > **Credentials**
2. Haz clic en **Create Credentials** > **OAuth 2.0 Client IDs**
3. Selecciona **Web application**
4. Configura las URLs autorizadas:
   ```
   http://localhost:8000/accounts/google/login/callback/
   http://127.0.0.1:8000/accounts/google/login/callback/
   ```
5. Guarda el **Client ID** y **Client Secret**

### Paso 3: Configurar en Django Admin

1. Inicia el servidor: `python manage.py runserver`
2. Ve a `http://localhost:8000/admin/`
3. Inicia sesión como superusuario
4. Ve a **Sites** y edita el sitio existente:
   - **Domain name**: `localhost:8000`
   - **Display name**: `Melissa`
5. Ve a **Social Applications** > **Add social application**
6. Configura:
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client ID**: [Tu Client ID de Google]
   - **Secret key**: [Tu Client Secret de Google]
   - **Sites**: Selecciona `localhost:8000`

### Paso 4: Verificar Configuración

1. Ve a `http://localhost:8000/accounts/login/`
2. Deberías ver el botón "Continuar con Google"
3. Al hacer clic, debería redirigir a Google para autenticación

## 📝 **Configuraciones en settings.py**

```python
# Google OAuth Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# Configuraciones adicionales para autenticación social
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_LOGIN_ON_GET = True
```

## 🎯 **Autenticación Simplificada**

### Cambios Realizados:

1. **Verificación de email desactivada**
   ```python
   ACCOUNT_EMAIL_VERIFICATION = 'none'
   ```

2. **Login simplificado**
   - Solo requiere usuario/email y contraseña
   - No requiere verificación de email
   - Proceso más rápido y directo

3. **Plantillas mejoradas**
   - Diseño moderno y responsive
   - Mensajes de error claros
   - Navegación intuitiva

## 🚀 **Cómo Probar**

### 1. Registro de Usuario
```bash
# Ve a http://localhost:8000/accounts/signup/
# Completa el formulario
# Deberías ser redirigido automáticamente sin verificación de email
```

### 2. Login de Usuario
```bash
# Ve a http://localhost:8000/accounts/login/
# Ingresa usuario/email y contraseña
# Deberías iniciar sesión inmediatamente
```

### 3. Google OAuth
```bash
# En la página de login, haz clic en "Continuar con Google"
# Deberías ser redirigido a Google para autenticación
# Después de autorizar, regresarás a Melissa autenticado
```

## 🔍 **Solución de Problemas**

### Error: "No module named 'allauth'"
```bash
pip install django-allauth
```

### Error: "Client ID not found"
- Verifica que hayas configurado la aplicación social en Django Admin
- Asegúrate de que el Client ID y Secret sean correctos

### Error: "Redirect URI mismatch"
- Verifica las URLs autorizadas en Google Cloud Console
- Asegúrate de que coincidan exactamente con las URLs de callback

### Error: "Site not found"
- Verifica que el sitio esté configurado en Django Admin
- Asegúrate de que la aplicación social esté asociada al sitio correcto

## 📋 **Comandos Útiles**

```bash
# Crear superusuario
python manage.py createsuperuser

# Verificar configuración
python manage.py check

# Iniciar servidor
python manage.py runserver

# Recolectar archivos estáticos
python manage.py collectstatic
```

## 🎨 **Plantillas Creadas/Modificadas**

1. ✅ `templates/account/email_confirm.html` - Confirmación de email
2. ✅ `templates/account/login.html` - Login simplificado
3. ✅ `templates/account/logout.html` - Logout mejorado
4. ✅ `templates/account/signup.html` - Registro (ya existía)

## 🔐 **Seguridad**

- Las credenciales de Google OAuth están configuradas para desarrollo
- En producción, usa variables de entorno para las credenciales
- Cambia `DEBUG = False` en producción
- Usa HTTPS en producción

## 📞 **Soporte**

Si tienes problemas con la configuración:
1. Verifica que todos los pasos se hayan seguido correctamente
2. Revisa los logs del servidor para errores específicos
3. Asegúrate de que las URLs de callback coincidan exactamente 