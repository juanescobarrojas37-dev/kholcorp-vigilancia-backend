from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .api import cameras

app = FastAPI(
    title="Kholcorp Vigilancia API",
    description="API REST para sistema de vigilancia inteligente con detección de personas usando YOLO",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

# Incluir routers
app.include_router(cameras.router)

async def root():
    return {
        "message": "Kholcorp Vigilancia API",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
