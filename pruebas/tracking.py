from ptz_track2 import PTZDetector
from ptz_control import ptzControl
from camera_config import CameraConfig
from intersection_handler import IntersectionHandler
import time

# Especifica el modelo que se va a usar para yolov8
model_path="models/yolov8n.engine" 
size=640

camera= 0

#Cargamos la información de las cámaras y el SDR a través del módulo CameraConfig
camera_config = CameraConfig("cameras.csv")
camaras = camera_config.get_cameras()
sdr = camera_config.get_sdr()

#Creamos un objeto de IntersectionHandler para el manejo de las intersecciónes de las cámaras fijas
intersection_handler = IntersectionHandler(camaras)

#Creamos unobjeto de PTZDetector para el manejo de la lógica de la cámara PTZ
ptz_detector=PTZDetector(intersection_handler.cola_desviaciones, camaras[-1],camera, "video.mp4" , model_path, size)

ptz_detector.detect_and_track()