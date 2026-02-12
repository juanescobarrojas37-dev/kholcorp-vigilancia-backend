FROM python:3.11-slim

WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy mysql-connector-python pymysql python-dotenv pydantic

# Copiar código de la aplicación
COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
