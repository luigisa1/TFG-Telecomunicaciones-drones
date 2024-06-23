import socket
import threading

def receive_messages():
    while True:
        # Recibe mensajes continuamente del servidor
        received_message = client_socket.recv(1024).decode('utf-8')
        print(f"-----------MENSAJE RECIBIDO DEL SERVIDOR: {received_message}")
        if received_message == 'end':
            print("-----------FIN DEL SERVIDOR.")
            break

def send_messages():
    while True:
        # Envia mensajes al servidor introducidos por el usuario
        message = input("-----------ENVIA UN MENSAJE AL SERVIDOR: ")
        client_socket.send(message.encode('utf-8'))
        if message == 'end':
            print("-----------FIN DE LA COMUNICACIÓN POR EL CLIENTE.")
            break

# Configuración del cliente
host = '192.168.110.4'  # Dirección IP del servidor
port = 8080  # Puerto en el que el servidor está escuchando

# Crea un socket TCP/IP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conectarse al servidor
client_socket.connect((host, port))

# Inicia hilos para enviar y recibir mensajes
thread_receiver = threading.Thread(target=receive_messages)
thread_sender = threading.Thread(target=send_messages)

# Iniciar hilos
thread_receiver.start()
thread_sender.start()

# Esperar a que ambos hilos terminen
thread_receiver.join()
thread_sender.join()

# Cierra la conexión con el servidor
client_socket.close()
