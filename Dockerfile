FROM ultralytics/ultralytics:latest

WORKDIR /app

# Instalar solo dependencias adicionales no incluidas en la imagen base
RUN apt-get update --fix-missing -y && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/* || true

# Instalar dependencias Python adicionales
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    sqlalchemy \
    pymysql \
    cryptography \
    python-dotenv \
    pydantic

# Copiar codigo de la aplicacion
COPY ./app ./app
COPY start.sh /app/start.sh

# Dar permisos de ejecucion al script
RUN chmod +x /app/start.sh

EXPOSE 8000

# Usar el script de inicio
CMD ["/bin/bash", "/app/start.sh"]
