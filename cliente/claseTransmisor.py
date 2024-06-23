import threading
import time
import os
import OpenSSL as SSL
import socket

class ErrorDeHandshake(Exception):
    """Excepción personalizada para errores de handshake."""
    pass

class TransmisorSIA:
    def __init__(self,  
                 serverAddress, serverPort,
                 numeroCliente=0x0000, prefijoCliente=0x000, numeroReceptor=0x00,
                 mensajeMantenimiento = True, cifradoMensaje = False):
        #Así se crea un objeto donde lo único obligatorio es la dirección del servidor, que es lo único crítico 

        # Atributos de la clase, son los datos del cliente
        self.numeroCliente = numeroCliente
        self.prefijoCliente = prefijoCliente
        self.numeroReceptor = numeroReceptor

        # Atributos de la clase, son los datos del servidor
        self.serverAddress = serverAddress
        self.serverPort = serverPort 

        # Atributos de la clase, características de la comunicación
        self.mensajeMantenimiento = mensajeMantenimiento
        self.cifradoMensaje = cifradoMensaje

        self.xdata = None  # Esto es el campo Xdata del mensaje SIA
        self.videoPath = None

        self.x = None
        self.y = None
        self.z = None

        # Inicia el monitoreo de mantenimiento al crear una instancia
        self.__start_maintenance_monitor()


    # Métodos que monitorean el mantenimiento. 
    def __monitor_mantenimiento(self):
        while True:
            time.sleep(20) #El primer NULL se envía a los 20 segundos
            if self.mensajeMantenimiento == 1 and self.alarmaEnviada == False:
                self.enviarNull()

            self.alarmaEnviada = False

    def __start_maintenance_monitor(self):
        threading.Thread(target=self.__monitor_mantenimiento,daemon=True).start()


    #setters
    def setCifrado(self, cifradoMensaje):
        self.cifradoMensaje = cifradoMensaje

    def setMantenimiento(self, mensajeMantenimiento):
        self.mensajeMantenimiento = mensajeMantenimiento

    def setServer(self, serverAddress, serverPort):
        self.serverAddress = serverAddress
        self.serverPort = serverPort
    
    def setCliente(self, numeroCliente, prefijoCliente, numeroReceptor):
        self.numeroCliente = numeroCliente
        self.prefijoCliente = prefijoCliente
        self.numeroReceptor = numeroReceptor

    def setXdataCoordenadas(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

        if self.xdata:
            self.xdata += f"X{x}Y{y}Z{z}"
        else:
            self.xdata = f"X{x}Y{y}Z{z}"

    def setXdataVideo(self, fps, width, height):
        self.xdata = f"Vf{fps}w{width}h{height}"

    #getters
    def getCifrado(self):
        return self.cifradoMensaje
    
    def getMantenimiento(self):
        return self.mensajeMantenimiento
    
    def getServer(self):
        return self.serverAddress, self.serverPort
    
    def getCliente(self):
        return self.numeroCliente, self.prefijoCliente, self.numeroReceptor
    

    #aquí se envía el mensaje de alarma
    def enviarAlarma(self, video_path=None, x=None, y=None, z=None):

        # Se definen las variables propias de la alarma--------------------------------
        # Protocolo del mensaje
        protocolo_flag = "ADM-CID"  # Esto es el ID del protocolo Contact ID

        if self.cifradoMensaje == True:
            cifrado_flag = "*"
        else:
            cifrado_flag = ""

        # Se inicializa el Sequence Number en 0 o se saca del archivo sequence_number.txt para que cada mensaje esté numerado correctamente
        self.secNum = self.__iniciarSecuencia()

        # Se define el mensaje de evento a enviar al servidor, contactID y luego SIA
        # Contact ID
        acct = self.numeroCliente  # Esto es el número de cuenta del cliente
        mt = 0x18  # Esto es el tipo de mensaje, que identifica contactID, también se puede usar 98
        q = 0x1  # Esto es el calificador de evento, en este tipo nuevo evento
        xyz = 0x131  # Esto es el código de evento,Perimeter Burglary
        gg = 0x0B  # Esto es el grupo de la alarma, en este caso sin grupo específico
        ccc = 0x000  # Esto es el número de zona, en este caso sin zona específica

        self.mensajeContactID = self.__generar_mensaje_CID(
            acct, mt, q, xyz, gg, ccc)  # Se genera el mensaje Contact ID


        self.timestamp = time.time()  # Obtener la fecha y hora actual en epoch
        
        if x and y and z:
            self.setXdataCoordenadas(x, y, z)

        if video_path:
            self.videoPath = video_path
        
        self.__enviarMensaje(cifrado_flag, protocolo_flag, self.secNum, self.mensajeContactID, self.xdata, self.timestamp)
        self.alarmaEnviada = True
        
        # Se actualiza el Sequence Number en el archivo sequence_number.txt
        self.__actualizarSecuencia(self.secNum)

        if self.videoPath:
            self._enviarVideo(self.videoPath)  # Se envía el video de la alarma


        #Volvemos a poner a None todos los xdata ya que son intrínsecos a cada mensaje
        self.xdata = None
        self.videoPath = None
        self.x = None
        self.y = None
        self.z = None
        




    #aquí se envía el mensaje de mantenimiento NULL
    def enviarNull(self):

        #Revisar si esto va bien aquí 
        protocolo_flag = "NULL"  # Esto es el ID del protocolo Contact ID
        cifrado_flag = ""  # Esto es el flag de cifrado, en este caso no está cifrado
        self.secNum = 0  # Esto es el número de secuencia del mensaje
        self.mensajeContactID = ""
        self.xdata = ""
        self.timestamp = time.time()  # Obtener la fecha y hora actual en epoch

        self.__enviarMensaje(cifrado_flag, protocolo_flag, self.secNum, self.mensajeContactID, self.xdata, self.timestamp)
        


    def _enviarVideo(self, video_path):
        import zlib
        import cv2
        print("Enviando video...")
        
        BUFF_SIZE = 1024
        self.clientSock.set_ciphertext_mtu(BUFF_SIZE)

        vid = cv2.VideoCapture(video_path)
        fps, width, height = self.__get_video_metadata(video_path)


        protocolo_flag = "ADM-CID"  # Esto es el ID del protocolo Contact ID

        if self.cifradoMensaje == True:
            cifrado_flag = "*"
        else:
            cifrado_flag = ""

        # Se inicializa el Sequence Number en 0 o se saca del archivo sequence_number.txt para que cada mensaje esté numerado correctamente
        self.secNum = self.__iniciarSecuencia()

        # Se define el mensaje de evento a enviar al servidor, contactID y luego SIA
        # Contact ID
        acct = self.numeroCliente  # Esto es el número de cuenta del cliente
        mt = 0x18  # Esto es el tipo de mensaje, que identifica contactID, también se puede usar 98
        q = 0x1  # Esto es el calificador de evento, en este tipo nuevo evento
        xyz = 0x131  # Esto es el código de evento,Perimeter Burglary
        gg = 0x0B  # Esto es el grupo de la alarma, en este caso sin grupo específico
        ccc = 0x000  # Esto es el número de zona, en este caso sin zona específica

        self.mensajeContactID = self.__generar_mensaje_CID(acct, mt, q, xyz, gg, ccc)  # Se genera el mensaje Contact ID

        self.timestamp = time.time()  # Obtener la fecha y hora actual en epoch

        self.setXdataVideo(fps, width, height)

        self.__enviarMensaje(cifrado_flag, protocolo_flag, self.secNum, self.mensajeContactID, self.xdata, self.timestamp)

        time.sleep(0.01)

        while vid.isOpened():
            _, frame = vid.read()
            if frame is None:
                print("Leidos todos los frames.")
                break

            encoded, buffer = cv2.imencode(
                '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if not encoded:
                print("Error al codificar el frame.")
                continue

            #message = base64.b64encode(buffer) # Se codifica el frame en base64
            message =zlib.compress(buffer) # Se codifica el frame comprimido, esto evita la corrupción de algunos frames que sí pasa en base64 no sé xq 
            #print("Enviando frame de tamaño:", len(message))

            # Se envía el frame en fragmentos de BUFF_SIZE bytes
            for i in range(0, len(message), BUFF_SIZE):
                fragment = message[i:i+BUFF_SIZE]
                self.clientSock.send(fragment)  
                #print(f"Enviado fragmento de tamaño {len(fragment)} bytes")
                
            
            self.clientSock.send(b'END')  # Se envía la señal de fin de frame
            #time.sleep(0.1) #Para que no se pierda el mensaje de fin de video

        recibido = False
        while not recibido:

            self.clientSock.send(b'END')  # Se envía la señal de fin de video
            thread = threading.Thread(target=self.__esperaRespuesta)
            thread.start()
            thread.join(3)

            if not thread.is_alive():
                recibido = True
                break

       

        vid.release()
        # cv2.destroyAllWindows()

        self.__actualizarSecuencia(self.secNum)
        self.xdata = None
        self.videoPath = None

    def enviarInicioSistema(self):
            
        try:
            # Protocolo del mensaje
            protocolo_flag = "ADM-CID"  # Esto es el ID del protocolo Contact ID

            if self.cifradoMensaje == True:
                cifrado_flag = "*"
            else:
                cifrado_flag = ""

            # Se inicializa el Sequence Number en 0 o se saca del archivo sequence_number.txt para que cada mensaje esté numerado correctamente
            self.secNum = self.__iniciarSecuencia()

            # Se define el mensaje de evento a enviar al servidor, contactID y luego SIA
            # Contact ID
            acct = self.numeroCliente  # Esto es el número de cuenta del cliente
            mt = 0x18  # Esto es el tipo de mensaje, que identifica contactID, también se puede usar 98
            q = 0x1  # Esto es el calificador de evento, en este tipo nuevo evento
            xyz = 0x133  # Esto es el código de evento,Safe
            gg = 0x0B  # Esto es el grupo de la alarma, en este caso sin grupo específico
            ccc = 0x000  # Esto es el número de zona, en este caso sin zona específica

            self.xdata = ""

            self.mensajeContactID = self.__generar_mensaje_CID(
                acct, mt, q, xyz, gg, ccc)  # Se genera el mensaje Contact ID

            self.timestamp = time.time()  # Obtener la fecha y hora actual en epoch

            self.__enviarMensaje(cifrado_flag, protocolo_flag, self.secNum, self.mensajeContactID, self.xdata, self.timestamp)

            # Se actualiza el Sequence Number en el archivo sequence_number.txt
            self.__actualizarSecuencia(self.secNum)

            return True
        
        except Exception as e:
            print(f"Error al enviar el mensaje de inicio del sistema: {e}")
            return False


    def enviarCaidaSistema(self):
        # Protocolo del mensaje
        protocolo_flag = "ADM-CID"  # Esto es el ID del protocolo Contact ID

        if self.cifradoMensaje == True:
            cifrado_flag = "*"
        else:
            cifrado_flag = ""

        # Se inicializa el Sequence Number en 0 o se saca del archivo sequence_number.txt para que cada mensaje esté numerado correctamente
        self.secNum = self.__iniciarSecuencia()

        # Se define el mensaje de evento a enviar al servidor, contactID y luego SIA
        # Contact ID
        acct = self.numeroCliente  # Esto es el número de cuenta del cliente
        mt = 0x18  # Esto es el tipo de mensaje, que identifica contactID, también se puede usar 98
        q = 0x1  # Esto es el calificador de evento, en este tipo nuevo evento
        xyz = 0x300  # Esto es el código de evento, System Trouble
        gg = 0x0B  # Esto es el grupo de la alarma, en este caso sin grupo específico
        ccc = 0x000  # Esto es el número de zona, en este caso sin zona específica

        self.xdata = ""

        self.mensajeContactID = self.__generar_mensaje_CID(
            acct, mt, q, xyz, gg, ccc)  # Se genera el mensaje Contact ID

        self.timestamp = time.time()  # Obtener la fecha y hora actual en epoch

        self.__enviarMensaje(cifrado_flag, protocolo_flag, self.secNum, self.mensajeContactID, self.xdata, self.timestamp)

        # Se actualiza el Sequence Number en el archivo sequence_number.txt
        self.__actualizarSecuencia(self.secNum)

#---------------------------------------------------------------

    #Zona de funciones privadas a las que el usuario del objeto no debería tener acceso :)


    
    #Función privada para enviar mensajes en el protocolo SIA
    def __enviarMensaje(self, cifrado_flag, protocolo, secNum, mensajeContactID, xdata, timestamp):
        import datetime
        import sys

        self.clientSock = self.__socketSSL_UDP()

        mensajeSIA = self.__generar_mensaje_sia(
            cifrado_flag, protocolo, secNum, self.numeroReceptor, self.prefijoCliente, self.numeroCliente, mensajeContactID, xdata, timestamp)
        
        
        timeout = 5
        intentos = 0
        # La siguiente parte del mensaje se define para poder repetirlo según la respuesta del servidor
        while intentos < 3:  # Se intenta enviar el mensaje 3 veces

 
        # Se envía el mensaje al servidor usando el socket seguro UDP
            self.clientSock.send(mensajeSIA.encode('ascii'))
            print("Mensaje enviado:", mensajeSIA)

            try:
                print("Mensaje enviado, intento número", intentos + 1)
                # print("Mensaje enviado:", mensajeSIA)

                #Esta es la única manera que se de hacer un timeout en un socket SSL, odio OpenSSL
                thread = threading.Thread(target=self.__esperaRespuesta)
                thread.start()
                thread.join(timeout)

                if thread.is_alive():  
                    raise Exception("Timeout")

                self.respuesta = self.respuesta.decode('ascii')

                # Se busca la posición del primer caracter de la respuesta
                inicio_respuesta = self.respuesta.find('"') + 1
                # Se busca la posición del último caracter de la respuesta
                fin_respuesta = self.respuesta.find('"', inicio_respuesta)
                # Se extrae la respuesta
                self.respuesta = self.respuesta[inicio_respuesta:fin_respuesta]

                if self.respuesta == "ACK":  # Si la self.self.respuesta es ACK
                    # Se imprime que el mensaje fue recibido correctamente
                    print("El mensaje fue recibido correctamente")
                    intentos = 3

                elif self.respuesta == "NACK":
                    # Se imprime que el mensaje no fue recibido correctamente
                    intentos += 1
                    print("El mensaje no fue recibido correctamente")
                    timestamp = time.time()  # Obtener la fecha y hora actual en epoch
                    # Se genera el mensaje SIA aquí porque solo se actualiza el timestamp en casos de fallo para actualizar el timestamp
                    mensajeSIA = self.__generar_mensaje_sia(
                        cifrado_flag, protocolo, secNum, self.numeroReceptor, self.prefijoCliente, self.numeroCliente, mensajeContactID, xdata, timestamp)

                    if intentos == 3:
                        print("Se han agotado los intentos, se declara fallo")
                        
                        break

                elif self.respuesta == "DUH":
                    print(
                        "Error de procesado o entendimiento del mensaje por parte del servidor, se declara fallo")
                    
                    break

                else:
                    print("Respuesta no reconocida, se declara fallo")
                    
                    break

            except Exception:  # Si se produce un timeout
                print("Timeout")
                intentos += 1
                if intentos == 3:
                    print("Se han agotado los intentos, se declara fallo")

                continue

        
        
    #Función privada para generar el mensaje SIA
    def __generar_mensaje_sia(self, cifrado_flag, protocolo, secNum, Rrcvr, Lpref, acct, mensajeContactID, xdata, timestamp):
        from Crypto.Cipher import AES
        
        # Same key as used for encryption
        key = b'm_\x1a\x92\x91\xf3%a\x90\x89\x83\x9d\xc6\xb5D\xc9'
        # Same IV as used for encryption
        iv = b'~U\xe3\xd1Hsz\xa8\x05\xe1\x14\x8c\xb8X\xea\xbc'
        
        # Se define el mensaje de alarma a enviar al servidor según SIA
        mensajeSIA_previo = f'"{cifrado_flag}{protocolo}"{secNum:04d}R{Rrcvr:x}L{Lpref:x}#{acct:x}'.upper()

        # Caso no cifrado
        if cifrado_flag == "":
            # Se añade mensajeContactID si está presente
            if mensajeContactID:
                mensajeSIA_previo += f"[#{acct:x}|{mensajeContactID}]".upper()
            else:
                mensajeSIA_previo += f"[]"

            # Se añade xdata si está presente
            if xdata:
                mensajeSIA_previo += f"[{xdata.upper()}]"
            

            # Se añade el timestamp
            mensajeSIA_previo += f"_{timestamp}"

        # Caso cifrado
        elif cifrado_flag == "*":  # Caso cifrado
            mensajeSIA_previo += f"["

            # El padding se añade al final
            mensajeSIA_padding = ""
            # Se cierra el pad
            mensajeSIA_padding += f"|"

            # Se añade mensajeContactID si está presente
            if mensajeContactID:
                mensajeSIA_padding += f"#{acct:04x}|{mensajeContactID.upper()}"

            mensajeSIA_padding += f"]"

            # Se añade xdata si está presente
            if xdata:
                mensajeSIA_padding += f"[{xdata.upper()}]"

            # Se añade el timestamp
            mensajeSIA_padding += f"_{timestamp.upper()}"

            # Se añade el padding al mensaje
            longitud_padding = (16 - (len(mensajeSIA_padding) % 16)) % 16
            padding = self.__generar_padding(longitud_padding)
            mensajeSIA_cifrar = f"{padding}{mensajeSIA_padding}"
            mensajeSIA_cifrar = mensajeSIA_cifrar.upper()

            # Se añade el cifrado
            # AES
            # Aún hay que manejar el iv y la clave
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encriptado = cipher.encrypt(mensajeSIA_cifrar.encode('ascii'))
            encriptado_ASCII = encriptado.hex().upper()
            # print("Mensaje cifrado:", repr(encriptado_ASCII))
            # print("Mensaje cifrado length:", len(encriptado_ASCII))

            mensajeSIA_previo += f"{encriptado_ASCII}"

        # Se calcula el CRC y la longitud del mensaje
        crc_calculado = self.__calcular_crc(mensajeSIA_previo)
        longitud_calculada = len(mensajeSIA_previo)
        # Esto es el código de longitud del mensaje (3 caracteres ASCII)
        longitud_calculada = str(longitud_calculada).zfill(3)[-3:]

        # Se estructura el mensaje SIA completo
        mensajeSIA = f'\n{crc_calculado}0{longitud_calculada}{mensajeSIA_previo}\r'.upper()

        return mensajeSIA
    


    #Función privada para generar el padding

    def __generar_padding(self, longitud_padding):
        import random

        if longitud_padding == 0:
            longitud_padding = 16

        while True:
            padding = ""
            # Rango de ascii
            lower_bound = 32  # Space character
            upper_bound = 126  # Tilde '~'
            for _ in range(longitud_padding):
                char = chr(random.randint(lower_bound, upper_bound))
                padding += char
            if all(c not in "|[]" for c in padding):
                break

        return padding

    #Función privada para calcular el CRC
    def __calcular_crc(self, mensaje):
        # print("El mensaje que le entra al crc es: ", repr(mensaje))
        # Se convierte el mensaje a bytes
        mensaje_bytes = mensaje.encode('ascii')
        #print("El mensaje que le entra al crc es: ", repr(mensaje_bytes))

        # Se inicializa el CRC
        crc = 0

        # Se calcula el CRC
        for byte in mensaje_bytes:
            crc = crc ^ byte
            for i in range(8):
                if crc & 1:
                    # 0x8408 es el polinomio del CRC-16 = 1000 0100 0000 1000
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc = crc >> 1

        # Se convierte el CRC a 4 caracteres ASCII
        crc = crc.to_bytes(2, byteorder='big').hex().upper()

        return crc

    def __generar_mensaje_CID(self, acct, mt, q, xyz, gg, ccc):
            # Se define el mensaje Contact ID
        mensajeContactID_previo = f"{acct:04x} {mt:02x} {q:01x}{xyz:03x} {gg:02x} {ccc:03x}"
        s = self.__calcular_checksum(mensajeContactID_previo)  # Esto es el checksum

        # Esto es el mensaje Contact ID completo
        mensajeContactID = f"{mensajeContactID_previo} {s:01x}"
        return mensajeContactID


    #Función privada para calcular el Checksum
    # Cálculo del Checksum
    def __calcular_checksum(self,mensaje):
        # Se inicializa el checksum
        checksum = 0

        # Se calcula el checksum
        for byte in mensaje.encode('ascii'):
            if byte == 48:  # ASCII '0'
                checksum += 10
            elif byte == 32:  # ASCII ' '
                continue
            else:
                checksum += int(chr(byte), 16)

        checksum = checksum % 15

        return checksum

    #Función privada para iniciar la secuencia
    def __iniciarSecuencia(self):
        import os
        # Manejo de un fichero para que el seq number se mantenga en el tiempo -----------
        # Nombre del archivo donde se almacenará el Sequence Number
        archivo = "sequence_number.txt"

        # Comprobar si el archivo existe
        if os.path.exists(archivo):
            # Leer el Sequence Number del archivo
            with open(archivo, "r") as f:
                sequence_number = int(f.read())
        else:
            # Inicializar el Sequence Number
            sequence_number = 0

        return sequence_number


    def __actualizarSecuencia(self,sequence_number):
        
        archivo = "sequence_number.txt"
        sequence_number += 1

    # Reiniciar el Sequence Number si alcanza 9999[^1^][1]
        if sequence_number > 9999:
            sequence_number = 0

    # Escribir el Sequence Number en el archivo
        with open(archivo, "w") as f:
            f.write(str(sequence_number))


    def __get_video_metadata(self,video_path):
        import cv2 

        # Abrir el video
        cap = cv2.VideoCapture(video_path)

        # Obtener los metadatos del video
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Cerrar el video
        cap.release()

        return fps, width, height


    def __esperaRespuesta(self):
        self.respuesta = self.clientSock.recv(1024)
        pass


    def __socketSSL_UDP(self):
        import socket
        from OpenSSL import SSL
        

        # 1. Crear Contexto DTLS
        contexto = SSL.Context(SSL.DTLS_CLIENT_METHOD)
        contexto.load_verify_locations('certificados/Server/server.crt')
        contexto.use_certificate_file('certificados/Client/client.crt')
        contexto.use_privatekey_file('certificados/Client/client.key')
        contexto.set_verify(SSL.VERIFY_PEER, callback=None)

        intentos = 0
        timeout = 5
        while intentos < 3:  # Limita los intentos de handshake a 3
            try:
                clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                clientSock_seguro = SSL.Connection(contexto, clientSock)
                clientSock_seguro.set_connect_state()

                clientSock.connect((self.serverAddress, self.serverPort))
                clientSock.sendto(b'Hello', (self.serverAddress, self.serverPort))
                print("Mensaje inicial enviado, esperando handshake...")

                # Realizar handshake con timeout
                handshake_successful, error = self.__esperaHandshakeConTimeout(clientSock_seguro, timeout)
                if not handshake_successful:
                    if error:
                        raise error
                    else:
                        print("Timeout de Handshake")
                        raise SSL.Error("Timeout de Handshake")

                print("Handshake completado con éxito.")
                return clientSock_seguro

            except SSL.Error as e:
                print(f"Handshake fallido: {e}")
                time.sleep(timeout)
                intentos += 1

                if intentos >= 3:
                    clientSock.close()
                    raise ErrorDeHandshake("No se pudo completar el handshake después de varios intentos.")
                continue

            except Exception as e:
                print(f"Excepción durante el handshake: {e}")
                clientSock.close()
                raise

        # Si se alcanzan los 3 intentos sin éxito
        raise ErrorDeHandshake("No se pudo completar el handshake después de varios intentos.")

    def __esperaHandshakeConTimeout(self, clientSock_seguro, timeout):
        import socket
        from OpenSSL import SSL
        error = None
        def handshake():
            nonlocal error
            try:
                clientSock_seguro.do_handshake()
            except SSL.Error as e:
                error = e

        thread = threading.Thread(target=handshake)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            return False, None

        return error is None, error

    