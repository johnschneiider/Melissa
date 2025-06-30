# Usa una imagen oficial de Python
FROM python:3.10

# Crea carpeta en el contenedor
WORKDIR /app

# Copia el proyecto dentro del contenedor
COPY . .

# Instala las dependencias desde el entorno virtual
RUN pip install --no-cache-dir -r env/requirements.txt

# Expone el puerto 8000
EXPOSE 8000

# Comando para iniciar el servidor de Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
