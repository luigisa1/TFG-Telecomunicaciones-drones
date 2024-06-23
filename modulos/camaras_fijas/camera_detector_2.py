"""
Este script realiza un análisis de datos preliminar sobre un conjunto de datos específico.

Proporciona estadísticas descriptivas, visualizaciones iniciales, y una exploración de los datos faltantes. Está diseñado para ser ejecutado como un paso inicial en el análisis de datos para ayudar en la comprensión general del conjunto de datos.

Uso:
    python script_analisis_preliminar.py <ruta_al_archivo_de_datos>

Dependencias:
    pandas, matplotlib

Autor: Tu Nombre
Fecha: 2024-03-07
"""

from ultralytics import YOLO
import queue
import threading
import time
from ..calculos import operaciones as op

class CameraDetector:
    def __init__(self, camera, detection_queue, model, size):
        self.camera = camera
        self.detection_queue = detection_queue
        self.model = YOLO(model)
        self.size = size
        self.det_cons = 0
        self.flag_comprobacion_inicial = False
        self.ids_deterctados = {}
        
        
    def detect(self):
        print("Iniciando deteciones en cámara: ",self.camera.name)
        # results = self.model.track(self.camera.source, conf=0.1, show=False , stream=True, verbose=False, imgsz=self.size, persist=True)
        results = self.model.track(self.camera.source, conf = 0.1, show = True , stream = True, verbose = False, imgsz = self.size, persist = True)
        for r in results:
            if self.camera.activado:
                if r.boxes.conf.size(0) > 0:
                    if not self.flag_comprobacion_inicial: self.comprobacion_id(r.boxes)
                    if not self.camera.detection:
                        self.det_cons += 1
                        if self.det_cons == 5:
                            self.det_cons = 0
                            self.camera.detection=True
                    timestamp = time.time()
                    for box in r.boxes:
                        xyxy = box.xyxy
                        desv = op.desviaciones(self.camera.image_size[0], self.camera.image_size[1], self.camera.field_of_view[0], self.camera.field_of_view[1], xyxy)
                        self.detection_queue.put((self.camera, desv, timestamp))
                else:
                    self.camera.detection = False
            else:
                self.camera.detection = False
    
    def comprobacion_inicial(self):
        time.sleep(10)
        self.flag_comprobacion_inicial = True

    def comprobacion_id(self, boxes):
        pass


        
        
