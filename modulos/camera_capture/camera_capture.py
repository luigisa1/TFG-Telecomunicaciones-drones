import cv2
import time
import threading
import os
import shutil

class CameraCapture:
    def __init__(self):
        self.directorio_imagenes = 'imagenes_barrido'
        self.directorio_video = 'video_detect'
        
        # Verifica y crea el directorio para las imágenes si no existe, o limpia si existe
        self.limpiar_directorio(self.directorio_imagenes)
        
        # Verifica y crea el directorio para los videos si no existe, o limpia si existe
        self.limpiar_directorio(self.directorio_video)
    
    def limpiar_directorio(self, directorio):
        if os.path.exists(directorio):
            # Elimina todo el contenido del directorio
            for filename in os.listdir(directorio):
                file_path = os.path.join(directorio, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
        else:
            # Crea el directorio si no existe
            os.makedirs(directorio)
    
    def iniciar_captura(self,url_de_la_camara, duracion):
        iniciar_captura_threading=threading.Thread(target=self.capturar_video, args=(url_de_la_camara,duracion))
        iniciar_captura_threading.start()
        iniciar_captura_threading.join()

    def capturar_video(self, url_de_la_camara, duracion=10):
        # Inicializa la captura de video de la cámara IP
        archivo_salida = os.path.join(self.directorio_video, 'output.mp4')
        cap = cv2.VideoCapture(url_de_la_camara)

        # Define el tamaño en píxeles (176x144) y FPS (8.0) para el video de salida
        frame_width = 176
        frame_height = 144
        fps = 8.0

        # Define el codec y crea un objeto VideoWriter para guardar el video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(archivo_salida, fourcc, fps, (frame_width, frame_height))

        # Tiempo de inicio
        start_time = time.time()
        frame_duration = 1 / fps  # Duración de cada frame en segundos

        while True:
            ret, frame = cap.read()
            if ret:
                # Redimensiona el frame al tamaño deseado
                frame = cv2.resize(frame, (frame_width, frame_height))
                # Escribe el frame en el archivo de salida
                out.write(frame)

                # Muestra el frame en una ventana (si es necesario)
                cv2.imshow('Grabando', frame)

                # Detiene la captura después de 'duracion' segundos
                if time.time() - start_time > duracion:
                    break
                
                # Espera el tiempo necesario para el próximo frame
                time.sleep(frame_duration)
            else:
                break

        # Libera el objeto de captura y el escritor de video
        cap.release()
        out.release()
        # Cierra solo la ventana específica de grabación
        cv2.destroyWindow('Grabando')
    
    # def capturar_video(self, url_de_la_camara, duracion=10):
    #     # Inicializa la captura de video de la cámara IP
    #     archivo_salida = os.path.join(self.directorio_video, 'output.mp4')
    #     cap = cv2.VideoCapture(url_de_la_camara)

    #     # Define el tamaño en píxeles (176x144) y FPS (8.0) para el video de salida
    #     frame_width = 176
    #     frame_height = 144
    #     fps = 8.0

    #     # Define el codec y crea un objeto VideoWriter para guardar el video
    #     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    #     out = cv2.VideoWriter(archivo_salida, fourcc, fps, (frame_width, frame_height))

    #     # Tiempo de inicio
    #     start_time = time.time()

    #     while True:
    #         ret, frame = cap.read()
    #         if ret:
    #             # Redimensiona el frame al tamaño deseado
    #             frame = cv2.resize(frame, (frame_width, frame_height))
    #             # Escribe el frame en el archivo de salida
    #             out.write(frame)

    #             # Detiene la captura después de 'duracion' segundos
    #             if time.time() - start_time > duracion:
    #                 break
    #         else:
    #             break

    #     # Libera el objeto de captura y cierra todas las ventanas
    #     cap.release()
    #     out.release()

    def iniciar_captura_imagenes(self, url_de_la_camara, numero_camara, duracion):
        captura_imagenes_threading = threading.Thread(target=self.guardar_imagenes, args=(url_de_la_camara, numero_camara, duracion))
        captura_imagenes_threading.start()
    
    def guardar_imagenes(self, url_de_la_camara, numero_camara, duracion):
        cap = cv2.VideoCapture(url_de_la_camara)
        print("Capturando imágenes...")

        start_time = time.time()
        actual_time= time.time()
        count = 0

        while True:
            ret, frame = cap.read()
            if ret:
                # Construye la ruta del archivo para guardar la imagen
                t=time.time()
                if (t-actual_time)>1:
                    actual_time=t
                    nombre_archivo = os.path.join(self.directorio_imagenes, f'{numero_camara}_frame_{count}.jpg')
                    # Guarda el frame como imagen
                    cv2.imwrite(nombre_archivo, frame)
                    count += 1
                # Detiene la captura después de 'duracion' segundos
                if time.time() - start_time > duracion:
                    break
            else:
                break

        # Libera el objeto de captura y cierra todos los recursos
        cap.release()
