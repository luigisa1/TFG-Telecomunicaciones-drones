import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

class AplicacionGUI:
    def __init__(self, intersection_handler, camaras, ptz_detector, ptz_barrido, core_logic_module):
        self.intersection_handler = intersection_handler
        self.camaras = camaras
        self.ptz_detector = ptz_detector
        self.ptz_barrido = ptz_barrido
        self.core_logic_module = core_logic_module

        self.root = tk.Tk()
        self.root.title('Monitor de Estado de Detections')
        self.root.geometry('800x600')  # Ajusta el tamaño según sea necesario

        # Creación de Frames para cada submódulo
        self.init_frames()

        # Inicializar la gráfica
        self.init_grafica()

        self.actualizar_estado_automatico()
        
    def init_grafica(self):
        self.fig = plt.Figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafica)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.ax.set_xlabel('Eje X')
        self.ax.set_ylabel('Eje Y')
        self.ax.set_zlabel('Eje Z')

        self.ax.set_xlim([-100, 100])
        self.ax.set_ylim([-100, 100])
        self.ax.set_zlim([0, 50])

        self.actualizar_grafica()
        
    def actualizar_grafica(self):
        self.ax.clear()
        self.ax.set_xlim([-100, 100])
        self.ax.set_ylim([-100, 100])
        self.ax.set_zlim([0, 50])
        self.dibujar_vectores_camara(self.ax, self.intersection_handler.posiciones, self.intersection_handler.vectores, self.intersection_handler.punto_dron)
        self.canvas.draw()
        self.root.after(1000, self.actualizar_grafica)  # Actualizar la gráfica cada 500 ms

    def dibujar_vectores_camara(self, ax, posiciones, vectores, p_dron):

        # print(f"Actualizando gráfica con posiciones: {posiciones}, vectores: {vectores}, punto dron: {p_dron}")

        if posiciones is not None and vectores is not None:
            colores = ['black'] * (len(posiciones))
            # Dibujar vectores de dirección para todas las cámaras
            for i, (pos, vector, color) in enumerate(zip(posiciones, vectores, colores), start=1):
                # No escalar el vector de la cámara PTZ
                # if i == len(posiciones):  # Si es la cámara PTZ
                #     vector_escalado = vector  # No escalar el vector
                # else:
                vector_escalado = [20 * v for v in vector]  # Escalar el vector x20
            
                # Dibujar el vector desde la posición de la cámara
                ax.quiver(pos[0], pos[1], pos[2], vector_escalado[0], vector_escalado[1], vector_escalado[2],
                        color=color, arrow_length_ratio=0.1, label=f'Cámara {i}')
                ax.scatter(*pos, color='black', s=20)  # Marca la posición de la cámara
                
                # if i == len(posiciones):
                #     ax.text(*pos, f'Cámara PTZ', color='black')  # Etiqueta para la posición de la cámara PTZ
                # else:
                ax.text(*pos, f'Cámara {i}', color='black')  # Etiqueta para la posición de la cámara
        
        # Dibujar los ejes X, Y, Z
        ax.quiver(0, 0, 0, 10, 0, 0, color='red', arrow_length_ratio=0.2)   # Eje X
        ax.quiver(0, 0, 0, 0, 10, 0, color='green', arrow_length_ratio=0.2) # Eje Y
        ax.quiver(0, 0, 0, 0, 0, 10, color='blue', arrow_length_ratio=0.2)  # Eje Z
        
        if p_dron is not None:
            # Marcar el punto de intersección
            ax.scatter(*p_dron, color='magenta', s=100)  # Marca el punto con un color específico y un tamaño s
            ax.text(*p_dron, "Dron", color='magenta')  # Añade una etiqueta al punto

        # Establecer los límites de los ejes
        ax.set_xlim([-5, 30])
        ax.set_ylim([-5, 30])
        ax.set_zlim([0, 20])

        # Etiquetas y leyenda
        ax.set_xlabel('Eje X')
        ax.set_ylabel('Eje Y')
        ax.set_zlabel('Eje Z')

    def toggle_camara(self, camara, label_estado_activado):
        # Alternar el estado de activado
        camara.activado = not camara.activado
        # Actualizar el label del estado de activado
        label_estado_activado.config(text='Activada' if camara.activado else 'Desactivada')

    def toggle_ptz_activado(self):
        # Alternar el estado de activado
        self.ptz_detector.activado = not self.ptz_detector.activado
        
        # Actualizar el label del estado de activado
        estado_activado = 'Sí' if self.ptz_detector.activado else 'No'
        self.label_estado_ptz_activado.config(text=f'Activado: {estado_activado}')

    def init_frames(self):
        # Frame para Intersection Handler
        self.frame_intersection_handler = ttk.LabelFrame(self.root, text="Intersection Handler", borderwidth=2, relief="groove")
        self.frame_intersection_handler.pack(fill='x', padx=5, pady=5, expand=True)

        self.estado_intersection_handler_label = ttk.Label(self.frame_intersection_handler, text='Número de cámaras fijas detectando: Pendiente')
        self.estado_intersection_handler_label.pack()

        self.estado_ptz_label = ttk.Label(self.frame_intersection_handler, text='PTZ detectando: Pendiente')
        self.estado_ptz_label.pack()

        self.estado_intersection_handler_label_2 = ttk.Label(self.frame_intersection_handler, text='Estado del modulo IntersectionHandler: Pendiente')
        self.estado_intersection_handler_label_2.pack()

        self.direccionPTZ_label = ttk.Label(self.frame_intersection_handler, text='Dirección a la que debe ir PTZ: Pendiente')
        self.direccionPTZ_label.pack()

        self.punto_dron_label = ttk.Label(self.frame_intersection_handler, text='Ubicación del dron: Pendiente')
        self.punto_dron_label.pack()


        # Frame para Cámaras
        self.frame_camaras = ttk.LabelFrame(self.root, text="Cámaras", borderwidth=2, relief="groove")
        self.frame_camaras.pack(fill='x', padx=5, pady=5, expand=True)

        self.estado_camaras_labels = []
        for i, camara in enumerate(self.camaras[:-1], start=1):
            # Crear un frame para cada cámara para contener el label y el botón
            camara_frame = ttk.Frame(self.frame_camaras)
            camara_frame.pack(fill='x', expand=True)

            # Label para mostrar el estado de detección
            label = ttk.Label(camara_frame, text=f'Cámara {i}: Detection Pendiente')
            label.pack(side='left', padx=5)

            # Label para mostrar si la cámara está activada o no
            estado_activado_label = ttk.Label(camara_frame, text='Activada' if camara.activado else 'Desactivada')
            estado_activado_label.pack(side='left', padx=5)

            # Botón para activar/desactivar la cámara
            boton_activar = ttk.Button(camara_frame, text="Activar/Desactivar", 
                                    command=lambda c=camara, l=estado_activado_label: self.toggle_camara(c, l))
            boton_activar.pack(side='left', padx=5)

            # Guardar los labels en una estructura para poder actualizarlos luego
            self.estado_camaras_labels.append((label, estado_activado_label, camara))

        # Frame para PTZ Detector
        self.frame_ptz_detector = ttk.LabelFrame(self.root, text="PTZ Detector", borderwidth=2, relief="groove")
        self.frame_ptz_detector.pack(fill='x', padx=5, pady=5, expand=True)

        self.estado_ptz_detection_label = ttk.Label(self.frame_ptz_detector, text='PTZ Detection: Pendiente')
        self.estado_ptz_detection_label.pack()

        self.estado_ptz_move_label = ttk.Label(self.frame_ptz_detector, text='PTZ Move: Pendiente')
        self.estado_ptz_move_label.pack()

        self.posicion_dron_label = ttk.Label(self.frame_ptz_detector, text='Posición dron: Pendiente')
        self.posicion_dron_label.pack()

        self.no_detections_label = ttk.Label(self.frame_ptz_detector, text='No detectiones: Pendiente')
        self.no_detections_label.pack()

        self.target_id_label = ttk.Label(self.frame_ptz_detector, text='Target ID: Pendiente')
        self.target_id_label.pack()

        # Añadiendo nuevo label y botón para activar/desactivar ptz_detector
        self.label_estado_ptz_activado = ttk.Label(self.frame_ptz_detector, text='Activado: No')
        self.label_estado_ptz_activado.pack(side='left', padx=5)

        self.boton_activar_ptz = ttk.Button(self.frame_ptz_detector, text="Activar/Desactivar PTZ", 
                                            command=self.toggle_ptz_activado)
        self.boton_activar_ptz.pack(side='left', padx=5)

        # Frame para PTZ Barrido
        self.frame_ptz_barrido = ttk.LabelFrame(self.root, text="PTZ Barrido", borderwidth=2, relief="groove")
        self.frame_ptz_barrido.pack(fill='x', padx=5, pady=5, expand=True)

        self.estado_ptz_barrido_label = ttk.Label(self.frame_ptz_barrido, text='PTZ Barrido: Pendiente')
        self.estado_ptz_barrido_label.pack()

        # Frame para el Estado del Sistema
        self.frame_estado_sistema = ttk.LabelFrame(self.root, text="Estado del Sistema", borderwidth=2, relief="groove")
        self.frame_estado_sistema.pack(fill='x', padx=5, pady=5, expand=True)

        self.estado_sistema_label = ttk.Label(self.frame_estado_sistema, text='Estado del sistema: Pendiente')
        self.estado_sistema_label.pack()

        # Frame para la gráfica
        self.frame_grafica = ttk.LabelFrame(self.root, text="Gráfica 3D", borderwidth=2, relief="groove")
        self.frame_grafica.pack(fill='both', padx=5, pady=5, expand=True)

    def actualizar_estado(self):
        # Actualiza el estado de Intersection Handler
        estado_intersection = f'Número de cámaras fijas detectando: {self.intersection_handler.detections}'
        self.estado_intersection_handler_label.config(text=estado_intersection, foreground="green" if self.intersection_handler.detections >= 1 else "red")

        estado_ptz = f'PTZ detectando: {"Sí" if self.ptz_detector.move else "No"}'
        self.estado_ptz_label.config(text=estado_ptz, foreground="green" if self.ptz_detector.move else "red")

        estado_deteccion = f'Estado del modulo IntersectionHandler: {"Activo" if self.intersection_handler.detection else "Inactivo"}'
        self.estado_intersection_handler_label_2.config(text=estado_deteccion, foreground="green" if self.intersection_handler.detection else "red")

        direccionPTZ = f'Dirección a la que debe ir PTZ: {self.intersection_handler.dir_grados}'
        self.direccionPTZ_label.config(text=direccionPTZ, foreground="red" if self.intersection_handler.dir_grados==None else "green")

        punto_dron = f'Ubicación del dron: {self.intersection_handler.punto_dron}'
        self.punto_dron_label.config(text=punto_dron, foreground="blue")

        for label_detection, label_activada, camara in self.estado_camaras_labels:
            estado_camara = 'Detection Sí' if camara.detection else 'Detection No'
            label_detection.config(text=f'{camara.name}: {estado_camara}', foreground="green" if camara.detection else "red")

            estado_activada = 'Activada' if camara.activado else 'Desactivada'
            label_activada.config(text=estado_activada, foreground="green" if camara.activado else "red")

        # Actualiza el estado de PTZ Detector
        estado_activado_ptz = 'Sí' if self.ptz_detector.activado else 'No'
        self.label_estado_ptz_activado.config(text=f'Activado: {estado_activado_ptz}', foreground="green" if self.ptz_detector.activado else "red")

        estado_ptz_detection = f'PTZ Detection: {"Seguimiento" if self.ptz_detector.detection else "Pérdida"}'
        self.estado_ptz_detection_label.config(text=estado_ptz_detection, foreground="green" if self.ptz_detector.detection else "red")

        estado_ptz_move = f'PTZ Move: {"Movimiento" if self.ptz_detector.move else "Estático"}'
        self.estado_ptz_move_label.config(text=estado_ptz_move, foreground="green" if self.ptz_detector.move else "red")

        posicion_dron = f'Posición dron: {self.ptz_detector.posicion}'
        self.posicion_dron_label.config(text=posicion_dron, foreground="red" if self.ptz_detector.posicion==None else "green")

        no_detections = f'No detectiones: {self.ptz_detector.consecutive_no_detections}'
        self.no_detections_label.config(text=no_detections, foreground="red" if self.ptz_detector.consecutive_no_detections!=0 else "green")

        target_id  = f'Target ID: {self.ptz_detector.target_id}'
        self.target_id_label.config(text=target_id, foreground="blue")

        # Actualiza el estado de PTZ Barrido
        estado_ptz_barrido = f'Barrido: {"Activo" if self.ptz_barrido.estado else "Inactivo"}'
        self.estado_ptz_barrido_label.config(text=estado_ptz_barrido, foreground="green" if self.ptz_barrido.estado else "red")

        # Actualiza el estado del Sistema
        estado_sistema = f'Estado del sistema: {self.core_logic_module.estado}'
        self.estado_sistema_label.config(text=estado_sistema, foreground="red" if self.core_logic_module.estado=="Perdida total" else "green")

    def actualizar_estado_automatico(self):
        self.actualizar_estado()
        self.root.after(200, self.actualizar_estado_automatico)  # Actualizar el estado cada 1000 ms

    def run(self):
        self.root.mainloop()

# # Simulación de datos para probar la aplicación
# class DummyIntersectionHandler:
#     def __init__(self):
#         self.detections = 2
#         self.detection = True
#         self.move_PTZ = [10, 10, 10]
#         self.punto_dron = [50, 50, 10]
#         self.aviso_cruce = False
#         self.posiciones = [[0, 0, 0], [10, 10, 10], [20, 20, 20]]
#         self.vectores = [[1, 1, 0], [0, 1, 0], [-1, 0, 1]]

# class DummyCamera:
#     def __init__(self, name):
#         self.name = name
#         self.detection = True
#         self.activado = True

# class DummyPTZDetector:
#     def __init__(self):
#         self.activado = True
#         self.detection = True
#         self.move = True
#         self.posicion = [10, 10, 10]
#         self.consecutive_no_detections = 0
#         self.target_id = 1

# class DummyPTZBarrido:
#     def __init__(self):
#         self.estado = True

# class DummyCoreLogicModule:
#     def __init__(self):
#         self.estado = "Funcionando"

# intersection_handler = DummyIntersectionHandler()
# camaras = [DummyCamera(f"Cámara {i}") for i in range(3)]
# ptz_detector = DummyPTZDetector()
# ptz_barrido = DummyPTZBarrido()
# core_logic_module = DummyCoreLogicModule()

# app = AplicacionGUI(intersection_handler, camaras, ptz_detector, ptz_barrido, core_logic_module)
# app.run()
