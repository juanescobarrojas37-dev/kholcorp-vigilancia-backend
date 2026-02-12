from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Obtener variables de entorno
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "vigilancia_ai")

# URL de conexión a MySQL
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# Crear engine de SQLAlchemy
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Crear session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
