import cv2
import os
import time
from ultralytics import YOLO
from datetime import datetime
from .database import SessionLocal
from .models import Detection, Camera
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectionService:
    def __init__(self):
        self.camera_url = os.getenv('CAMERA_URL', '')
        self.model = None
        self.running = False
        
    def load_model(self):
        """Carga el modelo YOLO"""
        logger.info("Cargando modelo YOLO...")
        self.model = YOLO('yolov8n.pt')
        logger.info("Modelo YOLO cargado")
    
    def get_or_create_camera(self, db):
        """Obtiene o crea la cámara principal en la BD"""
        camera = db.query(Camera).filter(Camera.id == 1).first()
        if not camera:
            camera = Camera(
                name="EZVIZ Principal",
                rtsp_url=self.camera_url,
                location="Entrada principal",
                status="active"
            )
            db.add(camera)
            db.commit()
            db.refresh(camera)
            logger.info("Cámara creada en base de datos")
        return camera
    
    def save_detections(self, db, camera_id, detections):
        """Guarda cada persona detectada como una fila en la BD"""
        try:
            for det in detections:
                bbox = det['bbox']  # [x1, y1, x2, y2]
                detection = Detection(
                    camera_id=camera_id,
                    detection_type="person",
                    confidence=det['confidence'],
                    bbox_x=int(bbox[0]),
                    bbox_y=int(bbox[1]),
                    bbox_width=int(bbox[2] - bbox[0]),
                    bbox_height=int(bbox[3] - bbox[1]),
                    timestamp=datetime.utcnow()
                )
                db.add(detection)
            db.commit()
            logger.info(f"Guardadas {len(detections)} detecciones")
        except Exception as e:
            logger.error(f"Error guardando detecciones: {e}")
            db.rollback()
    
    def run(self):
        """Ejecuta el servicio de detección continua"""
        logger.info(f"Iniciando servicio de detección - URL: {self.camera_url}")
        
        if not self.camera_url:
            logger.error("CAMERA_URL no configurada, servicio detenido")
            return
        
        # Esperar a que la BD esté disponible
        time.sleep(10)
        
        self.load_model()
        
        db = SessionLocal()
        try:
            camera = self.get_or_create_camera(db)
            camera_id = camera.id
        except Exception as e:
            logger.error(f"Error accediendo a BD: {e}")
            db.close()
            return
        finally:
            db.close()
        
        self.running = True
        retry_count = 0
        
        while self.running:
            cap = cv2.VideoCapture(self.camera_url)
            
            if not cap.isOpened():
                retry_count += 1
                logger.warning(f"No se pudo conectar a cámara (intento {retry_count}). Reintentando en 30s...")
                time.sleep(30)
                continue
            
            logger.info("Conectado a la cámara. Procesando frames...")
            retry_count = 0
            frame_count = 0
            
            while self.running:
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning("Fallo al leer frame, reconectando...")
                    break
                
                # Analizar cada 60 frames (~2 segundos a 30fps)
                if frame_count % 60 == 0:
                    results = self.model(frame, classes=[0], verbose=False)
                    detections = []
                    
                    for result in results:
                        for box in result.boxes:
                            conf = float(box.conf[0])
                            if conf > 0.45:
                                detections.append({
                                    'confidence': conf,
                                    'bbox': box.xyxy[0].tolist()
                                })
                    
                    if detections:
                        db = SessionLocal()
                        try:
                            self.save_detections(db, camera_id, detections)
                        finally:
                            db.close()
                        logger.info(f"Frame {frame_count}: {len(detections)} persona(s) detectada(s)")
                
                frame_count += 1
                time.sleep(0.033)  # ~30fps
            
            cap.release()

def run_detection_service():
    """Función para correr el servicio en un thread"""
    service = DetectionService()
    service.run()

if __name__ == "__main__":
    run_detection_service()
