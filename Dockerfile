FROM ultralytics/ultralytics:latest

WORKDIR /app

# Instalar dependencias del sistema para OpenCV y RTSP
RUN apt-get update --fix-missing && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    sqlalchemy \
    pymysql \
    python-dotenv \
    pydantic \
    cryptography

# Copiar codigo de la aplicacion
COPY ./app ./app
COPY start.sh .

# Dar permisos de ejecucion al script
RUN chmod +x /app/start.sh

EXPOSE 8000

# Usar el script de inicio
CMD ["/bin/bash", "/app/start.sh"]
