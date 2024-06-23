# ---------------------------------------- CÓDIGO PARA IMPLEMENTAR EL CLIENTE CON SOCKETS ----------------------

import socket

# Configura el cliente
host = '192.168.110.4'  # Dirección IP del servidor
port = 8080       # Puerto en el que el servidor está escuchando

# Crea un socket TCP/IP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conéctate al servidor
client_socket.connect((host, port))

# Espera un aviso del servidor ---> ha empezado el barrido inicial
barrido_inicial = client_socket.recv(1024).decode('utf-8')
print(f"-----------SE HA EMPEZADO EL BARRIDO INICIAL: {barrido_inicial}")

# Espera un aviso del servidor ---> al hacer el barrido inicial se ha detectado un dron o no (lo normal es que no se detecte dron)
respuesta_inicial = client_socket.recv(1024).decode('utf-8')
print(f"-----------EN EL BARRIDO INICIAL SE HA DETECTADO UN DRON (0->NO DET, 1-> SI DET): {respuesta_inicial}")
respuesta_inicial=int(respuesta_inicial)      # Pasar la variable respuesta_inicial a int para poder interpretarlo

if respuesta_inicial==1:
    # Espera un aviso del servidor ---> cuando pierda la deteccion
    lost_inicial = client_socket.recv(1024).decode('utf-8')
    print(f"-----------SE HA PERDIDO EL DRON DETECTADO EN EL BARRIDO INICIAL: {lost_inicial}")

while True:
    # Envía un mensaje al servidor
    message = input("-----------------ENVIA UNA ALARMA EN CASO DE HABERLA: ")
    client_socket.send(message.encode('utf-8'))

    # Espera una respuesta del servidor
    received_message = client_socket.recv(1024).decode('utf-8')
    print(f"-----------LA RESPUESTA DE LA CÁMARA ES (0->NO DET, 1->SI DET): {received_message}")
    received_message=int(received_message)      # Pasar la variable received_message a int para poder interpretarlo
    
    if received_message==1:
        # Espera una respuesta del servidor para indicar que lo ha perdido despueś de encontrarlo
        lost_message = client_socket.recv(1024).decode('utf-8')
        print(f"-----------SE HA PERDIDO EL DRON: {lost_message}")

# Cierra la conexión con el servidor
client_socket.close()
