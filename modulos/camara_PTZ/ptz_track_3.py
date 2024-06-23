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
import torch
from ultralytics import YOLO
import threading
import time
from ..calculos import operaciones as op
import numpy as np
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
        self.boxes=None
        self.target_id=None

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
        comprobar_correccion_thread = threading.Thread(target=self.comprobar_correccion)
        marcar_posicion_thread=threading.Thread(target=self.marcar_posicion)
        evaluate_perdida = threading.Thread(target=self.aviso_perdida)

        detection_thread.start()
        tracking_thread.start()
        marcar_posicion_thread.start()
        comprobar_correccion_thread.start()
        evaluate_perdida.start()

    def detect(self):

        if not self.model:
            print("Modelo YOLO no inicializado.")
            return

        print("Iniciando detección YOLO en tiempo real...")
        try:
            # results = self.model(self.camera_source,conf=0.2, show=False, stream=True, verbose=False, imgsz=self.size)
            results = self.model.track(self.camera_source,conf=0.2, show=True, stream=True, verbose=False, imgsz=self.size, persist=True)

            for r in results:
                if self.activado:
                    self.estado=True
                    self.boxes = r.boxes  
                    self.evaluate_detect()
                else:
                    self.detection=False
                    self.move=False

        except Exception as e:
            print(f"Error durante la detección: {e}")

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
    
    def evaluate_id(self):
        if self.boxes.id is not None: #Si hay id trackeados
            if self.target_id == None: 
                self.target_id = self.boxes.id[0] #Si no se ha establecido un id target lo establecemos
                print("el id es: ", self.target_id )
                self.xyxy = self.boxes.xyxy[0]
                #self.activar_move_y_enviar_datos_cola()

            elif self.target_id is not None:    
                if self.target_id in self.boxes.id:
                    print("existe el id", self.target_id )
                    print("self.boxes_id: ", self.boxes.id, "Self.targer_id: ",self.target_id)
                    self.xyxy = self.boxes.xyxy[torch.where(self.boxes.id == self.target_id)] #Si ya se ha establecido un target id y coincide actualizamos xyxy
                    #self.activar_move_y_enviar_datos_cola()
                else:
                    print("No existe el id")
                    #Calculamos el IOU sobre las demás detecciones para ver si alguna es similar 
                    iou_vect = np.array([])
                    for i, box in enumerate(self.boxes.xyxy):
                        iou = op.calcular_iou_tensor(self.xyxy.flatten(), box)
                        iou_vect=np.append(iou_vect, iou)  

                    # Encontrar índices de valores que son mayores a 0.1
                    indices = np.where(iou_vect > 0.1)[0]
                    if indices.size > 0:
                        # Encontrar el índice del máximo de los valores filtrados
                        max_index = indices[np.argmax(iou_vect[indices])]
                        self.xyxy = self.boxes.xyxy[max_index]
                        #self.activar_move_y_enviar_datos_cola()
                        #Comprobar primero si existe ese indice en el vector
                        if max_index < self.boxes.id.size(0):
                            self.target_id=self.boxes.id[max_index]
                            print("Se cambia el id: ", self.target_id )
                    
                    else:
                        pass
                        # self.move = False
                        # self.det_cons = 0
                        # if self.detection: self.consecutive_no_detections+=1
                        #Ponemos move a False
                    
        else:
            if self.boxes.xyxy.size(0)>0 and self.xyxy is not None:
                iou_vect = np.array([])
                for i, box in enumerate(self.boxes.xyxy):
                    iou = op.calcular_iou_tensor(self.xyxy.flatten(), box)
                    iou_vect = np.append(iou_vect, iou)  

                # Encontrar índices de valores que son mayores a 0.1
                indices = np.where(iou_vect > 0.1)[0]
                if indices.size > 0:
                    # Encontrar el índice del máximo de los valores filtrados
                    max_index = indices[np.argmax(iou_vect[indices])]
                    print("No existe el id pero seguimos con el seguimiento por detección coincidente")
                    self.xyxy= self.boxes.xyxy[max_index]
                    # self.activar_move_y_enviar_datos_cola()
                
                else:
                    pass
                    # self.move = False
                    # self.det_cons = 0
                    # if self.detection: self.consecutive_no_detections+=1
                    #Ponemos move a False
            else:
                pass
                # self.move = False
                # self.det_cons = 0
                # if self.detection: self.consecutive_no_detections+=1
                #Ponemos move a False
        # time.sleep(0.2)
                print("Se mantiene un segimiento ya que hay una detección proxima pero no contiene un id")


    def evaluate_detect(self):
        if self.boxes.conf.size(0) > 0:
            self.evaluate_id()
            timestamp = time.time()
            self.xyxy=self.boxes[0].xyxy 
            FoVh=op.calc_fov(self.zoom,0)
            FoVv=op.calc_fov(self.zoom,1)
            #print("Campos de visión: ",FoVh,FoVv)  AAAAAAAAAAAAAAAAAARRRREEEEEEEEEEEGLLLLAAAAAAAAAAAARRRRRRRRRR
            desv = op.desviaciones(self.camera_2.image_size[0], self.camera_2.image_size[1], 61, 33, self.xyxy)
            #print("Desviación :",desv)
            self.detection_queue.put((self.camera_2, desv, timestamp))
            if self.detection:
                self.move=True
            self.consecutive_no_detections=0
            self.aviso_deteccion()
            
        else:
            self.move=False
            if self.detection:
                self.consecutive_no_detections+=1

    def aviso_deteccion(self):
        if not self.detection:
            self.det_cons+=1
            if self.det_cons==5:
                self.det_cons=0
                self.detection=True


    def aviso_perdida(self):
        while True:
            if self.consecutive_no_detections>=100:
                self.consecutive_no_detections=0
                self.detection=False
                self.perdida=True
            time.sleep(0.1)


    
    def comprobar_correccion(self):
        while True:
            if 10<self.consecutive_no_detections<=12 and self.correccion:
                print(" Movimiento para cuando perdemos el dron !!!!!!! ")                
                self.movimiento_pan=self.movimiento_pan*2
                self.movimiento_tilt=self.movimiento_tilt*3 
                if self.movimiento_pan>1:
                    self.movimiento_pan=1
                if self.movimiento_tilt>1:
                    self.movimiento_tilt=1
                self.camera.move_relative(self.movimiento_pan,self.movimiento_tilt,0.7,1)
            time.sleep(0.1)

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