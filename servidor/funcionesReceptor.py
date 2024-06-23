# Cálculo del CRC
import datetime
from receptorDesencriptado import desencriptado_limpio
# import pywhatkit
import sys
import threading

def esperaHandshake(serverSock_seguro):
    # 7. Realizar el handshake
    try:
        serverSock_seguro.do_handshake()
        pass
    except Exception as e:
        print(f'Error en el handshake: {e}')
        sys.exit(1)

def calcular_crc(mensaje):
    
    # Se convierte el mensaje a bytes
    mensaje_bytes = mensaje.encode('ascii')
    print("El mensaje que entra al crc es: ", repr(mensaje_bytes))

    # Se inicializa el CRC
    crc = 0

    # Se calcula el CRC
    for byte in mensaje_bytes:
        crc = crc ^ byte
        for i in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408  # 0x8408 es el polinomio del CRC-16
            else:
                crc = crc >> 1

    # Se convierte el CRC a 4 caracteres ASCII
    crc = crc.to_bytes(2, byteorder='big').hex().upper()

    return crc


# Función para validar la fecha con un margen de +-20 segundos
def validar_fecha(fecha_recibida):
    print("La fecha recibida es: ", fecha_recibida)
    # Obtener la fecha actual en UTC
    # Obtener la fecha actual en UTC
    fecha_actual = datetime.datetime.utcnow()

    # Convertir la fecha recibida a un objeto datetime
# Convertir la fecha epoch en un objeto datetime
    fecha_recibida_epoch = float(fecha_recibida)
    fecha_recibida_obj = datetime.datetime.utcfromtimestamp(fecha_recibida_epoch)


    # Calcular la diferencia en segundos entre la fecha recibida y la fecha actual
    diferencia = (fecha_actual - fecha_recibida_obj).total_seconds()

    # Validar si la diferencia está dentro del margen de +-20 segundos
    if diferencia <= 20 and diferencia >= -40:
        return True
    else:
        print("La fecha no es correcta, recibida:",
              fecha_recibida, "actual:", fecha_actual)

        return False


def extraer_datos(mensaje):
    x = y = z = v = None
    print("El mensaje recibido es: ", repr(mensaje))

    # Inicio del mensaje
    # Buscamos el primer caracter que siempre es un salto de línea
    primer_caracter = mensaje.find("\n")

    crc = mensaje[primer_caracter+1:primer_caracter+5]  # Extraemos el CRC
    # print("crc recibido es: ",crc)

    # 2) Longitud del mensaje
    indice_primer_cero = mensaje.find("0", primer_caracter+5)
    longitud = int(mensaje[indice_primer_cero+1:indice_primer_cero+4])
    # print("longitud recibida del mensaje es: ", longitud)

    # 3) El protocolo utilizado y averiguación de si está cifrado
    inicio_cadena_comillas = mensaje.find('"') + 1
    fin_cadena_comillas = mensaje.find('"', inicio_cadena_comillas)
    protocolo = mensaje[inicio_cadena_comillas:fin_cadena_comillas]

    cifrado_flag = protocolo.find("*")
    if cifrado_flag != -1:
        cifrado_flag = "*"
        print("El mensaje está cifrado")
        protocolo = protocolo.replace("*", "")
    else:
        cifrado_flag = ""
        print("El mensaje no está cifrado")

    # print("El protocolo utilizado es: ", protocolo)

    # 4) Número de secuencia
    secuencia = int(mensaje[fin_cadena_comillas+1:fin_cadena_comillas+5])
    # print("secuencia: ", secuencia)

    # 5) El número de receptor
    inicio_cadena_receptor = mensaje.find('R') + 1
    fin_cadena_receptor = mensaje.find('L', inicio_cadena_receptor)
    receptor = int(mensaje[inicio_cadena_receptor:fin_cadena_receptor], 16)
    #print("El receptor es: ", receptor)

    # 6) El prefijo de cuenta
    inicio_cadena_prefijo = mensaje.find('L', fin_cadena_receptor) + 1
    fin_cadena_prefijo = mensaje.find('#', inicio_cadena_prefijo)
    prefijoCuenta = int(mensaje[inicio_cadena_prefijo:fin_cadena_prefijo], 16)
    #print("El prefijo de cuenta es: ", prefijoCuenta)

    # 7) numCuenta_1
    inicio_cadena_cuenta1 = mensaje.find('#') + 1
    fin_cadena_cuenta1 = mensaje.find('[', inicio_cadena_cuenta1)
    numCuenta_1 = int(mensaje[inicio_cadena_cuenta1:fin_cadena_cuenta1], 16)
    #print("El número de cuenta 1 es: ", numCuenta_1)

    if protocolo == "ADM-CID":
        base_mensaje = mensaje[inicio_cadena_comillas-1:mensaje.find('\r')]
        #print("El mensaje base es: ", base_mensaje)

        # Si el mensaje está cifrado, se debe desencriptar y retirar el padding
        if cifrado_flag == "*":
            # Por limpieza, se desencripta el mensaje en otro lado
            mensaje = desencriptado_limpio(mensaje)

        # 8) numCuenta_2
        inicio_cadena_cuenta2 = mensaje.find('[#') + 2
        fin_cadena_cuenta2 = mensaje.find('|', inicio_cadena_cuenta2)
        numCuenta_2 = int(
            mensaje[inicio_cadena_cuenta2:fin_cadena_cuenta2], 16)
        # print("numCuenta_2: ", numCuenta_2)

        # 9) mensaje_CID
        inicio_cadena_mensaje = mensaje.find('|') + 1
        fin_cadena_mensaje = mensaje.find(']', inicio_cadena_mensaje)
        mensaje_CID = mensaje[inicio_cadena_mensaje:fin_cadena_mensaje]
        # print("mensaje_CID: ", mensaje_CID)

        # 10) extendedData separando el primer caracter del resto de la cadena
        inicio_cadena_corchetes = mensaje.find('][') + 1
        if inicio_cadena_corchetes != 0: 
            fin_cadena_corchetes = mensaje.find(']', inicio_cadena_corchetes)
            cadena_corchetes = mensaje[inicio_cadena_corchetes:fin_cadena_corchetes]
            extendedData = cadena_corchetes[1:]
        else:
            extendedData = ""

        print("ExtendedData: ", extendedData)


        # print("tipoExtendedData: ", tipoExtendedData)

        #10.2) Ahora el extendedData es separable, se puede hacer un split por X, Y, Z y V para obtener los valores
        
        if 'X' in extendedData and 'Y' in extendedData and 'Z' in extendedData:

            xini = extendedData.find('X') + 1
            xfin = extendedData.find('Y')
            x = extendedData[xini:xfin]

            yini = extendedData.find('Y') + 1
            yfin = extendedData.find('Z')
            y = extendedData[yini:yfin]

            zini = extendedData.find('Z') + 1
            if 'V' in extendedData:
                zfin = extendedData.find('V')
                z = extendedData[zini:zfin]
            else: 
                zfin = extendedData.find(']')
                z = extendedData[zini:]

        if 'V' in extendedData:

            vini = extendedData.find('V') + 1
            vfin = extendedData.find(']')
            v = extendedData[vini:]

        # 11) Toda la cadena, que es una fecha, entre el siguiente _ y el final.
        inicio_fecha = mensaje.find('_') + 1
        fin_fecha = mensaje.find('\r')
        fecha = mensaje[inicio_fecha:fin_fecha]
        # print("fecha: ", fecha)

    elif protocolo == "NULL":
        base_mensaje = mensaje[inicio_cadena_comillas-1:mensaje.find('\r')]
        numCuenta_2 = 0
        mensaje_CID = ""
        extendedData = ""
        # 11) Toda la cadena, que es una fecha, entre el siguiente _ y el final.
        inicio_fecha = mensaje.find('_') + 1
        fin_fecha = mensaje.find('\r')
        fecha = mensaje[inicio_fecha:fin_fecha]
        # print(fecha)

    print(f'Las coordenadas que se extraen son: x: {x}, y: {y}, z: {z}')

    return (base_mensaje, crc,
            longitud,
            protocolo,
            secuencia,
            receptor,
            prefijoCuenta,
            numCuenta_1,
            numCuenta_2,
            mensaje_CID, extendedData,
            fecha, cifrado_flag,
            x, y, z, v)


# def enviarWhatsapp(prefijoCuenta, numCuenta_1, receptor, imagePath, fecha):
#     # Código usando Pywhatkit. Menos completo pero gratuito
#     #Cambio en la fecha para que whatsapp lo pueda enviar
#     fecha = float(fecha)
#     fecha = datetime.datetime.utcfromtimestamp(fecha)
#     fecha = fecha.strftime("%H:%M:%S %d-%m-%Y")

#     try:
#         pywhatkit.sendwhats_image(
#             "+34662555969",

#             imagePath,

#             caption="Intrusión detectada en el receptor " + str(receptor) + " de la casa con número de cuenta " + str(prefijoCuenta) + "_" + str(numCuenta_1) + " en la fecha " + fecha + "." + " Para ver el video completo, entre a la aplicación de seguridad.",

#             wait_time=15,

#             tab_close=True)
#     except Exception as e:
#         print("Error al enviar el mensaje de WhatsApp: ", e)
#         pass


# def enviarWhatsappSegundoPlano(prefijoCuenta, numCuenta_1, receptor, imagePath, fecha):
    
#     hilo = threading.Thread(target=enviarWhatsapp, args=(prefijoCuenta, numCuenta_1, receptor, imagePath, fecha))
#     hilo.start()


