#!/bin/bash
set -e

echo "🚀 Iniciando despliegue..."

# 1. Verifica que estés en la carpeta del proyecto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ No se encontró docker-compose.yml. Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

RUN apt-get update && apt-get install -y libgl1


# 2. Construye los contenedores sin cache
echo "🔧 Construyendo contenedores..."
docker compose build --no-cache

# 3. Levanta todo en segundo plano
echo "📦 Levantando contenedores..."
docker compose up -d

# 4. Espera unos segundos para que arranquen
sleep 5

# 5. Otorga permisos dentro del contenedor (opcional, solo si usas SQLite)
echo "🔐 Corrigiendo permisos (si aplica)..."
docker compose exec web chmod -R 777 /app/db.sqlite3 || true
docker compose exec web chmod -R 777 /app || true

# 6. Aplica migraciones
echo "📁 Aplicando migraciones..."
docker compose exec web python manage.py migrate

# 7. Recolecta archivos estáticos
echo "🗂️ Recolectando archivos estáticos..."
docker compose exec web python manage.py collectstatic --noinput


echo "✅ Despliegue completo. Accede a http://TU_IP y prueba la app."
