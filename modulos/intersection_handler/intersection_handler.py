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

import time
import queue
from threading import Thread
from ..intersection_handler import intersecion_PTZ_v2 as inter
import matplotlib.pyplot as plt


class IntersectionHandler:
    def __init__(self, cameras):
        self.cola_desviaciones = queue.Queue()
        self.data_queue = queue.Queue()
        self.detecciones_recientes = []
        self.INTERVALO_TIEMPO = 1  # segundos
        self.cameras = cameras
        self.detections = 0
        self.detection = False
        self.move_PTZ = None
        self.aviso_cruce = False
        self.posiciones = None
        self.vectores = None
        self.punto_dron = None
        self.count = 0
        self.dir_grados = None

    def add_detection(self, camera, desviacion, timestamp):
        self.cola_desviaciones.put((camera, desviacion, timestamp))

    def process_detections(self):
        detecciones_recientes = []  # Lista para almacenar detecciones recientes
        while True:

            # Inicializar la lista para almacenar las desviaciones
            desviaciones = []
            # Inicializar listas para posiciones y orientaciones filtradas
            posiciones_filtradas = []
            orientaciones_filtradas = []
            nombres=[]

            datos = self.cola_desviaciones.get()
            if datos is None:
                time.sleep(0.1)

            camera, desv, timestamp = datos

            # Añadir detección a la lista de detecciones recientes
            detecciones_recientes.append((camera, desv, timestamp))

            # Limpiar detecciones antiguas
            tiempo_actual = time.time()
            detecciones_recientes = [d for d in detecciones_recientes if tiempo_actual - d[2] < self.INTERVALO_TIEMPO]

            # Procesar si hay detecciones simultáneas de al menos dos cámaras diferentes
            if len({d[0].name for d in detecciones_recientes}) >= 2:
                self.count=0
                time.sleep(0.1)  # Ajusta este tiempo según sea necesario
                #Espero otra detección diferente
                datos = self.cola_desviaciones.get()
                if datos is None:
                    time.sleep(0.05)

                camera, desv, timestamp = datos

                # Añadir detección a la lista de detecciones recientes
                detecciones_recientes.append((camera, desv, timestamp))
                detecciones_recientes = sorted(detecciones_recientes, key=lambda deteccion: deteccion[0].name)

                # Limpiar detecciones antiguas
                num_camaras_detectadas = len({d[0].name for d in detecciones_recientes})
                    
                if num_camaras_detectadas >= 3:
                    # Procesar con tres detecciones
                    # Recorrer la lista de detecciones recientes
                    camaras_procesadas = set()
                    for deteccion in detecciones_recientes:
                        # Cada 'deteccion' es una tupla que contiene (cam, desv_x, desv_y, timestamp)
                        camera, desv, timestamp = deteccion
                        # Verificar si la cámara ya ha sido procesada
                        if camera.name not in camaras_procesadas:
                            # Añadir la desviación a la lista
                            desviaciones.append((desv))
                            #desviaciones.append((0,0))
                            #print("desviacion: ", desv, " de la cámara: ", camera.name)

                            # Marcar la cámara como procesada
                            camaras_procesadas.add(camera.name)
                    # Crear un conjunto de nombres cámaras que han detectado algo
                    camaras_detectadas = {d[0].name for d in detecciones_recientes}
                    # Filtrar posiciones y orientaciones
                    for i, camera in enumerate(self.cameras):
                        if camera.name in camaras_detectadas:

                            # print(camera.name, "Posición:",camera.position, "Orientacion: ",camera.orientation)

                            nombres.append(camera.name)
                            posiciones_filtradas.append(camera.position)
                            orientaciones_filtradas.append(camera.orientation)
                        if i == len(self.cameras) - 1:
                            posiciones_filtradas.append(camera.position)
                    
                    # for i, desviacion in enumerate(desviaciones):
                    #     print("Desviación ",i," :",desviacion)
                    #     pass

                    direcciones_finales=[(a[0] + b[0], a[1] + b[1]) for a,b in zip(orientaciones_filtradas, desviaciones)]

                    # for i, direcc_final in enumerate(direcciones_finales):
                    #     print("direcciones_finales ",i," :",direcc_final)
                    #     pass

                    # Aquí calcularías la intersección usando los datos de detecciones recientes
                    self.punto_dron, direccionPTZ, self.dir_grados, direcciones = inter.intersecion_dir_PTZ(posiciones_filtradas, orientaciones_filtradas, desviaciones)
                    #Enviar datos para plotear 
                    self.move_PTZ=direccionPTZ
                    self.data_queue.put((posiciones_filtradas, direcciones, self.punto_dron))
                    self.posiciones = posiciones_filtradas[:-1]
                    self.vectores = direcciones[:-1]
                    #print("El dron está en:", self.punto_dron)
                    # print("La dirección que debe tomar la cámara PTZ es: ", direccionPTZ)
                    # print(" ")
                    # print(" ")

                    # Limpiar las detecciones después del procesamiento
                    detecciones_recientes.clear()
                    time.sleep(0.1)

                elif num_camaras_detectadas == 2:
                    # Procesar con dos detecciones

                    camaras_procesadas = set()
                    for deteccion in detecciones_recientes:
                        # Cada 'deteccion' es una tupla que contiene (cam, desv_x, desv_y, timestamp)
                        camera, desv, timestamp = deteccion
                        # Verificar si la cámara ya ha sido procesada
                        if camera.name not in camaras_procesadas:
                            # Añadir la desviación a la lista
                            desviaciones.append((desv))
                            #desviaciones.append((0,0))
                            #print("desviacion: ", desv, " de la cámara: ", camera.name)

                            # Marcar la cámara como procesada
                            camaras_procesadas.add(camera.name)
                    # Crear un conjunto de nombres de cámaras que han detectado algo
                    camaras_detectadas = {d[0].name for d in detecciones_recientes}
                    # Filtrar posiciones y orientaciones

                    for i, camera in enumerate(self.cameras):
                        if camera.name in camaras_detectadas:
                            
                            #print(camera.name, "Posición:",camera.position, "Orientacion: ",camera.orientation)

                            nombres.append(camera.name)
                            posiciones_filtradas.append(camera.position)
                            orientaciones_filtradas.append(camera.orientation)
                        if i == len(self.cameras) - 1:
                            posiciones_filtradas.append(camera.position)

                    # for i, desviacion in enumerate(desviaciones):
                    #     print("Desviación ",i," :",desviacion)
                    #     pass

                    direcciones_finales=[(a[0] + b[0], a[1] + b[1]) for a,b in zip(orientaciones_filtradas, desviaciones)]

                    # for i, direcc_final in enumerate(direcciones_finales):
                    #     print("direcciones_finales ",i," :",direcc_final)
                    #     pass

                            
                    # Aquí calcularías la intersección usando los datos de detecciones recientes
                    self.punto_dron, direccionPTZ, self.dir_grados, direcciones = inter.intersecion_dir_PTZ(posiciones_filtradas, orientaciones_filtradas, desviaciones)
                    #Enviar datos para plotear 
                    self.move_PTZ=direccionPTZ
                    self.data_queue.put((posiciones_filtradas, direcciones, self.punto_dron))
                    self.posiciones = posiciones_filtradas[:-1]
                    self.vectores = direcciones[:-1]

                    #print("El dron está en:", self.punto_dron)
                    # print("La dirección que debe tomar la cámara PTZ es: ", direccionPTZ)
                    # print(" ")
                    # print(" ")

                    # Limpiar las detecciones después del procesamiento
                    detecciones_recientes.clear()
                    time.sleep(0.1)

            self.cola_desviaciones.task_done()

    def count_cameras_with_detection(self):
        no_det = 1
        det = 1
        while True:    
            count = 0 # Ponemos a 0 el contador del número de cámaras que hay detectando
            for camera in self.cameras:
                if camera.detection:
                    count += 1 # Sumamos una cámara al contador por cada cámra que está detectando

            if count == 0: # Si no hay ninguna cámara detectando reiniciamos el contador de deteciones y actualizamos el de no deteciones
                det = 1
                no_det += 1

            else:
                det += 1 # De lo contrario actualizamos el de deteciones y reiniciamos el de no detectiones
                no_det = 1

            if self.punto_dron is not None: 
                self.detection = True 
            else:
                self.detection = False
            
            # if det % 5 == 0 and self.detection == False: self.detection = True #Si hay cinco deteciones seguidas activo el módulo

            self.detections = count # Actualizo el valor del número de cámara detectando
            time.sleep(0.1)

    def control_aviso_cruce(self):
        time.sleep(4)
        self.aviso_cruce = False
    
    def actualizacion_pos(self):
        while True:
            time.sleep(0.1)
            self.count += 1
            if self.count == 10:
                self.move_PTZ = None
                self.punto_dron = None
                self.count = 0
        
    def start_processing_thread(self):
        processing_thread = Thread(target=self.process_detections)
        count_cameras_with_detection_thread = Thread(target=self.count_cameras_with_detection)
        actualizacion_pos_thread = Thread(target=self.actualizacion_pos)
        processing_thread.start()
        count_cameras_with_detection_thread.start()
        actualizacion_pos_thread.start()
