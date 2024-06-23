from camera_config import CameraConfig

#Cargamos la información de las cámaras a través del módulo CameraConfig
camera_config = CameraConfig("cameras.csv")
camaras = camera_config.get_cameras()
for camara in camaras:
    print(camara.__str__())
sdr = camera_config.get_sdr()
print(sdr.__str__())