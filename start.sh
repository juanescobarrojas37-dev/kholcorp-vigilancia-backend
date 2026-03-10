#!/bin/bash
set -e

echo "=========================================="
echo "Kholcorp Vigilancia - Iniciando sistema..."
echo "=========================================="

# Esperar a que MySQL esté listo
echo "Esperando conexión a la base de datos..."
until python3 -c "import sqlalchemy; from sqlalchemy import create_engine; e = create_engine('mysql+pymysql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}'); e.connect()" 2>/dev/null; do
  echo "MySQL no disponible, esperando 5 segundos..."
  sleep 5
done
echo "MySQL conectado!"

# Iniciar servicio de detección en background
echo "Iniciando servicio de detección YOLO..."
python3 -m app.detection_service &
DETECTION_PID=$!
echo "Servicio de detección iniciado con PID: $DETECTION_PID"

# Iniciar servidor FastAPI
echo "Iniciando API FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
