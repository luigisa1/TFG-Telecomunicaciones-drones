"""
Este script realiza un análisis de datos preliminar sobre un conjunto de datos específico.

Proporciona estadísticas descriptivas, visualizaciones iniciales, y una exploración de los datos faltantes. Está diseñado para ser ejecutado como un paso inicial en el análisis de datos para ayudar en la comprensión general del conjunto de datos.

Uso:
    python script_analisis_preliminar.py <ruta_al_archivo_de_datos>

Dependencias:
    pandas, matplotlib

Autor: Tu Nombre
Fecha: 2024-03-07
"""



#---------------------------------------------- CÓDIGO operaciones.py -------------------------------------------------------------
import numpy as np
import time
import math
import torch

# Campo de visión en grados para diferentes niveles de zoom
campo_vision_maximo_x = 61.0  # Grados (zoom mínimo)
campo_vision_minimo_x = 2.8   # Grados (zoom máximo)
campo_vision_maximo_y = 33.2  # Grados (zoom mínimo)
campo_vision_minimo_y = 1.7   # Grados (zoom máximo)
zoom_max=25
f_min=4.8
f_max=120
sensor_width=5.7
sensor_height=sensor_width*8.1/16

# ---------------- FUNCIÓN DE REAJUSTE DE ZOOM
def reajuste_zoom(area_pantalla,xyxy,zoom_actual):
    # Calcular el área del cuadro de detección
    # Primero desempaquetar los valores de xyxy en las variables individuales x1, y1, x2, y2.
    x1, y1, x2, y2 = xyxy[0]

    # Calcular la longitud y el ancho del recuadro de detección
    long_detec=(x2-x1).item()
    ancho_detec=(y2-y1).item()
    # print("long_detec: ", long_detec)
    # print("ancho detec: ",ancho_detec)

    # Calcular el area de la detección
    area_detec=long_detec*ancho_detec
    # print("El area del cuadro de detección es: ", area_detec)
    # print("El area de pantalla es: ", area_pantalla)

    # Comprobar qué porcentaje ocupa el cuadro de detección respecto a la pantalla de visualización
    porcentaje_detec_pantalla=area_detec/area_pantalla
    # print("Porcentaje detección: ", porcentaje_detec_pantalla)

    # Se inicializa la variable a 0 por si no es necesario variar el zoom
    variacion_zoom=0
    
    # Se decide si hace falta aumentar el zoom o disminuirlo  0.00025  0.01
    if porcentaje_detec_pantalla<=0.00125:
        # Si el valor es tan pequeño, debemos AUMENTAR el zoom
        variacion_zoom=((0.25/25)*(1-0.04))
        # print("Queremos aumentar el zoom: ",aumento_zoom)
        zoom_deseado=zoom_actual+variacion_zoom
        # print("Aumentar zoom a: ", zoom_deseado) 
        if zoom_deseado>1:      # si el zoom deseado es mayor que 1 lo dejamos en 1 (el máximo zoom)
            variacion_zoom=1-zoom_actual
        #print("Zoom que metemos a la funcion: ", variacion_zoom)

    elif porcentaje_detec_pantalla>=0.005:
        # Si el valor es tan grande, debemos DISMINUIR el zoom 
        variacion_zoom=-((0.25/25)*(1-0.04))
        #print("Queremos disminuir el zoom: ",variacion_zoom)
        zoom_deseado=zoom_actual+variacion_zoom
        #print("Disminuir zoom a: ", zoom_deseado)
        if zoom_deseado<0.04:      # si el zoom deseado es menor que 0.04 lo dejamos en 0.04 (el mínimo zoom)
            variacion_zoom=zoom_actual-0.04
        #print("Zoom que metemos a la funcion: ", variacion_zoom)

    return variacion_zoom

# -------------------------------- Cálculo del movimiento de la cámara CON UMBRAL
def movimiento(px,py,zoom_actual,xyxy):
    correccion=False
    # El zoom ya está normalizado con valor máximo 1 cuando zoom=25 y valor 0.04 cuando zoom=1 
    # Convertir el zoom actual para que esté normalizado entre 0 y 1 debido a ese valor mínimo de 0.04 que devuelve la cámara cuando el zoom está al mínimo
    zoom_actual = (zoom_actual - 0.04) / (1 - 0.04)

    # Interpolar el campo de visión en grados para el zoom actual en los ejes X e Y: Depeendiendo del zoom actual de la cámara el campo de visión será uno u otro
    # campo_vision_x = campo_vision_maximo_x-(campo_vision_maximo_x - campo_vision_minimo_x)*zoom_convertido
    # campo_vision_y = campo_vision_maximo_y-(campo_vision_maximo_y - campo_vision_minimo_y)*zoom_convertido
    focal_lenght= f_min + (zoom_actual/1)*(f_max-f_min)
    campo_vision_x=2*np.arctan((sensor_width/(2*focal_lenght)))
    campo_vision_y=2*np.arctan((sensor_height/(2*focal_lenght)))
    # h_g=campo_vision_x*(180/np.pi)
    # v_g=campo_vision_y*(180/np.pi)

    # Calcular longitud de la cuerda en cada eje
    cx=2*np.sin(campo_vision_x/2)
    cy=2*np.sin(campo_vision_y/2)

    # Calcular segmiento CO
    co_x=(cx/2)/np.tan(campo_vision_x/2)
    co_y=(cy/2)/np.tan(campo_vision_y/2)
    
    # CALCULAR PUNTOS MEDIOS DE LA IMÁGEN Y LA DETECCIÓN
    
    # Desempaquetar los valores de xyxy en las variables individuales x1, y1, x2, y2.
    x1, y1, x2, y2 = xyxy[0]  

    # Calcular el punto medio de la detección en las coordenadas x e y. .item() para pasar de formato a torch a un float
    x_detect_mid = ((x1 + x2) / 2).item()
    y_detect_mid = ((y1 + y2) / 2).item()

    # Calcular el punto medio de la pantalla
    x_frame_mid = (px-1) / 2
    y_frame_mid = (py-1) / 2

    # SI la variación en el eje x es menor a 50 píxels y en el eje y es menor a 30 píxels, NO mover la cámara
    if (abs(x_detect_mid-x_frame_mid)<=px/10 and abs(y_detect_mid-y_frame_mid)<=py/15):
        return 0, 0, False

    # Calcular desviación normalizada sobre el tamaño de pantalla (2D)
    desv_x=(x_detect_mid-x_frame_mid)/px
    desv_y=(y_detect_mid-y_frame_mid)/py

    # Calcular desviación np.arctanhen unidades de longitud de la cuerda
    desv_cuerda_x=desv_x*cx
    desv_cuerda_y=desv_y*cy

    # Calcular desviación normalizada en cada eje en radianes
    desv_norm_x_rad=math.atan(desv_cuerda_x/co_x)
    desv_norm_y_rad=-math.atan(desv_cuerda_y/co_y)

    a=abs(desv_norm_x_rad/(campo_vision_x/2))
    b=abs(desv_norm_y_rad/(campo_vision_y/2))
    #print("------------------",a , "-------------------",b)
    if a>0.6 or b>0.6:
        correccion=True

    # Calcular desviación en en cada eje normalizada
    desv_norm_x=desv_norm_x_rad/(2*np.pi)
    desv_norm_y=desv_norm_y_rad/(np.pi)
    
    return desv_norm_x, desv_norm_y, correccion

def calc_fov(zoom_actual, orientacion):
    zoom_actual = (zoom_actual - 0.04) / (1 - 0.04)
    focal_lenght= f_min + (zoom_actual/1)*(f_max-f_min)
    if orientacion==0:
        campo_vision=2*np.arctan((sensor_width/(2*focal_lenght)))
    if orientacion==1:
        campo_vision=2*np.arctan((sensor_height/(2*focal_lenght)))
    return campo_vision

def desviaciones(px,py,max_x,max_y,xyxy):
    # Pasar los valores a radianes
    campo_vision_x_rad=np.radians(max_x)
    campo_vision_y_rad=np.radians(max_y)

    # Calcular longitud de la cuerda en cada eje
    cx=2*np.sin(campo_vision_x_rad/2)
    cy=2*np.sin(campo_vision_y_rad/2)

    # Calcular segmiento CO
    co_x=(cx/2)/np.tan(campo_vision_x_rad/2)
    co_y=(cy/2)/np.tan(campo_vision_y_rad/2)
    
    # CALCULAR PUNTOS MEDIOS DE LA IMÁGEN Y LA DETECCIÓN
    
    # Desempaquetar los valores de xyxy en las variables individuales x1, y1, x2, y2.
    x1, y1, x2, y2 = xyxy[0]  

    # Calcular el punto medio de la detección en las coordenadas x e y. .item() para pasar de formato a torch a un float
    x_detect_mid = ((x1 + x2) / 2).item()
    y_detect_mid = ((y1 + y2) / 2).item()

    # Calcular el punto medio de la pantalla
    x_frame_mid = (px-1) / 2
    y_frame_mid = (py-1) / 2

    # Calcular desviación normalizada sobre el tamaño de pantalla (2D)
    desv_x=(x_detect_mid-x_frame_mid)/px
    desv_y=(y_detect_mid-y_frame_mid)/py

    # Calcular desviación en unidades de longitud de la cuerda
    desv_cuerda_x=desv_x*cx
    desv_cuerda_y=desv_y*cy

    # Calcular desviación normalizada en cada eje en radianes
    desv_norm_x_rad=math.atan(desv_cuerda_x/co_x)
    desv_norm_y_rad=-math.atan(desv_cuerda_y/co_y)
    #Pasamos los valores a grados
    x=desv_norm_x_rad*360/(2*np.pi)
    y=desv_norm_y_rad*360/(2*np.pi)

    desv=(-x,-y)

    return desv

def calcular_iou_tensor(caja1, caja2):
    # Suponiendo que caja1 y caja2 son tensores de la forma [x1, y1, x2, y2]

    # Calcula las coordenadas de la intersección de las dos cajas
    x1_inter = torch.max(caja1[0], caja2[0])
    y1_inter = torch.max(caja1[1], caja2[1])
    x2_inter = torch.min(caja1[2], caja2[2])
    y2_inter = torch.min(caja1[3], caja2[3])

    # Calcula el área de la intersección
    ancho_inter = torch.clamp(x2_inter - x1_inter, min=0)
    alto_inter = torch.clamp(y2_inter - y1_inter, min=0)
    area_interseccion = ancho_inter * alto_inter

    # Calcula el área de la primera caja
    ancho_caja1 = caja1[2] - caja1[0]
    alto_caja1 = caja1[3] - caja1[1]
    area_caja1 = ancho_caja1 * alto_caja1

    # Calcula el área de la segunda caja
    ancho_caja2 = caja2[2] - caja2[0]
    alto_caja2 = caja2[3] - caja2[1]
    area_caja2 = ancho_caja2 * alto_caja2

    # Calcula el área de la unión
    area_union = area_caja1 + area_caja2 - area_interseccion

    # Calcula la IoU
    iou = area_interseccion / area_union if area_union > 0 else 0

    return iou

    