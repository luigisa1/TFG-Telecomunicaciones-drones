"""
Este script se encarga de manejar la lógica central de la aplicación manejando los estados y señales de los diferentes módulos para tomar las acciones corresponientes.

Autor: Luis Gimeno San Frutos 
"""

import threading
import time
import intersection_handler
from camera_detector_2 import CameraDetector
import calc_dist as cd

class CoreLogicModule:
    """
    Clase CoreLogicModule para manejar la lógica central.

    Atributos:

        comunicacion_sdr(ComunicacionSDR): Objeto de la clase ComunicacionSDR encargado de la comunicación con el SDR a través de sockets.
        ptz_barrido(PTZBarrido): Objeto de la clase PTZBarrido encargado de ralizar los diferentes barridos.
        camaras(Camara): Lista de objetos de la clase Camara.
        ptz_detector(PTZDetector): Objeto de la clase PTZDetector encargado de la detección y seguiimeinto con la cámara PTZ:
        intersection_handler(IntersectionHandler): Objeto de la clase IntersectionHandler encargado del cruce de direciones de diferentes cámarad detectando simultáneamente.
        primer_aviso(bool): Variable para indicar si ya se ha realizado el primer barrido con su corresponiente aviso al módulo SDR de que se hace.
        estado(str): Variable que indica el estado del sistema entre los 4 posibles.
        aviso_deteccion(bool): Variable que indica si se ha avisado de la detección del dron.
        aviso_perdida(bool): Varibale que indica si se ha avisado de la pérdida del dron.
        avisar_por_finalizacion_barrido(bool): Variable que indica si hay que avisar por la finalización del barrido.
        barrido_una_fija(bool) : Variable que indica que se ha mandado un barrido por la detección de una sola cámara fija.

    Métodos:

        __init__(self, camera): Constructor de la clase.
        monitorear_sistema(self): Comprueba repetidamente las variables y señales de los módulos.
        iniciar_modulos(self): Inicia todos los módulos.
        iniciar_barrido(self,selector): Inicia el barrido seleccionado.
        iniciar_camaras_fijas(self): Inicia el modelo Yolo en las cámara fijas mediante un objeto de la clase CameraDetector para cada cámara.
        iniciar_intersection_handler(self): Inicia el módulo IntersectionHandler.
        iniciar_ptz_detector(self): Inicia el módulo PTZDetector
        esperar_deteciones_ptz(self): Espera a la primera detección de la cámara PTZ para que el programa continue.
        comprobar_si_parar_barrido(self): Comprueba si el barrido ha de ser detenido.
        iniciar_conexion_SDR(self): Inicia la conexión en módulo SDR.
        esperar_alarma(self): Inicia la espera continuada de una alarma por parte del módulo SDR.
        comprobar_si_empezar_barrido(self): Comprueba si se ha de empezar un barrido.
        comprobar_camaras_fijas(self): Comprueba si solo hay una cámara fija detectando junto con otras condiciones para empezar un barrido.
        comprobar_estado(self): Comprueba el estado de los diferentes módulos para signar el estado correspondiente al sistema.
        comprobar_intersection_handler(self): Comprueba si ha habido un curce de direcciones por dos o más cámaras fijas detectando simultáneamente junto con otras condiciones para tomar las acciones correspondientes.
        comprobar_aviso(self): Comprueba si hay que avisar al módulo SDR de la detección o de la pérdida de un dron.
        comprobar_perdida(self): Comprueba si ha habido una pérdido del dron para mandar un barrido post-périda.
        espera_barrido(self): Inicia un tiempo de espera una vez mandado un barrido debido a la detección de una sola cámara fija para que no se manden barridos continuos en caso de que haya detecciones no consistentes por parte de otra cámara fija. 

    """
    def __init__(self, comunicacion_sdr, ptz_barrido, camaras, ptz_detector, intersection_handler, camera_capture, model, size, sdr):
        self.comunicacion_sdr = comunicacion_sdr
        self.ptz_barrido = ptz_barrido
        self.camaras = camaras # Lista o diccionario de objetos de cámaras fijas
        self.ptz_detector = ptz_detector
        self.intersection_handler=intersection_handler
        self.camera_capture=camera_capture
        self.primer_aviso=False
        self.estado="Perdida total"
        self.aviso_deteccion=False
        self.aviso_perdida=False
        self.avisar_por_finalizacion_barrido=False
        self.barrido_una_fija=False
        self.model = model
        self.size=size
        self.sdr=sdr
        self.detectors = []

    def monitorear_sistema(self):
        """
        Realiza las difernetes comprobaciones sobre las variables y señales de los distintos módulos.
        Se trata de un buble infinito que hace este análisis continuamente.
        """
        while True:
            self.comprobar_si_empezar_barrido()
            self.comprobar_si_parar_barrido()
            self.comprobar_camaras_fijas()
            self.comprobar_estado()
            self.comprobar_intersection_handler()
            self.comprobar_aviso()
            # self.comprobar_barrido_terminado()
            self.comprobar_perdida()
            time.sleep(0.05)

    def iniciar_modulos(self):
        """
        Inicializa los diferente módulos del sistema.
        """
        self.iniciar_camaras_fijas()                                                          # En primer lugar se inician las cámaras fijas.
        self.iniciar_intersection_handler()                                                   # En segundo lugar el módulo IntersectionHandler.
        self.iniciar_ptz_detector()                                                           # En tercer lugar el PTZDetector.
        self.comprobacion_inicial_fijas()
        espera=threading.Thread(target=self.esperar_deteciones_ptz)                           # Se espera a que la cámra PTZ haya iniciado su modelo Yolo y esté haciendo el análisis del video para continuar.
        espera.start()
        espera.join()
        comprobacion_inicial_fijas_thread=threading.Thread(target=self.comprobacion_inicial_fijas)
        comprobacion_inicial_fijas_thread.start()
        comprobacion_inicial_fijas_thread.join()

        iniciar_conexion_SDR_thread=threading.Thread(target=self.iniciar_conexion_SDR)        # Se inicia el servidor socket y se espera a que le módulo SDR esté conectado antes de continuar.
        iniciar_conexion_SDR_thread.start()
        iniciar_conexion_SDR_thread.join()

        monitorear_sistema_thread=threading.Thread(target=self.monitorear_sistema)            # Se inicia la monitorización del sistema.
        monitorear_sistema_thread.start()

        alarma_thread=threading.Thread(target=self.esperar_alarma)                            # Se inicializa el hilo que estará constantemente esperando una alarma.
        alarma_thread.start()


    def iniciar_barrido(self,selector):
        self.avisar_por_finalizacion_barrido=True
        self.ptz_barrido.iniciar_barrido(selector)          #Llamo a la función iniciar barrido del modulo de PTZ barrido

    def iniciar_camaras_fijas(self):
        for camera in self.camaras[:-1]:
            print("Inicio detector en :", camera.name)
            detector = CameraDetector(camera, self.intersection_handler.cola_desviaciones, self.model, self.size)
            self.detectors.append(detector)
            threading.Thread(target=detector.detect).start()

    def comprobacion_inicial_fijas(self):
        for detector in self.detectors:
            threading.Thread(target=detector.comprobacion_inicial)

    def iniciar_intersection_handler(self):
        self.intersection_handler.start_processing_thread()
    
    def iniciar_ptz_detector(self):
        self.ptz_detector.detect_and_track()

    def esperar_deteciones_ptz(self):
        while True:
            if self.ptz_detector.estado:
                break
            else:
                time.sleep(1)

    def comprobar_si_parar_barrido(self): 
        if self.ptz_barrido.estado and self.ptz_detector.detection:
            self.ptz_barrido.detener_barrido_por_aviso()

    def iniciar_conexion_SDR(self):
        self.comunicacion_sdr.iniciar()
        
    def esperar_alarma(self):
        self.comunicacion_sdr.recibir_alarma()

    def comprobar_si_empezar_barrido(self):
        if self.comunicacion_sdr.alarma:                #Compruebo si se ha activado una alarma
            print("inicio barrido")
            if not self.primer_aviso:
                self.comunicacion_sdr.enviar_respuesta("barrido")   #Aviso al SDR de que empiezo el primer bvarrido 
                print("primer barrido sin alarma al empezar")
                self.primer_aviso=True
                self.comunicacion_sdr.alarma=False
                self.avisar_por_finalizacion_barrido=True         
                self.iniciar_barrido(0) 
                self.camera_capture.iniciar_captura_imagenes(self.camaras[-1].source, self.camaras[-1].name, 65)
                for camera in self.camaras[:-1]:
                    self.camera_capture.iniciar_captura_imagenes(camera.source, camera.name, 5)
            else:   
                self.iniciar_barrido(1)                      #Llamo a la función para inicial el barrido
                self.comunicacion_sdr.alarma=False          #Pongo la alarma a False una vez hechos los cambios necesarios
                self.aviso_perdida=False

    def comprobar_camaras_fijas(self):
        """

        """
        if self.intersection_handler.detections==1 and self.ptz_detector.detection==False and self.ptz_barrido.estado==False and self.primer_aviso and not self.barrido_una_fija:
            self.iniciar_barrido(1)
            threading.Thread(target=self.espera_barrido).start()

    def comprobar_estado(self):
        """

        """
        if self.ptz_detector.detection or self.intersection_handler.detection:
            self.estado="Dron localizado"
        elif not self.ptz_detector.detection and not self.intersection_handler.detection and not self.ptz_barrido.estado and not self.ptz_detector.perdida:
            self.estado="Perdida total"
        elif self.ptz_barrido.estado and not self.ptz_detector.detection and not self.intersection_handler.detection and not self.ptz_barrido.barrido_post:
            self.estado="Búsqueda"
        elif  not self.ptz_detector.detection and not self.intersection_handler.detection and self.ptz_barrido.estado and self.ptz_barrido.barrido_post:
            self.estado="Barrido post pérdida"

    def comprobar_intersection_handler(self):
        """

        """
        if self.intersection_handler.move_PTZ!=None and self.ptz_detector.detection==False and self.intersection_handler.aviso_cruce==False:
            if self.ptz_barrido.estado==True:
                self.ptz_barrido.detener_barrido_por_aviso()
            self.intersection_handler.aviso_cruce=True
            self.ptz_detector.buscar_por_aviso_ih(self.intersection_handler.move_PTZ[0],self.intersection_handler.move_PTZ[1])
            control_aviso_thread=threading.Thread(target=self.intersection_handler.control_aviso_cruce)
            control_aviso_thread.start()
            
    def comprobar_aviso(self):
        """

        """
        if self.estado=="Dron localizado" and self.aviso_deteccion==False:
            self.aviso_deteccion=True
            self.aviso_perdida=False
            print("Aviso de detección")
            self.comunicacion_sdr.enviar_respuesta("deteccion") #Aviso de que he detectado
            #Envio vídeo
            enviar_alarma_cra=threading.Thread(target=self.enviar_alarma_cra)
            enviar_alarma_cra.start()

        elif self.estado=="Perdida total" and self.aviso_perdida==False:
            self.aviso_perdida=True
            self.aviso_deteccion=False
            self.comunicacion_sdr.enviar_respuesta("perdida") #Aviso pérdida
            print("Aviso de perdida o finalización de barrido sin detección")


    def comprobar_perdida(self):
        """

        """
        if self.ptz_detector.perdida and not self.intersection_handler.detection:
            print("Mando barrido post pérdida")
            self.ptz_detector.perdida=False
            self.iniciar_barrido(2)
        elif self.ptz_detector.perdida and self.intersection_handler.detection:
            print("Anulo el barrido pos perdida ya que hay deteciones del otro módulo qyue ya enmvía sus propios barridos")
            self.ptz_detector.perdida=False

    def espera_barrido(self):
        """

        """
        self.barrido_una_fija=True
        time.sleep(5)
        self.barrido_una_fija=False

    def enviar_alarma_cra(self):
        #Se graba el video
        print("Grabando video")
        #Comprobamos de donde viene la detecion para ver con quien grabamos
        if self.ptz_detector.detection:
            self.camera_capture.iniciar_captura(self.camaras[-1].source,6)
        elif self.intersection_handler.detection:
            for camera in self.camaras[:-1]:
                if camera.detection:
                    self.camera_capture.iniciar_captura(camera.source,6)
                break
        #Recibimos la distancia del SDR
        self.comunicacion_sdr.enviar_respuesta("grabado") #Aviso de que he acabado de grabar
        while True:
            distancia = self.comunicacion_sdr.distancia
            if distancia != None:
                break
            time.sleep(0.1)

        #Compruebo si todavía estoy detectando para ver si envío una localización o no       
        if self.estado=="Dron localizado":
            print("El dron sigue localizado en el momento de enviar el mensaje")
            #Comprobar si intersection_handler ha calculado un punto porque durante la grabación una nueva cámara está detectando
            if self.intersection_handler.punto_dron is not None:  
                #Enviamos el video con las coordenadas calculadas por intersection handler
                print("Se envía el video junto con el punto calculado por intersection handler: ", self.intersection_handler.punto_dron)
                #self.comunicador_api......
            
            else:
                if distancia==0:
                    print("Envío solo el video porque el SDR no sabe la distancia actual al dron")
                    #Envio solo el video 
                    pass
                else:
                    origen_SDR=(self.sdr.position)
                    #Comprobar desde que camara se ha detecxtado
                    if self.ptz_detector.detection:
                        punto_medio_final, _, _ = cd.intersectar_recta_esfera(origen_SDR, distancia, self.camaras[-1].position, self.camaras[-1].orientation[0],self.camaras[-1].orientation[1])
                        #Enviamos el video con las coordenadas calculadas por el cruce de informaciones de la cámara y el SDR
                        print("Se envía el video junto con el punto calculado por el cruce de informaciones: ", punto_medio_final)
                        #self.comunicador_api......
                    elif self.intersection_handler.detection:
                        for camera in self.camaras[:-1]:
                            if camera.detection:
                                punto_medio_final, _, _ = cd.intersectar_recta_esfera(origen_SDR, distancia, camera[-1].position, camera.orientation[0], camera.orientation[1])
                                #Enviamos el video con las coordenadas calculadas por el cruce de informaciones de la cámara y el SDR
                                print("Se envía el video junto con el punto calculado por el cruce de informaciones ", punto_medio_final)
                            #self.comunicador_api......
                            
        else:
            print("Se envía solo el video porque actualmente no se está en visión con él")
            #Se envía solo el vídeo grabado pero con mensaje de que actualmente no está en visión
            #self.comunicador_api......
            pass

        self.comunicacion_sdr.distancia=None


