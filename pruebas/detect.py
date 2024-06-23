from ultralytics import YOLO    
from camera_config import CameraConfig
import queue
from camera_detector import CameraDetector


model_path="yolov8n.pt"
camera_config=CameraConfig("cameras.csv")
camaras = camera_config.get_cameras()
data_queue = queue.Queue()
detector=CameraDetector(camaras[2], data_queue, model_path, 640)
detector.detect()
