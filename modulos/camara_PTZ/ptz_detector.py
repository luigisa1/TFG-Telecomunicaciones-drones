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
import threading
import time
from ..calculos import operaciones as op
import numpy as np
import torch

px=1920 # Pixeles eje x
py=1080 # Pixeles eje y
# Calcular el area de la pantalla para luego ver si el cuadro de detección es muy grande o pequeño en comparación
area_pantalla=px*py
class PTZDetector:
    def __init__(self,detection_queue, camera_2, camera, camera_source, model_path, size):
        self.camera_2=camera_2
        self.camera = camera
        self.camera_source = camera_source
        self.model_path = model_path
        self.size=size
        self.model = self._load_model()
        self.move = False  # Controla si se debe realizar el seguimiento
        self.xyxy = None  # Última detección (bbox)
        self.detection=False
        self.consecutive_no_detections=0
        self.correccion=False
        self.movimiento_pan=None
        self.movimiento_tilt=None
        self.estado=False
        self.avisar_sdr=False
        # self.busqueda=False
        self.posicion=None
        self.activado=True
        self.perdida=False
        self.zoom=0.04
        self.det_cons=0
        self.detection_queue=detection_queue
        self.target_id = None

    def _load_model(self):
        try:
            model = YOLO(self.model_path)
            print("Modelo YOLO cargado exitosamente.")
            return model
        except Exception as e:
            print(f"Error al cargar el modelo YOLO: {e}")
            return None
  
    def detect_and_track(self):
        print("empiezo a detectar")

        detection_thread = threading.Thread(target=self.detect)
        tracking_thread = threading.Thread(target=self.tracking)
        marcar_posicion_thread=threading.Thread(target=self.marcar_posicion)

        detection_thread.start()
        tracking_thread.start()
        marcar_posicion_thread.start()

    def detect(self):

        if not self.model:
            print("Modelo YOLO no inicializado.")
            return

        print("Iniciando detección YOLO en tiempo real...")
        # try:
        results = self.model(self.camera_source,conf=0.2, show=True, stream=True, verbose=False, imgsz=self.size)
            # results = self.model.track(self.camera_source,conf=0.2, show=True, stream=True, verbose=False, imgsz=self.size, persist=True)

        for r in results:
            if self.activado:
                self.estado=True
                boxes = r.boxes  

                self.evaluate_detect(boxes)
                self.comprobar_correccion()
                self.aviso_perdida()
            else:
                self.detection=False
                self.move=False

        # except Exception as e:
        #     print(f"Error durante la detección: {e}")

    def tracking(self):
        while True:
            if self.move:
                variacion_zoom = op.reajuste_zoom(area_pantalla, self.xyxy, self.zoom)
                self.movimiento_pan, self.movimiento_tilt, self.correccion = op.movimiento(px, py, self.zoom, self.xyxy)
                self.camera.move_relative_zoom(self.movimiento_pan, self.movimiento_tilt, 0.5, 0.5, variacion_zoom, 1)
                t=self.calcular_tiempo_espera(self.movimiento_pan,self.movimiento_tilt)
                time.sleep(0.35)
            else:
                time.sleep(0.1)
    
    def calcular_tiempo_espera(self, pan, tilt):
        #120º/s y 75º/s
        t_pan=pan*2*360/120
        t_tilt=tilt*180/75
        t=abs(max(t_pan,t_tilt,0.15))
        return t
    
    def evaluate_detect(self, boxes):
        if boxes.conf.size(0) > 0: #Si hay detecciones
            timestamp = time.time()
            # print("boxes: ", boxes.xyxy)
            if boxes.xyxy.shape[0] > 1: #Si hay más de una detección
                if self.xyxy is not None: #Si ya se ha asignado un xyxy
                    print("Hay más de una detecion y ya se ha asignado un id")
                    self.comprobar_det_cercana(boxes)
                    self.move = True
                else:
                    self.xyxy=boxes[0].xyxy #Si no se ha asignado un xyxy
                    print("Hay más de una detecion y ya NO se ha asignado un id")
            else: #Si solo hay una detección
                if self.detection: #Si ya he detectado algo anteiormente
                    if self.comprobar_det_cercana(boxes):
                        print("Solo hay una detecion ya habia detectado algo y la nueva det está lo suficiente cerca")
                        self.xyxy = boxes[0].xyxy 
                        self.move = True
                    else:
                        self.move = False
                        print("Solo hay una detecion ya habia detectado algo y la nueva det NO está lo suficiente cerca")
                else: # Si no he detectado nada anteriormente
                    self.xyxy = boxes[0].xyxy 
                    self.move = True
                    print("Solo hay una detecion ya NO habia detectado algo ")

            FoVh=op.calc_fov(self.zoom,0)
            FoVv=op.calc_fov(self.zoom,1)
            #print("Campos de visión: ",FoVh,FoVv)  AAAAAAAAAAAAAAAAAARRRREEEEEEEEEEEGLLLLAAAAAAAAAAAARRRRRRRRRR
            desv = op.desviaciones(self.camera_2.image_size[0], self.camera_2.image_size[1], 61, 33, self.xyxy)
            #print("Desviación :",desv)
            self.detection_queue.put((self.camera_2, desv, timestamp))
            self.consecutive_no_detections=0
            self.aviso_deteccion()
            
        else:
            self.move=False
            if self.detection:
                self.consecutive_no_detections+=1

    def comprobar_det_cercana(self, boxes):
        det_ant = self.xyxy.flatten()

        cx_ant = (det_ant[0] + det_ant[2]) / 2
        cy_ant = (det_ant[1] + det_ant[3]) / 2

        cx_act = (boxes.xyxy[:, 0] + boxes.xyxy[:, 2]) / 2
        cy_act = (boxes.xyxy[:, 1] + boxes.xyxy[:, 3]) / 2

        dist = torch.sqrt((cx_act - cx_ant) ** 2 + (cy_act - cy_ant) ** 2)
        print(dist)

        indice = torch.argmin(dist)
        self.xyxy = boxes[indice].xyxy

        if torch.any(dist < 100):
            return True

    def aviso_deteccion(self):
        if not self.detection:
            self.det_cons += 1
            if self.det_cons == 5:
                self.det_cons = 0
                self.detection = True


    def aviso_perdida(self):
        if self.consecutive_no_detections == 100:
            self.consecutive_no_detections = 0
            self.detection = False
            # self.busqueda=True
            self.perdida = True
            # #self.avisar_sdr=True
            # print("perdida")
    
    def comprobar_correccion(self):
        if self.consecutive_no_detections==10 and self.correccion:
            # print(" Movimiento para cuando perdemos el dron !!!!!!! ")                
            self.movimiento_pan=self.movimiento_pan*2
            self.movimiento_tilt=self.movimiento_tilt*3 
            if self.movimiento_pan>1:
                self.movimiento_pan=1
            if self.movimiento_tilt>1:
                self.movimiento_tilt=1
            self.camera.move_relative(self.movimiento_pan,self.movimiento_tilt,0.7,1)

    def marcar_posicion(self):
        while True:
            if self.move:
                pan,tilt=self.camera.get_current_pan_tilt()
                pan_corregido=pan*180
                tilt_corregido=90-(tilt*90)
                self.camera_2.orientation=(-pan_corregido, tilt_corregido)
                pan=pan*360
                tilt=tilt*180
                self.zoom=self.camera.get_current_zoom()
            else:
                self.posicion=None        
            time.sleep(0.1)

    def buscar_por_aviso_ih(self,pan,tilt):
        self.camera.move_abspantilt(pan,tilt,1,0)