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

from modulos.camara_PTZ.ptz_barrido import PTZBarrido
from modulos.modulo_core.core_logic_module import CoreLogicModule
from modulos.camara_PTZ.ptz_control import ptzControl
from modulos.comSDR.comSDR import ComunicacionSDR
from modulos.camaras_fijas.camera_config import CameraConfig
from modulos.camara_PTZ.ptz_track_4 import PTZDetector
from modulos.intersection_handler.intersection_handler import IntersectionHandler
import threading
from modulos.camera_capture.camera_capture import CameraCapture
from modulos.interfaz_de_usuario.aplicartionGUI_2 import AplicacionGUI
# from .Proyecto_Alarmas.claseTransmisor import TransmisorSIA
import time
from cliente.claseTransmisor import TransmisorSIA

def main():
    flag_servidor = False
    transmisor = 0
    enviar= False
    iteraciones_barrido_inicial = 2
    iteraciones_barrido_normal = 7

    if flag_servidor:
        transmisor = TransmisorSIA(serverAddress="172.233.107.104", serverPort=19000)
        transmisor.setCliente(0x111A, 0x22B, 0x3A)
        transmisor.setCifrado(0)
        transmisor.setMantenimiento(0)

        while not transmisor.enviarInicioSistema(): #Cambiar a cuando me conecte con pablo
            time.sleep(1)

    # Especifica el modelo que se va a usar para yolov8
    model_path="models/best.engine"
    classes=0
    size=640

    #Creamos un objeto de ptzControl para el control de la cámara PTZ, la movemos a la dirección origen y establecemos esta dirección como el preset
    camera = ptzControl()
    camera.move_abspantilt(0, 0, 1, 0)
    time.sleep(3)
    camera.set_preset("origen")
  
    #Creamos un objeto de PTZBarrido para el control de los barridos
    ptz_barrido=PTZBarrido(camera, iteraciones_barrido_inicial, iteraciones_barrido_normal)

    #Creamos un objeto de ComunicacionSDR para la conexión con el módulo SDR vía sockets
    comunicacion_sdr = ComunicacionSDR('192.168.110.4', 8080, modo='servidor')

    #Cargamos la información de las cámaras y el SDR a través del módulo CameraConfig
    camera_config = CameraConfig("configuracion/cameras.csv")
    camaras = camera_config.get_cameras()
    sdr = camera_config.get_sdr()

    #Creamos un objeto de IntersectionHandler para el manejo de las intersecciónes de las cámaras fijas
    intersection_handler = IntersectionHandler(camaras)

    #Creamos nun onjeto de CameraCapture para el manejo de las grabaciones
    camera_capture=CameraCapture()

    #Creamos unobjeto de PTZDetector para el manejo de la lógica de la cámara PTZ
    ptz_detector=PTZDetector(intersection_handler.cola_desviaciones, camaras[-1],camera, camaras[-1].source , model_path, size, classes)

    #Creamos un objeto de CoreLogicModule para el manejo de la lógica central
    core_logic_module= CoreLogicModule(comunicacion_sdr, ptz_barrido, camaras, ptz_detector, intersection_handler, camera_capture, model_path, size, classes, sdr, transmisor, flag_servidor, enviar)

    # Iniciamos el funcionamiento de los módulos a través de un método del CoreLogicModule para que empiece a funcionar el programa
    iniciar_modulos_thread=threading.Thread(target=core_logic_module.iniciar_modulos)
    iniciar_modulos_thread.start()

    #Creamos e iniciamos la interfaz gráfica de ususario a través de un objeto del módulo AplicationGUI
    gui = AplicacionGUI(intersection_handler, camaras, ptz_detector, ptz_barrido, core_logic_module)
    gui.run()

if __name__ == "__main__":
    main()