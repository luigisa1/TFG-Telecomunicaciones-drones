import json
import time
from cliente.claseTransmisor_original import TransmisorSIA
import socket

def load_config():
    with open('config.json', 'r') as file:
        config = json.load(file)
    return config


def parse_hex_value(hex_string):
    return int(hex_string, 16)

# Crear un cliente de la clase Transmisor
# Configuraciones de la alarma
# Cargar configuraciones del archivo config.json, buenísimo para no tener que cambiar el código fuente
config = load_config()
mantenimiento = bool(int(config['MANTENIMIENTO']))
cifrado_flag = bool(int(config['CIFRADO']))

CLIENT_ACCOUNT_NUMBER = parse_hex_value(config['CLIENT_ACCOUNT_NUMBER'])
CLIENT_ACCOUNT_PREFIX = parse_hex_value(config['CLIENT_ACCOUNT_PREFIX'])
CLIENT_RECEIVER_NUMBER = parse_hex_value(config['CLIENT_RECEIVER_NUMBER'])
# COnfiguraciones del servidor
SERVER_ADDRESS = config['SERVER_ADDRESS']
SERVER_PORT = config['SERVER_PORT']
PROTOCOLO = config['PROTOCOLO']


# Se crea el objeto transmisor omitiendo algunos datos y se comprueba que envía mensajes correctamente
transmisor = TransmisorSIA(serverAddress="127.0.0.1",serverPort=SERVER_PORT)
transmisor.setCliente(CLIENT_ACCOUNT_NUMBER, CLIENT_ACCOUNT_PREFIX, CLIENT_RECEIVER_NUMBER)
#Se mira si las configuraciones son correctas
print("Configuraciones del cliente: ", transmisor.getCliente())
print("Configuraciones del servidor: ", transmisor.getServer())
print("Configuraciones de la comunicación: ", transmisor.getMantenimiento(), transmisor.getCifrado())

transmisor.setMantenimiento(mantenimiento)
transmisor.setCifrado(cifrado_flag)

# print("Espera para separar y ver si se envia el ataque")
# time.sleep(3)
# # Prueba de ataque, a ver que pasa
# # import socket
# fakeSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# fakeSock.sendto(b"Mensaje de ataque", (SERVER_ADDRESS, SERVER_PORT))
# print("Mensaje de ataque enviado")
# time.sleep(3)

# Se envía un mensaje de alarma

transmisor.enviarAlarma(video_path="madriguera.mp4", x = 2.45, y = 3, z = 8.443)  # Debería mandqar por sockets UPD el mensaje de alarma

# # print("Espera para separar y ver si se envia el ataque")
time.sleep(30)
# # Debería mandar por sockets UPD el mensaje de alarma
# transmisor.enviarAlarma(x=7.33, y=8.22, z=9.11)
# time.sleep(3)
# transmisor.enviarAlarma()  # Debería mandar por sockets UPD el mensaje de alarma
# #Prueba de ataque, a ver que pasa
# # import socket
# fakeSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# fakeSock.sendto(b"Mensaje de ataque", (SERVER_ADDRESS, SERVER_PORT))
# print("Mensaje de ataque enviado")
# time.sleep(5)

transmisor.enviarInicioSistema()  # Debería mandar por sockets UPD el mensaje de inicio de sistema
time.sleep(30)
transmisor.enviarCaidaSistema()  # Debería mandar por sockets UPD el mensaje de fin de sistema

# # Se cambian las configuraciones que no se pasaron en el constructor
# transmisor.setCliente(CLIENT_ACCOUNT_NUMBER, CLIENT_ACCOUNT_PREFIX, CLIENT_RECEIVER_NUMBER)

# #Se envía el mensaje con todas las configuraciones
# transmisor.enviarAlarma()

# # Se cambian las configuraciones
# transmisor.setMantenimiento(1)
# transmisor.setCifrado(1)

# #Se envia un mensaje cifrado 
# transmisor.enviarAlarma()  # Debería mandar por sockets UDP el mensaje de alarma cifrado

# time.sleep(30)  # Esperar 30 segundos para que se imprima el mensaje de mantenimiento al menos 1 vez y comprobar que va en paralelo a cualquier otra cosa

# # Se cambian las configuraciones de nombre del cliente
# # "CLIENT_ACCOUNT_NUMBER": "0x9A9A",
# # "CLIENT_ACCOUNT_PREFIX": "0x111",
# # "CLIENT_RECEIVER_NUMBER": "0x00",

# transmisor.setCliente(0x9A9A, 0x111, 0x00) 

# # Se envía un mensaje de alarma con las nuevas configuraciones y sin cifrar para verlo 
# transmisor.setCifrado(0)
# transmisor.enviarAlarma()


while True:
    pass