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

import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import minimize

def calcular_direccion_relativa(pos_camara, pos_dron):
    x ,y ,z = pos_dron[0] - pos_camara[0], pos_dron[1] - pos_camara[1], pos_dron[2] - pos_camara[2]
    longitud=np.sqrt(x**2+y**2+z**2)
    x, y, z = x/longitud, y/longitud, z/longitud
    pan_radians = - np.arctan2(y,x)
    tilt_radians = np.arcsin(z)
    pan_grados = pan_radians*180/np.pi
    titlt_grados = tilt_radians*180/np.pi
    pan_normalized = pan_radians/np.pi
    tilt_normalized = tilt_radians/(np.pi/2)
    return (pan_normalized, tilt_normalized), (pan_grados, titlt_grados)
################################################################################################################################
#A partir de la dirección relativa calcular  el pan y tilt al que debe moverse la cámara PTZ
def calcular_pan_tilt(direccion):
    dx, dy, dz = direccion

    # Ángulo de pan (en el plano horizontal)
    pan = math.atan2(dy, dx)

    # Distancia horizontal desde la cámara al dron
    distancia_horizontal = math.sqrt(dx**2 + dy**2)

    # Ángulo de tilt (en el plano vertical)
    tilt = math.atan2(dz, distancia_horizontal)

    return math.degrees(pan), math.degrees(tilt)

def encontrar_interseccion_minimos_cuadrados(positions, vectors):
    # Verifica si las entradas son válidas
    if len(positions) != len(vectors):
        raise ValueError("Las listas de posiciones y vectores deben tener la misma longitud")
    
    results = []
    tolerance=1e-6
    for i in range(len(positions)):
        P = np.array(positions[i])
        V = np.array(vectors[i])

        for j in range(i + 1, len(positions)):
            Q = np.array(positions[j])
            U = np.array(vectors[j])

            # Calcula el producto cruzado de los vectores directores
            cross_product = np.cross(V, U)

            # Verifica si las rectas son casi paralelas
            if np.linalg.norm(cross_product) < tolerance:
                # Las rectas están casi paralelas, encuentra el punto más cercano
                closest_point = P + np.dot(Q - P, V) / np.dot(V, V) * V
                results.append(closest_point)
                p_inter=np.mean(results, axis=0)
                return p_inter
            else:
                # Calcula los parámetros t y s
                t = np.dot(np.cross(Q - P, U), np.cross(V, U)) / np.dot(np.cross(V, U), np.cross(V, U))
                s = np.dot(np.cross(Q - P, V), np.cross(V, U)) / np.dot(np.cross(V, U), np.cross(V, U))

                # Calcula el punto de intersección
                intersection_point = P + t * V
                results.append(intersection_point)
                p_inter=np.mean(results, axis=0)
                return p_inter


def distancia_cuadrada_a_recta(punto, origen, direccion):
    """
    Calcula la distancia cuadrada desde un punto en el espacio 3D hasta una recta definida por un punto de origen y un vector de dirección.
    """
    punto = np.array(punto)
    origen = np.array(origen)
    direccion = np.array(direccion)
    v = punto - origen
    distancia_cuadrada = np.linalg.norm(v - np.dot(v, direccion) * direccion)**2
    return distancia_cuadrada

def funcion_objetivo(punto, origenes, direcciones):
    """
    La función objetivo que queremos minimizar: la suma de las distancias cuadradas desde el punto hasta cada una de las rectas.
    """
    suma_distancias = sum(distancia_cuadrada_a_recta(punto, origenes[i], direcciones[i]) for i in range(len(origenes)))
    return suma_distancias

def encontrar_interseccion_minimos_cuadrados_2(origenes, direcciones):
    """
    Encuentra el punto que minimiza la suma de las distancias cuadradas a un conjunto de rectas en el espacio 3D.
    """
    punto_inicial = np.mean(origenes, axis=0)  # Un punto inicial para la optimización podría ser el promedio de los puntos de origen.
    resultado = minimize(funcion_objetivo, punto_inicial, args=(origenes, direcciones), method='SLSQP')
    return resultado.x



def actualizar_animacion(ax, posiciones, vectores, p_dron):
    ax.clear()  # Limpia el gráfico para el nuevo cuadro

    # Configurar colores para todas las cámaras excepto la PTZ
    colores = ['black'] * (len(posiciones) - 1) + ['magenta']  # PTZ será magenta

    # Dibujar vectores de dirección para todas las cámaras
    for i, (pos, vector, color) in enumerate(zip(posiciones, vectores, colores), start=1):
        # No escalar el vector de la cámara PTZ
        vector_escalado = vector if i == len(posiciones) else [30 * v for v in vector]

        # Dibujar el vector desde la posición de la cámara
        ax.quiver(pos[0], pos[1], pos[2], vector_escalado[0], vector_escalado[1], vector_escalado[2], color=color, arrow_length_ratio=0.1)
        ax.scatter(*pos, color='black', s=20)  # Marca la posición de la cámara
        ax.text(*pos, f'Cámara {i}' if i < len(posiciones) else 'Cámara PTZ', color='black')

    # Dibujar los ejes X, Y, Z
    ax.quiver(0, 0, 0, 10, 0, 0, color='red', arrow_length_ratio=0.2)   # Eje X
    ax.quiver(0, 0, 0, 0, 10, 0, color='green', arrow_length_ratio=0.2) # Eje Y
    ax.quiver(0, 0, 0, 0, 0, 10, color='blue', arrow_length_ratio=0.2)  # Eje Z

    # Marcar el punto de intersección
    ax.scatter(*p_dron, color='magenta', s=100)
    ax.text(*p_dron, "Dron", color='magenta')

    # Establecer los límites de los ejes
    ax.set_xlim([-30, 30])
    ax.set_ylim([-30, 30])
    ax.set_zlim([0, 30])
    ax.set_xlabel('Eje X')
    ax.set_ylabel('Eje Y')
    ax.set_zlabel('Eje Z')
    plt.show()

def dibujar_vectores_camara(ax, posiciones, vectores, p_dron):
    # Configurar colores para todas las cámaras excepto la PTZ
    colores = ['black'] * (len(posiciones) - 1) + ['magenta'] # PTZ será magenta

    # Dibujar vectores de dirección para todas las cámaras
    for i, (pos, vector, color) in enumerate(zip(posiciones, vectores, colores), start=1):
        # No escalar el vector de la cámara PTZ
        if i == len(posiciones):  # Si es la cámara PTZ
            vector_escalado = vector  # No escalar el vector
        else:
            vector_escalado = [20 * v for v in vector]  # Escalar el vector x20
            #vector_escalado = vector
        
        # Dibujar el vector desde la posición de la cámara
        ax.quiver(pos[0], pos[1], pos[2], vector_escalado[0], vector_escalado[1], vector_escalado[2],color=color, arrow_length_ratio=0.1, label=f'Cámara {i}' if i < len(posiciones) else 'Cámara PTZ')
        ax.scatter(*pos, color='black', s=20)  # Marca la posición de la cámara
        
        if i == len(posiciones):
            ax.text(*pos, f'Cámara PTZ', color='black')  # Etiqueta para la posición de la cámara PTZ
        else:
            ax.text(*pos, f'Cámara {i}', color='black')  # Etiqueta para la posición de la cámara
        
    # Dibujar los ejes X, Y, Z
    ax.quiver(0, 0, 0, 10, 0, 0, color='red', arrow_length_ratio=0.2)   # Eje X
    ax.quiver(0, 0, 0, 0, 10, 0, color='green', arrow_length_ratio=0.2) # Eje Y
    ax.quiver(0, 0, 0, 0, 0, 10, color='blue', arrow_length_ratio=0.2)  # Eje Z
    
    # Marcar el punto de intersección
    ax.scatter(*p_dron, color='magenta', s=100)  # Marca el punto con un color específico y un tamaño s
    ax.text(*p_dron, "Dron", color='magenta')  # Añade una etiqueta al punto

    # Establecer los límites de los ejes
    ax.set_xlim([-10, 10])
    ax.set_ylim([-10, 10])
    ax.set_zlim([0, 20])

    # Etiquetas y leyendaposiciones[:-1], direcciones[:-1]
    ax.set_xlabel('Eje X')
    ax.set_ylabel('Eje Y')
    ax.set_zlabel('Eje Z')
    ax.legend()

    plt.show()

def calcular_vector_normalizado(camara_orient,desv):
    """
    Calcula y normaliza el vector de dirección de la cámara.
    
    :param camara_orient: Orientación de la cámara (pan, tilt) en grados.
    :return: Vector de dirección normalizado (dx, dy, dz).
    """
    # Convertir la orientación de la cámara a radianes
    pan_rad = math.radians(camara_orient[0] + desv[0])
    tilt_rad = math.radians(camara_orient[1] + desv[1])


    # Calcular componentes del vector en base a la orientación
    dx = math.sin(tilt_rad) * math.cos(pan_rad)
    dy = math.sin(tilt_rad) * math.sin(pan_rad)
    dz = math.cos(tilt_rad)
    
    return (dx , dy, dz )


def calcular_vector_direccion(camara_orient, desv_x, desv_y):
    """
    :param camara_orient: Orientación de la cámara (pan, tilt) en grados.
    :param desv_x: Desviación normalizada en el eje X.
    :param desv_y: Desviación normalizada en el eje Y.
    :return: Vector de dirección (dx, dy, dz).
    """

    # Convertir la orientación de la cámara a radianes
    pan_rad = math.radians(camara_orient[0])
    tilt_rad = math.radians(camara_orient[1])

    # Convertir desviaciones a radianes
    desv_x_rad = desv_x * 2 * math.pi
    desv_y_rad = desv_y * 2 * math.pi

    # Calcular componentes del vector en base a la orientación y desviaciones
    dx = math.cos(tilt_rad) * math.sin(pan_rad + desv_x_rad)
    dy = math.cos(tilt_rad) * math.cos(pan_rad + desv_x_rad)
    dz = math.sin(tilt_rad + desv_y_rad)

    # Crear el vector de dirección
    direccion = (dx, dy, dz)

    return direccion
###############################################################################################################################

def intersecion_dir_PTZ(posiciones, orientaciones, desviaciones):
    #Calcular los vectores normalizados de dirección de cada cámara:
    # print("posiciones: ", posiciones, "Direciones", orientaciones, "Desviaciones", desviaciones)
    direcciones = []
    for i, (ori , desv) in enumerate(zip(orientaciones, desviaciones), start=1):
        direccion=calcular_vector_normalizado(ori,desv)
        direcciones.append(direccion)
    #Una vez tenemos las direciones el siguiente paso es encontrar el punto de intersección
    print("posiciones: ", posiciones[:-1],"direcciones: ", direcciones[:-1])
    punto_dron = encontrar_interseccion_minimos_cuadrados_2(posiciones[:-1], direcciones)
    # print("posiciones: ", posiciones, "Direciones", direcciones)
    print(punto_dron)
    direccionPTZ, dir_grados = calcular_direccion_relativa(posiciones[-1], punto_dron)
    direcciones.append(direccionPTZ)
    print("Calculooos", punto_dron, direccionPTZ)
    return punto_dron, direccionPTZ, dir_grados, direcciones
