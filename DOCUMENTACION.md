# Documentación Técnica y Funcional - Melissa

## Descripción General
Melissa es una plataforma web para la gestión de reservas en peluquerías, con módulos para clientes, negocios, profesionales y administración. Incluye autenticación social, análisis de visagismo con IA, sistema de notificaciones y paneles diferenciados.

---

## Estructura del Proyecto
- `melissa/`: Configuración principal de Django
- `cuentas/`: Gestión de usuarios, autenticación, feedback y tickets
- `negocios/`: Gestión de negocios, peluqueros y servicios
- `clientes/`: Reservas, calificaciones y dashboard de clientes
- `profesionales/`: Panel y perfil de profesionales
- `chat/`: Mensajería y chat en tiempo real
- `ia_visagismo/`: Análisis de rostro y recomendaciones de cortes con IA
- `static/` y `media/`: Archivos estáticos y subidos
- `templates/`: Plantillas HTML para cada módulo

## Tipos de Usuario
- Cliente: Reserva turnos, califica y recibe recomendaciones de IA.
- Negocio: Administra su peluquería, agenda, profesionales y servicios.
- Profesional: Gestiona su perfil, agenda y servicios ofrecidos.
- Super Admin: Acceso a métricas, feedback y gestión global.

## Flujos Principales
1. Registro y autenticación (tradicional y social)
2. Gestión de negocios y profesionales
3. Reservas y calendario
4. Chat y notificaciones
5. IA Visagismo
6. Feedback y soporte

## Seguridad
- CSRF, XSS y HSTS habilitados
- Validación de archivos y límites de tamaño
- Cookies seguras y sesiones protegidas
- Variables sensibles fuera del código fuente

## Instalación y Configuración
1. Clona el repositorio y crea un entorno virtual.
2. Instala dependencias: `pip install -r requirements.txt`
3. Crea y configura el archivo `.env` con tus variables sensibles.
4. Ejecuta migraciones: `python manage.py migrate`
5. Crea un superusuario: `python manage.py createsuperuser`
6. Ejecuta el servidor: `python manage.py runserver`

## Soporte y Contacto
- Email: soporte@melissa.com
- Documentación: [docs.melissa.com](https://docs.melissa.com)

## Licencia
Este proyecto está bajo la Licencia MIT. 