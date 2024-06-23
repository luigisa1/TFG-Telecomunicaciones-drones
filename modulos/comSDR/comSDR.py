import socket

class ComunicacionSDR:
    def __init__(self, host, port, modo='cliente'):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.modo = modo  # Puede ser 'cliente' o 'servidor'
        self.alarma = True
        self.distancia = None
        
    def iniciar(self):
        if self.modo == 'cliente':
            self.conectar()
        elif self.modo == 'servidor':
            self.configurar_servidor()
            self.aceptar_conexion()

    def conectar(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Conexión establecida con el SDR en {self.host}:{self.port} como cliente")
        except Exception as e:
            print(f"Error al conectar con el SDR: {e}")
            self.connected = False

    def configurar_servidor(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            print(f"Servidor SDR configurado y escuchando en {self.host}:{self.port}")
        except Exception as e:
            print(f"Error al configurar el servidor SDR: {e}")
            self.connected = False

    def aceptar_conexion(self):
        try:
            self.client_socket, self.address = self.socket.accept()
            self.connected = True
            print(f"Conexión aceptada de {self.address}")
        except Exception as e:
            print(f"Error al aceptar la conexión: {e}")
            self.connected = False

    def recibir_alarma(self):
        while True:
            if self.connected:
                try:
                    print("A la espera de una alarma")
                    data_socket = self.client_socket if self.modo == 'servidor' else self.socket
                    respuesta=data_socket.recv(1024).decode('utf-8') 
                    if respuesta=="alarma":
                        self.alarma = True
                        print(f"Alarma recibida: {self.alarma}")
                    else:
                        respuesta=float(respuesta)
                        self.distancia=respuesta
                        print(f"Distancia recibida: {self.distancia}")

                except Exception as e:
                    print(f"Error al recibir la alarma: {e}")
                    return None
            else:
                print("No conectado al SDR.")
                return None
            
    def recibir_distancia(self):
        if self.connected:
            try:
                print("Esperando distancia")
                data_socket = self.client_socket if self.modo == 'servidor' else self.socket
                distancia=data_socket.recv(1024).decode('utf-8') 
                distancia=int(distancia)
                print(f"Distancia recibida: {distancia}")
                return distancia
            except Exception as e:
                print(f"Error al recibir la alarma: {e}")
                return None
        else:
            print("No conectado al SDR.")
            return None

    def enviar_respuesta(self, mensaje):
        if self.connected:
            try:
                data_socket = self.client_socket if self.modo == 'servidor' else self.socket
                data_socket.send(str(mensaje).encode('utf-8'))
                print(f"Mensaje enviado al SDR: {mensaje}")
            except Exception as e:
                print(f"Error al enviar el mensaje al SDR: {e}")
        else:
            print("No conectado al SDR.")

    def cerrar_conexion(self):
        if self.connected:
            try:
                if self.modo == 'servidor' and hasattr(self, 'client_socket'):
                    self.client_socket.close()
                self.socket.close()
                self.connected = False
                print("Conexión con el SDR cerrada.")
            except Exception as e:
                print(f"Error al cerrar la conexión: {e}")

# Ejemplo de uso como servidor
# comunicacion_sdr = ComunicacionSDR('192.168.110.4', 8080, modo='servidor')
# comunicacion_sdr.iniciar()
# comunicacion_sdr.recibir_alarma()
# comunicacion_sdr.enviar_respuesta("Respuesta")
# comunicacion_sdr.cerrar_conexion()

# Ejemplo de uso como cliente
# comunicacion_sdr = ComunicacionSDR('192.168.1.100', 9090, modo='cliente')
# comunicacion_sdr.iniciar()
# comunicacion_sdr.enviar_respuesta("Mensaje")
# comunicacion_sdr.cerrar_conexion()
