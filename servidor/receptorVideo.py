import cv2
import numpy as np
import zlib


def recibirVideo(serverSock_seguro, videoPath, datosVideo):
    print("Recibiendo video", datosVideo)
    BUFF_SIZE = 1024
    serverSock_seguro.set_ciphertext_mtu(BUFF_SIZE)
    try:
        fpsIni = datosVideo.find('F')
        fpsFin = datosVideo.find('W')
        fps = float(datosVideo[fpsIni+1:fpsFin])

        widthIni = datosVideo.find('W')
        widthFin = datosVideo.find('H')
        width = int(datosVideo[widthIni+1:widthFin])

        heightIni = datosVideo.find('H')
        height = int(datosVideo[heightIni+1:])


        print(
            f"fps: {fps}, width: {width}, height: {height}")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        # Se crea el archivo de video, será buena idea nombrarlo con el número de cuenta o algo así
        
        
        out = cv2.VideoWriter(videoPath, fourcc, fps, (width, height))

        print("Cliente iniciado, esperando datos...")
        while True:
            data_fragments = []
            while True:
                fragment = serverSock_seguro.recv(BUFF_SIZE)
                #print(f"Fragmento recibido de tamaño: {len(fragment)} bytes")
                if fragment == b'END':
                    #print("Fin del fragmento")
                    break
                data_fragments.append(fragment)

            packet = b''.join(data_fragments)
            #print("Recibido frame de tamaño: ", len(packet))
            # print(packet)

            if packet == b'':
                print("Fin del stream de video")
                serverSock_seguro.send(b'ACK')
                break

            try:
                # data = base64.b64decode(packet)
                data = zlib.decompress(packet)
                npdata = np.frombuffer(data, np.uint8)
                frame = cv2.imdecode(npdata, cv2.IMREAD_COLOR)
                if frame is not None:
                    out.write(frame)
                    #print(f"Writing frame, received packet size: {len(packet)} bytes")
            except Exception as e:
                #print(f"Error decoding data: {e}")
                continue
    
    except Exception as e:
        print(f"Error de recepción de video, no se guardará: {e}")
    finally:
        
        out.release()
        cv2.destroyAllWindows()


def extraer_frame_central(videoPath, imagePath):
    # Cargar el video
    cap = cv2.VideoCapture(videoPath)

    if not cap.isOpened():
        print("Error: No se pudo abrir el video.")
        return

    # Obtener el número total de frames
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calcular el frame central
    central_frame_index = total_frames // 2

    # Posicionar el video en el frame central
    cap.set(cv2.CAP_PROP_POS_FRAMES, central_frame_index)

    # Leer el frame
    ret, frame = cap.read()

    if not ret:
        print("Error: No se pudo leer el frame.")
        return

    # Guardar el frame como imagen
    cv2.imwrite(imagePath, frame)

    # Liberar el objeto cap y cerrar todas las ventanas de OpenCV
    cap.release()
    cv2.destroyAllWindows()
