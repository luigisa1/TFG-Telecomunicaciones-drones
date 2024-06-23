import csv

class Camera:
    def __init__(self, name, position, field_of_view, image_size, orientation, source):
        self.name = name
        self.position = position
        self.field_of_view = field_of_view
        self.image_size = image_size
        self.orientation = orientation
        self.source = source
        self.detection=False
        self.activado=True

    def __str__(self):
        return f"Camera(name={self.name}, pos={self.position}, fov={self.field_of_view}, size={self.image_size}, orient={self.orientation}, source={self.source})"
    
class SDR:
    def __init__(self, name, position):
        self.name = name
        self.position = position

    def __str__(self):
        return f"SDR(name={self.name}, position={self.position})"

class CameraConfig:
    def __init__(self, filename):
        self.cameras = []
        self.filename = filename
        self.load_cameras()

    def add_camera_from_data(self, data):
        name, position, fov, img_size, orientation, source = data
        new_camera = Camera(name, position, fov, img_size, orientation, source)
        self.cameras.append(new_camera)
        

    def load_cameras(self):
        with open(self.filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Salta el encabezado
            rows = list(reader)
            sdr_data = rows.pop()  # Extraer la última fila para el SDR
            # Cargar todas las cámaras excepto la última
            for row in rows:
                data = (
                    row[0],  # name
                    (float(row[1]), float(row[2]), float(row[3])),  # position
                    (float(row[4]), float(row[5])),  # field_of_view
                    (int(row[6]), int(row[7])),  # image_size
                    (float(row[8]), float(row[9])),  # orientation
                    row[10]  # source
                )
                self.add_camera_from_data(data)
             # Configurar el SDR con la última fila
            self.sdr = SDR(sdr_data[0], (float(sdr_data[1]), float(sdr_data[2]), float(sdr_data[3])))

    def get_cameras(self):
        return self.cameras
    
    def get_sdr(self):
        return self.sdr

