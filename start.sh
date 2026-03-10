#!/bin/bash

echo "=========================================="
echo "Kholcorp Vigilancia - Iniciando sistema..."
echo "=========================================="

# Iniciar el servidor FastAPI directamente
# El servicio de deteccion se inicia automaticamente desde main.py
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
