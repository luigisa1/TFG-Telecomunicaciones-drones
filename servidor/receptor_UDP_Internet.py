#Este código no hace nada especial, solo es un receptor TCP de prueba. 

import socket
import time
from OpenSSL import SSL
import threading

from receptorVideo import recibirVideo, extraer_frame_central
from funcionesReceptor import extraer_datos, calcular_crc, validar_fecha, esperaHandshake
from base_datos import iniciarBD, guardarAlarma

# Same key as used for encryption
key = b'm_\x1a\x92\x91\xf3%a\x90\x89\x83\x9d\xc6\xb5D\xc9'
# Same IV as used for encryption
iv = b'~U\xe3\xd1Hsz\xa8\x05\xe1\x14\x8c\xb8X\xea\xbc'


serverAddress = "192.168.0.24"  # Definimos nuestra dirección como servidor
# serverAddress='127.0.0.1'
serverPort = 19000  # Definimos nuestro puerto como servidor

#iNICIAR BBDD 
iniciarBD()

print("el Servidor está listo")


test = 0
fechaVideo = None
xguardar, yguardar, zguardar = None, None, None

while True:
    try:
        intentos = 0
        while intentos < 3:
        
            context = SSL.Context(SSL.DTLS_SERVER_METHOD)
            context.use_certificate_file('certificados/Server/server.crt')
            context.use_privatekey_file('certificados/Server/server.key')

            # Cargamos el certificado de la CA
            context.load_verify_locations('certificados/CA/ca.crt')
            context.set_verify(
                SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, callback=None)

            

            serverSock = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM)  # Creamos un socket UDP

            serverSock.bind((serverAddress, serverPort))
            # Esperar a recibir un mensaje inicial de cualquier cliente
            data = cliente = None
            while data != b'Hello':

                data, cliente = serverSock.recvfrom(1024)

            try:
                print(f'Datos recibidos de {cliente}: {data}')
            except Exception as e:
                print(f'Error al decodificar datos, saliendo: {e}')
                break
                

            # Envolver el socket en la capa SSL
            serverSock_seguro = SSL.Connection(context, serverSock)
            serverSock_seguro.set_accept_state()

            # Importante: establecer la dirección del cliente
            serverSock.connect(cliente)

            timeout = 5
            # Realizar el handshake SSL/TLS
            thread = threading.Thread(target=esperaHandshake, args=(serverSock_seguro,))
            thread.start()
            thread.join(timeout)

            print('Handshake completado con:', cliente)

            
                
            try:
                receivedMessage = serverSock_seguro.recv(1024)
            except Exception as e:
                print(f'Error en el primer mensaje cifrado, cerrando esta conexión y reiniciando: {e}')
                serverSock_seguro.close()
            mensaje = receivedMessage.decode('ascii') #Imprimimos lo que recibimos

            print(f"Mensaje recibido")

            

            base_mensaje, crc_recibido, longitud_recibida, protocolo, num_secuencia, receptor, prefijoCuenta, numCuenta_1, numCuenta_2, mensaje_CID, extendedData, fecha, cifrado_flag, x, y, z, datosVideo = extraer_datos(mensaje)
            
            #Una vez estraidos los datos se guarda la alarma en la base de datos
            

            # print("El CRC recibido es: ", crc_recibido)
            # print("La longitud del mensaje es: ", longitud_recibida)
            # print("El protocolo utilizado es: ", protocolo)
            # print("El número de secuencia es: ", num_secuencia)
            # print("El receptor es: ", receptor)
            # print("El prefijo de cuenta es: ", prefijoCuenta)
            # print("El número de cuenta 1 es: ", numCuenta_1)
            # print("El número de cuenta 2 es: ", numCuenta_2)
            # print("El mensaje CID es: ", mensaje_CID)
            # print("El tipo de extended data es: ", tipoExtendedData)
            # print("El extended data es: ", extendedData)
            # print("La fecha es: ", fecha)
            #print("El mensaje base es: ", base_mensaje)

            if protocolo == "ADM-CID" and cifrado_flag == "*":  
                crc_calculado = calcular_crc(base_mensaje)
                longitud_calculada = len(base_mensaje)

                # print("El crc calculado es: ", crc_calculado)
                # print("La longitud calculada es: ", longitud_calculada)

            if protocolo == "ADM-CID":
                #Ahora hay que comprobar si el CRC es correcto y si la longitud del mensaje es correcta
                if extendedData == "":
                    base_mensaje = f'"{cifrado_flag}{protocolo}"{num_secuencia:04d}R{receptor:x}L{prefijoCuenta:x}#{numCuenta_1:x}[#{numCuenta_2:x}|{mensaje_CID}]_{fecha}'.upper(
                    )
                else: 
                    base_mensaje = f'"{cifrado_flag}{protocolo}"{num_secuencia:04d}R{receptor:x}L{prefijoCuenta:x}#{numCuenta_1:x}[#{numCuenta_2:x}|{mensaje_CID}][{extendedData}]_{fecha}'.upper()

                if cifrado_flag == "": 
                    #print("El mensaje que le entra al crc es: ", base_mensaje)
                    crc_calculado = calcular_crc(base_mensaje)
                    longitud_calculada = len(base_mensaje)

            elif protocolo == "NULL":
                base_mensaje = f'"{protocolo}"{num_secuencia:04d}R{receptor:x}L{prefijoCuenta:x}#{numCuenta_1:x}[]_{fecha}'.upper()
                #print("El mensaje que le entra al crc es: ", base_mensaje)
                crc_calculado = calcular_crc(base_mensaje)
                longitud_calculada = len(base_mensaje)

        
            #print(crc_calculado)

            #Estructurar el mensaje de ACK
            # Se definen los caracteres de control del mensaje
            LF = "\n"  # Esto es LF (Line Feed)
            CR = "\r"  # Esto es CR (Carriage Return) 

            ack_texto = "ACK" #Esto es el mensaje de ACK
            
            ack_previo = f'"{ack_texto}"{num_secuencia:04d}R{receptor:x}L{prefijoCuenta:x}#{numCuenta_1:x}[]{CR}'.upper()
            crc_ack = calcular_crc(ack_previo)
            length_ack = len(ack_previo)  # Esto es el código de longitud del mensaje
            length_str_ack = str(length_ack).zfill(3)[-3:] # Esto es el código de longitud del mensaje (3 caracteres ASCII)
            Message_ack = f'{LF}{crc_ack}0{length_str_ack}{ack_previo}{CR}'

            Message_bytes_ack = Message_ack.encode('ascii') #Se codifica el mensaje en ascii
            

            #Estructurar el mensaje de NACK
            ahora = time.time()
            nack_texto = "NACK"  # Esto es el mensaje de NACK

            nack_previo = f'"{nack_texto}"0000R0L0#0[]{ahora}{CR}'.upper()
            crc_nack = calcular_crc(nack_previo)
            length_nack = len(nack_previo)  # Esto es el código de longitud del mensaje
            length_str_nack = str(length_nack).zfill(3)[-3:] # Esto es el código de longitud del mensaje (3 caracteres ASCII)
            Message_nack = f'{LF}{crc_nack}0{length_str_nack}{nack_previo}{CR}'

            Message_bytes_nack = Message_nack.encode('ascii') #Se codifica el mensaje en ascii

            time.sleep(1) #Esperamos 1 segundo

            if crc_recibido != crc_calculado:
                print("El CRC no es correcto")
                serverSock_seguro.send(Message_bytes_nack)
                intentos += 1

            elif longitud_recibida != longitud_calculada:
                print("La longitud del mensaje no es correcta")
                serverSock_seguro.send(Message_bytes_nack)
                intentos += 1
            elif not validar_fecha(fecha):
                print("La fecha no es correcta")
                serverSock_seguro.send(Message_bytes_nack)
                intentos += 1
            elif test == 1: 
                serverSock_seguro.send(Message_bytes_nack)
                test = 0
                intentos += 1
            else:
                # Enviamos un mensaje de ACK al cliente
                # Se envía el mensaje al servidor usando el socket
                serverSock_seguro.send(Message_bytes_ack)
                print("El mensaje fue recibido correctamente")

                numCuenta_1 = hex(numCuenta_1)[2:].upper()
                receptor = hex(receptor)[2:].upper()
                prefijoCuenta = hex(prefijoCuenta)[2:].upper()

                # Guardar coordenadas de la alarma en la base de datos
                if x is not None:
                    xguardar = x
                    yguardar = y
                    zguardar = z

                video = None
                if datosVideo is not None:
                    fechaVideo = float(fecha)
                    fechaVideo = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(fechaVideo))

                    video = f"static/videos/video_{numCuenta_1}_{receptor}_{prefijoCuenta}__{fechaVideo}.mp4"
        # Formatear de nuevo a un formato que es seguro para nombres de archivos
                    imagePath = f"static/imagenes/imagen_{numCuenta_1}_{receptor}_{prefijoCuenta}__{fechaVideo}.jpg"

                    recibirVideo(serverSock_seguro, video, datosVideo)

                    extraer_frame_central(video, imagePath)

                    #enviarWhatsappSegundoPlano(prefijoCuenta, numCuenta_1, receptor, imagePath, fecha)

                    guardarAlarma(receptor, prefijoCuenta, numCuenta_1, protocolo, fecha, video, xguardar, yguardar, zguardar)
                    
                    

                serverSock_seguro.close()

                break

        if intentos == 3:
            print("Se han superado los intentos de envío")
            break

    except Exception as e:
        print(f'Error en el servidor: {e}')
        
        break
    
    
 
