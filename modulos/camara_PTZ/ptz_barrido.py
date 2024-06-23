"""
Este script implementa el módulo dedicado a hacer los diferentes tipos de baridos posibles por la cámara PTZ

Autor: Luis Gimeno San Frutos
"""

from time import sleep
from threading import Thread, Event

class PTZBarrido:
    """
    Clase PTZBarrido para realizar los diferentes tipos de barrido.

    Atributos:

        camera(ptzControl): Objeto de la clase ptzControl a través del cual se realiza el barrido.
        detener_barrido(Event): Evento que marca cuando ha de detenerse el barrido.
        barrido_thread(Thread): Hilo generado para realizar el barrido.
        estado(bool): Variable booleana que indica si el barrido está activo o no.
        barrido_acabado(bool): Variable booleana que indica si el barrido ha finalizado.
        barrido_post(bool): Varibale booleana que indica si se está realizando un barrido post-pérdida.

    Métodos:

        __init__(self, camera): Constructor de la clase.
        iniciar_barrido(self,selector): Inicia el tipo de barrido seleccionado.
        detener_barrido_por_aviso(self): Detiene el barrido en caso de un aviso a través de un Event.
        barrido_inicial(self): Realiza el barrido inicial.
        barrido(self): Realiza el barrido genérico
        barrido_post_perida(self): Realiza el barrido post-perdida.
        clear_detener_barrido(self): Limpia el evento que detiene el barrido.

    """

    def __init__(self, camera, iter_inicial, iter_normal):
        """
        Constructor de la clase PTZBarrido.

        Args:
            camera: objeto de la clase ptzControl a través del cual se realiza el barrido.
        """
        self.camera = camera
        self.detener_barrido = Event()
        self.barrido_thread = None
        self.estado=False
        self.barrido_acabado=False
        self.barrido_post=False
        self.iter_inicial = iter_inicial
        self.iter_normal = iter_normal
        self.velocidad = 0.17
        
    def iniciar_barrido(self,selector):
        """
        Inicia el proceso de barrido seleccionado en un hilo separado.
        
        Args:
            selector: selecciona el tipo de barrido a realizar.
        """
        self.estado=True                                                            # Se indica que el barrido está activo a través de la variable estado.

        if self.barrido_thread is None or not self.barrido_thread.is_alive():       # Se comprueba que no haya ningún barrido activo.
            self.clear_detener_barrido()                                            # Asegurar que el evento para detener el barrido esté limpio al comenzar.

            if selector==0:                                                         # Si el selector vale 0 se inicia un barrido inicial.
                self.barrido_thread = Thread(target=self.barrido_inicial)
                self.barrido_thread.start()

            elif selector==1:                                                       # Si el selector vale 1 se inicia un barrido estándar.
                self.barrido_thread = Thread(target=self.barrido)
                self.barrido_thread.start()
                
            elif selector==2:                                                       # Si el selector vale 2 se inicia un barrido post-pérdida.
                self.barrido_thread = Thread(target=self.barrido_post_perida)
                self.barrido_thread.start()

    def detener_barrido_por_aviso(self):
        """
        Detiene el barrido a través del evento.
        """
        self.detener_barrido.set()      # Se establece el evento para detener el barrido.
        self.estado=False               # Se indica que el barrido ya no está activo a través de la variable estado

    def barrido_inicial(self):
        
        """
        Realiza el barrido inicial con la cámara PTZ.
        Se trata de un barrido más extenso que realiza 7 giros de 360º con diferentes inclinaciones variando desde un apuntamiento paralelo al plano del suelo hasta un apuntamiento perpendicualr a este.
        """
        inst_par_impar = 1                               # Creamos un incidador para saber si estamos en una iteración par o impar
        i = 0                                            # Creramos un contador de iteraciones
        incl = 1/6                                       # Creamos una varible para los saltos de inclinación. 1/6 corresponde a 15 grados en el formato que trabaja la cámara PTZ.
        zoom=self.camera.get_current_zoom()              # Obtenemos el zoom actual de la cámara
        var=0.04-zoom                                    # Calculamos la variación entre el zoom actual y el zoom mínimo de la cámara.
        _, tilt = self.camera.get_current_pan_tilt()     # Obtenemos la inclinación actual de la cámara.
        
        while not self.detener_barrido.is_set():         # Comprobamos que el evento de detener barrido no esté activado antes de cada iteración sobre el bucle.

            if inst_par_impar % 2 == 1:

                if i == 0:
                    self.camera.move_relative_zoom(1, -tilt, self.velocidad, 0.3, var, 1)   # Si es la primera iteración se lleva la cámara a la inclinzación paralela al suelo, se devuelve el zoom al zoom al mínimo y se realiza el primer medio giro.
                else:
                    self.camera.move_relative(1, incl, self.velocidad, 0.3)                 # Si es una iteración impar diferente de la primera se realiza medio giro a la vez que se aumenta la inclinación 15º.
            else:
                self.camera.move_relative(1, 0, self.velocidad, 0.3)                        # Si es una iteración impar tan solo se realiza medio giro sin variar la inclinación.

            sleep(12)                                                            # Se hace una espera de 5 segundos para que se complete el giro.

            if i == self.iter_inicial or self.detener_barrido.is_set():                        # Se comprueba si la iteración es la número 13 (la última) o si se ha activado el evento de detener el barrido.

                if i == self.iter_inicial:                                                       # Si es la última se devuelve la cámara a 15º de inclinación y se pone a True la variable que indica que el barrido a acabado.
                    _, tilt_final = self.camera.get_current_pan_tilt()
                    self.camera.move_relative(0, -tilt_final + (0.5/3), 0, 1)
                    self.barrido_acabado=True

                self.estado=False                                               # Se desactiva el estado del barrido indicando que ya no está activo
                print("EL BARRIDO HA ACABADO")
                break

            inst_par_impar += 1
            i += 1


    def barrido(self):
        """
        Realiza el barrido estándar con la cámara PTZ.
        Se trata de un barrido general que realiza 4 giros de 360º con diferentes inclinaciones variando desde un apuntamiento paralelo al plano del suelo hasta un apuntamiento perpendicualr a este.
        """
        inst_par_impar = 1
        i = 0
        incl = 1/3
        _, tilt = self.camera.get_current_pan_tilt()
        zoom=self.camera.get_current_zoom()
        var=0.04-zoom
        
        while not self.detener_barrido.is_set():

            if inst_par_impar % 2 == 1:
                if i == 0:
                    self.camera.move_relative_zoom(1, -tilt, self.velocidad, 0.3, var, 1)
                else:
                    self.camera.move_relative(1, incl, self.velocidad, 0.3)
            else:
                self.camera.move_relative(1, 0, self.velocidad, 0.3)
            sleep(12)  

            if i == self.iter_normal or self.detener_barrido.is_set():
                if i == self.iter_normal:
                    _, tilt_final = self.camera.get_current_pan_tilt()
                    self.camera.move_relative(0, -tilt_final + (0.5/3), 0, 1)
                    self.barrido_acabado=True
                self.estado=False
                print("EL BARRIDO HA ACABADO")
                break

            inst_par_impar += 1
            i += 1

            
    def barrido_post_perida(self):
        """
        Realiza el barrido post-pérdida con la cámara PTZ.
        Se trata de un barrido que se realiza una vez se pierde el dron con el objetivo de volverlo a encontrar realizandos 3 giros de 360º completos, uno a la misma inclinación que se ha perido el dron, uno 30º por debajo y uno 30º por arriba.
        """
        self.barrido_post=True
        inst_par_impar = 1
        i = 0
        incl = 1/3
        _, tilt = self.camera.get_current_pan_tilt()
        zoom=self.camera.get_current_zoom()
        var=0.04-zoom
        tilt_2=tilt-2/6
        if tilt_2<=-11:tilt_2=-1
        var=tilt_2-tilt
        while not self.detener_barrido.is_set():

            if inst_par_impar % 2 == 1:
                if i == 0:
                    self.camera.move_relative_zoom(1, 0,  self.velocidad, 0.3, var, 1)
                elif i==2:
                    self.camera.move_relative(1, -1/6,  self.velocidad, 0.3)
                    _, tilt = self.camera.get_current_pan_tilt()
                    tilt_2=tilt+2/6
                    if tilt_2>=1:tilt_2=1
                    var=tilt_2-tilt
                elif i==4:
                    self.camera.move_relative(1, var,  self.velocidad, 0.3)
            else:
                self.camera.move_relative(1, 0,  self.velocidad, 0.3)

            sleep(12)  

            if i == 5 or self.detener_barrido.is_set():
                if i==5:
                    _, tilt_final = self.camera.get_current_pan_tilt()
                    zoom=self.camera.get_current_zoom()
                    var=0.04-zoom
                    self.camera.move_relative_zoom(0, -tilt_final + (0.5/3), 0, 1, var, 1)
                    self.barrido_acabado=True
                self.estado=False
                self.barrido_post=False
                print("EL BARRIDO HA ACABADO")
                break

            inst_par_impar += 1
            i += 1


    def clear_detener_barrido(self):
        """
        Limpia el evento una vez que el barrido ha finalizado o ha sido detenido.
        """
        self.detener_barrido.clear()        # Se limpia el evento
