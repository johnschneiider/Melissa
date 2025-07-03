# Usa una imagen oficial de Python
FROM python:3.12

# Crea carpeta en el contenedor
WORKDIR /app

# Copia solo los archivos necesarios primero para aprovechar el cache
RUN apt-get update && apt-get install -y libgl1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Copia el resto del proyecto
COPY . .


# Expone el puerto 8000
EXPOSE 8000

# Comando para iniciar el servidor de producción
CMD ["gunicorn", "melissa.wsgi:application", "--bind", "0.0.0.0:8000"]
