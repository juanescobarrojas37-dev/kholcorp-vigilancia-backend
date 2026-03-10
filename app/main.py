from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import text
import os
import threading

from .api import cameras
from .database import engine, Base
from .detection_service import run_detection_service

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Kholcorp Vigilancia API",
    description="API REST para sistema de vigilancia inteligente con detección de personas usando YOLO",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(cameras.router)

@app.on_event("startup")
async def startup_event():
    """Inicia el servicio de detección en un thread separado al arrancar"""
    detection_thread = threading.Thread(
        target=run_detection_service,
        daemon=True,
        name="detection-service"
    )
    detection_thread.start()

@app.get("/")
async def root():
    return {
        "message": "Kholcorp Vigilancia API",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    from .database import SessionLocal
    from .models import Detection
    from datetime import datetime, timedelta
    from sqlalchemy import func
    import json

    db = SessionLocal()
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        # Total detecciones hoy
        total_today = db.query(func.count(Detection.id)).filter(
            Detection.timestamp >= today,
            Detection.timestamp < tomorrow
        ).scalar() or 0

        # Detecciones por hora hoy
        hourly = db.query(
            func.hour(Detection.timestamp).label('hora'),
            func.count(Detection.id).label('total')
        ).filter(
            Detection.timestamp >= today,
            Detection.timestamp < tomorrow
        ).group_by('hora').all()

        hourly_labels = [f"{h.hora}:00" for h in hourly]
        hourly_data = [h.total for h in hourly]

        # Detecciones por día ultimos 7 dias
        week_ago = today - timedelta(days=7)
        daily = db.query(
            func.date(Detection.timestamp).label('dia'),
            func.count(Detection.id).label('total')
        ).filter(
            Detection.timestamp >= week_ago
        ).group_by('dia').all()

        daily_labels = [str(d.dia) for d in daily]
        daily_data = [d.total for d in daily]

        # Ultima detección
        last = db.query(Detection).order_by(Detection.timestamp.desc()).first()
        last_time = last.timestamp.strftime("%d/%m/%Y %H:%M:%S") if last else "Sin datos"
        last_conf = f"{last.confidence:.0%}" if last and last.confidence else "N/A"

    finally:
        db.close()

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Vigilancia - Kholcorp</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; }}
            .header {{ background: linear-gradient(135deg, #1e3a8a, #1d4ed8); padding: 20px 30px; display: flex; align-items: center; gap: 15px; }}
            .header img {{ width: 40px; }}
            .header h1 {{ font-size: 22px; font-weight: 700; }}
            .header p {{ font-size: 13px; opacity: 0.8; }}
            .container {{ padding: 25px; max-width: 1200px; margin: auto; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 25px; }}
            .stat-card {{ background: #1e293b; border-radius: 12px; padding: 20px; border-left: 4px solid #3b82f6; }}
            .stat-card.green {{ border-left-color: #10b981; }}
            .stat-card.orange {{ border-left-color: #f59e0b; }}
            .stat-label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
            .stat-value {{ font-size: 36px; font-weight: 800; color: #3b82f6; }}
            .stat-card.green .stat-value {{ color: #10b981; }}
            .stat-card.orange .stat-value {{ color: #f59e0b; }}
            .stat-sub {{ font-size: 12px; color: #64748b; margin-top: 5px; }}
            .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; }}
            @media(max-width: 768px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
            .chart-card {{ background: #1e293b; border-radius: 12px; padding: 20px; }}
            .chart-card h3 {{ font-size: 14px; color: #94a3b8; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }}
            .info-card {{ background: #1e293b; border-radius: 12px; padding: 20px; }}
            .info-card h3 {{ font-size: 14px; color: #94a3b8; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }}
            .info-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #334155; }}
            .info-row:last-child {{ border-bottom: none; }}
            .info-row span:first-child {{ color: #94a3b8; }}
            .info-row span:last-child {{ color: white; font-weight: 600; }}
            .live-dot {{ width: 10px; height: 10px; background: #10b981; border-radius: 50%; display: inline-block; animation: pulse 2s infinite; margin-right: 8px; }}
            @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>📹 Dashboard Vigilancia</h1>
                <p>Kholcorp • Sistema de Detección de Personas con IA</p>
            </div>
        </div>
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Humanos detectados hoy</div>
                    <div class="stat-value">{total_today}</div>
                    <div class="stat-sub">registros en la BD</div>
                </div>
                <div class="stat-card green">
                    <div class="stat-label">Última detección</div>
                    <div class="stat-value" style="font-size:18px;padding-top:8px">{last_time}</div>
                    <div class="stat-sub">Confianza: {last_conf}</div>
                </div>
                <div class="stat-card orange">
                    <div class="stat-label">Estado del sistema</div>
                    <div class="stat-value" style="font-size:18px;padding-top:8px"><span class="live-dot"></span>ACTIVO</div>
                    <div class="stat-sub">YOLO v8 + EZVIZ</div>
                </div>
            </div>
            <div class="charts-grid">
                <div class="chart-card">
                    <h3>Detecciones por Hora (Hoy)</h3>
                    <canvas id="hourlyChart" height="200"></canvas>
                </div>
                <div class="chart-card">
                    <h3>Detecciones por Día (Últimos 7 días)</h3>
                    <canvas id="dailyChart" height="200"></canvas>
                </div>
            </div>
        </div>
        <script>
            const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
            new Chart(hourlyCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(hourly_labels)},
                    datasets: [{{
                        label: 'Personas',
                        data: {json.dumps(hourly_data)},
                        backgroundColor: 'rgba(59, 130, 246, 0.7)',
                        borderColor: '#3b82f6',
                        borderWidth: 2,
                        borderRadius: 6
                    }}]
                }},
                options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }}, x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }} }} }}
            }});
            const dailyCtx = document.getElementById('dailyChart').getContext('2d');
            new Chart(dailyCtx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(daily_labels)},
                    datasets: [{{
                        label: 'Personas',
                        data: {json.dumps(daily_data)},
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        borderColor: '#10b981',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#10b981'
                    }}]
                }},
                options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }}, x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }} }} }}
            }});
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
