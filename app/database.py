from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Obtener variables de entorno - soporta ambos formatos DB_* y MYSQL_*
DB_HOST = os.getenv("DB_HOST") or os.getenv("MYSQL_HOST", "juaner222_vigilancia-db")
DB_PORT = os.getenv("DB_PORT") or os.getenv("MYSQL_PORT", "3306")
DB_USER = os.getenv("DB_USER") or os.getenv("MYSQL_USER", "root")
DB_PASS = os.getenv("DB_PASS") or os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME") or os.getenv("MYSQL_DB", "vigilancia_ai")

# URL de conexion a MySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear engine con pool de reconexion
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"connect_timeout": 30}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
