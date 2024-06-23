import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def pan_tilt_to_vector(pan, tilt):
    """
    Convert pan (azimuth in degrees) and tilt (elevation in degrees from the vertical axis downward) to a direction vector.
    """
    # Convertir grados a radianes
    pan_rad = np.deg2rad(pan)
    tilt_rad = np.deg2rad(tilt)
    
    # Coordenadas cartesianas usando la descripción ajustada de tilt
    x = np.sin(tilt_rad) * np.cos(pan_rad)
    y = np.sin(tilt_rad) * np.sin(pan_rad)
    z = np.cos(tilt_rad)
    
    return np.array([x, y, z])

def punto_mas_cercano(origen_esfera, origen_recta, direccion_recta):
    vector = origen_esfera - origen_recta
    t = np.dot(vector, direccion_recta) / np.dot(direccion_recta, direccion_recta)
    punto_recta = origen_recta + t * direccion_recta
    return punto_recta

def punto_mas_cercano_esfera(origen_esfera, punto, radio):
    vector = punto - origen_esfera
    punto_esfera = origen_esfera + radio * vector / np.linalg.norm(vector)
    return punto_esfera

def intersectar_recta_esfera(origen_esfera, radio, origen_recta, pan, tilt):
    origen_esfera = np.array(origen_esfera)
    origen_recta = np.array(origen_recta)
    direccion_recta = pan_tilt_to_vector(pan, tilt)  #
    direccion_recta = np.array(direccion_recta)
    
    m = origen_recta - origen_esfera
    a = np.dot(direccion_recta, direccion_recta)
    b = 2 * np.dot(m, direccion_recta)
    c = np.dot(m, m) - radio**2
    discriminante = b**2 - 4*a*c
    
    if discriminante < 0:
        punto_recta = punto_mas_cercano(origen_esfera, origen_recta, direccion_recta)
        vector_esfera = punto_recta - origen_esfera
        punto_esfera = origen_esfera + radio * vector_esfera / np.linalg.norm(vector_esfera)
        punto_medio = (punto_recta + punto_esfera) / 2
        return punto_medio, None, None
    else:
        t1 = (-b - np.sqrt(discriminante)) / (2*a)
        t2 = (-b + np.sqrt(discriminante)) / (2*a)
        p1 = origen_recta + t1 * direccion_recta
        p2 = origen_recta + t2 * direccion_recta
        punto_medio = (p1 + p2) / 2
        punto_cercano_esfera = punto_mas_cercano_esfera(origen_esfera, punto_medio, radio)
        punto_medio_final = (punto_medio + punto_cercano_esfera) / 2
        return punto_medio_final, (p1, p2), punto_cercano_esfera
    
def dibujar_esfera_recta(origen_esfera, radio, origen_recta, direccion_recta, punto_medio_final, intersecciones, punto_cercano_esfera):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    u, v = np.mgrid[0:2*np.pi:100j, 0:np.pi:50j]
    x = origen_esfera[0] + radio * np.sin(v) * np.cos(u)
    y = origen_esfera[1] + radio * np.sin(v) * np.sin(u)
    z = origen_esfera[2] + radio * np.cos(v)
    ax.plot_surface(x, y, z, color='b', alpha=0.5, linewidth=0)
    t = np.linspace(-10, 10, 400)
    x_line = origen_recta[0] + t * direccion_recta[0]
    y_line = origen_recta[1] + t * direccion_recta[1]
    z_line = origen_recta[2] + t * direccion_recta[2]
    ax.plot(x_line, y_line, z_line, 'r-', label='Recta')
    ax.scatter(*punto_medio_final, color='yellow', s=100, label='Punto medio final')

    # Dibujar vectores unitarios de los ejes
    ax.quiver(0, 0, 0, 1, 0, 0, color='r', length=3, label='Eje X')
    ax.quiver(0, 0, 0, 0, 1, 0, color='g', length=3, label='Eje Y')
    ax.quiver(0, 0, 0, 0, 0, 1, color='b', length=3, label='Eje Z')

    if intersecciones:
        p1, p2 = intersecciones
        ax.scatter(*p1, color='green', s=100, label='Intersección 1')
        ax.scatter(*p2, color='orange', s=100, label='Intersección 2')
        ax.scatter(*punto_cercano_esfera, color='purple', s=100, label='Punto cercano en esfera')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_xlim([-10, 10])
    ax.set_ylim([-10, 10])  
    ax.set_zlim([-10, 10])
  
    ax.legend()
    plt.show()

# # Ejemplo de uso
# origen_esfera = np.array([0, 0, 0])
# radio = 5
# origen_recta = np.array([0, 0, 0])
# pan=45
# tilt=90
# direccion_recta = pan_tilt_to_vector(pan, tilt)
# punto_medio_final, intersecciones, punto_cercano_esfera = intersectar_recta_esfera(origen_esfera, radio, origen_recta, pan, tilt)
# dibujar_esfera_recta(origen_esfera, radio, origen_recta, direccion_recta, punto_medio_final, intersecciones, punto_cercano_esfera)
