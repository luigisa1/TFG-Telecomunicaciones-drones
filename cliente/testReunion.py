import time
from claseTransmisor import TransmisorSIA
import socket

mantenimiento = 0
cifrado_flag = 0

CLIENT_ACCOUNT_NUMBER =0x111A
CLIENT_ACCOUNT_PREFIX = 0x22B
CLIENT_RECEIVER_NUMBER = 0x3A
# COnfiguraciones del servidor
SERVER_ADDRESS = '172.233.107.104'
SERVER_PORT = 19000


# Se crea el objeto transmisor 
transmisor = TransmisorSIA(serverAddress=SERVER_ADDRESS,serverPort=SERVER_PORT)
transmisor.setCliente(CLIENT_ACCOUNT_NUMBER, CLIENT_ACCOUNT_PREFIX, CLIENT_RECEIVER_NUMBER)
transmisor.setMantenimiento(mantenimiento)
transmisor.setCifrado(cifrado_flag)

total_mensajes = 6
tiempo_ciclo = 4
# espaciado = tiempo_ciclo/total_mensajes
espaciado = tiempo_ciclo

with open('mensajes_log.txt', 'w') as archivo:
    while True:
    # Prueba de mensaje
        print("Mensaje 1") #Funciona bien
        try:
            transmisor.enviarInicioSistema()  # Debería mandar por sockets UPD el mensaje de inicio de sistema
            mensaje = 'Mensaje Inicio'
            hora_legible = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hora_epoch = int(time.time())
            archivo.write(f'{hora_legible} - ({hora_epoch}) -> {mensaje}\n')
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(espaciado) 

        try:
            print("Mensaje 2") #Funciona bien
            transmisor.enviarAlarma()
            mensaje = 'Mensaje Alarma sin xdata'
            hora_legible = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hora_epoch = int(time.time())
            archivo.write(f'{hora_legible} - ({hora_epoch}) -> {mensaje}\n')
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(espaciado)

        print("Mensaje 3") #Funciona bien

        try:
            transmisor.enviarAlarma(x = 2.45, y = 3, z = 8.443)
            mensaje = 'Mensaje Alarma con coord'
            hora_legible = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hora_epoch = int(time.time())
            archivo.write(f'{hora_legible} - ({hora_epoch}) -> {mensaje}\n')
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(espaciado)

        print("Mensaje 4") #Funciona bien

        try:
            transmisor.enviarNull()
            mensaje = 'Mensaje Null'
            hora_legible = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hora_epoch = int(time.time())
            archivo.write(f'{hora_legible} - ({hora_epoch}) -> {mensaje}\n')
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(espaciado)
        print("Mensaje 5") #Funciona bien

        try:
            transmisor.enviarCaidaSistema()
            mensaje = 'Mensaje Caida Sistema'  
            hora_legible = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hora_epoch = int(time.time())
            archivo.write(f'{hora_legible} - ({hora_epoch}) -> {mensaje}\n')
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(espaciado)

        print("Mensaje 6")

        try:
            transmisor.enviarAlarma(video_path="/home/diadron/ultralytics/video_detect/output.mp4", x = 2.45, y = 3, z = 8.443)
            mensaje = 'Mensaje Alarma con video y coord'
            hora_legible = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hora_epoch = int(time.time())
            archivo.write(f'{hora_legible} - ({hora_epoch}) -> {mensaje}\n')
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(espaciado)