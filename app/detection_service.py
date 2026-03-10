import cv2
import os
import time
from ultralytics import YOLO
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Detection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectionService:
    def __init__(self):
        self.camera_url = os.getenv('CAMERA_URL', '')
        self.model = YOLO('yolov8n.pt')  # Modelo ligero para detección rápida
        self.db = SessionLocal()
        
    def detect_humans(self, frame):
        """Detecta personas en un frame usando YOLO"""
        results = self.model(frame, classes=[0])  # Clase 0 = persona
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                conf = float(box.conf[0])
                if conf > 0.5:  # Confianza mínima del 50%
                    detections.append({
                        'confidence': conf,
                        'bbox': box.xyxy[0].tolist()
                    })
        
        return detections
    
    def save_detection(self, count, confidence_avg):
        """Guarda la detección en la base de datos"""
        try:
            detection = Detection(
                camera_id=1,  # ID de la cámara principal
                person_count=count,
                confidence=confidence_avg,
                timestamp=datetime.utcnow()
            )
            self.db.add(detection)
            self.db.commit()
            logger.info(f"Detección guardada: {count} personas")
        except Exception as e:
            logger.error(f"Error guardando detección: {e}")
            self.db.rollback()
    
    def run(self):
        """Ejecuta el servicio de detección continua"""
        logger.info(f"Iniciando detección con URL: {self.camera_url}")
        
        if not self.camera_url:
            logger.error("CAMERA_URL no está configurada")
            return
        
        cap = cv2.VideoCapture(self.camera_url)
        
        if not cap.isOpened():
            logger.error("No se pudo conectar a la cámara")
            return
        
        logger.info("Conectado a la cámara. Iniciando detección...")
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                logger.warning("No se pudo leer frame, reintentando...")
                time.sleep(5)
                cap = cv2.VideoCapture(self.camera_url)
                continue
            
            # Procesar cada 30 frames (aproximadamente 1 por segundo)
            if frame_count % 30 == 0:
                detections = self.detect_humans(frame)
                
                if detections:
                    person_count = len(detections)
                    avg_confidence = sum(d['confidence'] for d in detections) / person_count
                    self.save_detection(person_count, avg_confidence)
                    logger.info(f"Detectadas {person_count} personas")
            
            frame_count += 1
            time.sleep(0.03)  # ~30 FPS
        
        cap.release()

if __name__ == "__main__":
    service = DetectionService()
    service.run()
