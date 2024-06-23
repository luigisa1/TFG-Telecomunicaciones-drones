import sqlite3

def iniciarBD():
    con = sqlite3.connect('instance/alarmas.db')
    cursor = con.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS alarmas (id INTEGER PRIMARY KEY, receptor TEXT, prefijo TEXT, cuenta TEXT, protocolo TEXT, fecha TEXT, hora TEXT, video TEXT, x REAL, y REAL, z REAL)")
    con.commit()
    con.close()


def guardarAlarma(receptor, prefijo, cuenta, protocolo, fecha, video, x, y, z):

    print(f'Al entrar a guardar alarma, x: {x}, y: {y}, z: {z}')

    #Aquí adaptamos los datos recibidos al formato de la base de datos
    receptor, prefijo, cuenta, protocolo, fecha, hora, video, x, y, z = adaptarDatos(receptor, prefijo, cuenta, protocolo, fecha, video, x, y, z)

    con = sqlite3.connect('instance/alarmas.db')
    cursor = con.cursor()
    cursor.execute("INSERT INTO alarmas (receptor, prefijo, cuenta, protocolo, fecha, hora, video, x, y, z) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (receptor, prefijo, cuenta, protocolo, fecha, hora, video, x, y, z))
    con.commit()
    con.close()
    



def adaptarDatos(receptor, prefijo, cuenta, protocolo, fecha, video, x, y, z):
    import datetime

    print(f'Al adaptar los datos x: {x}, y: {y}, z: {z}')

    if x == None:
        x = 0
    if y == None:
        y = 0
    if z == None:
        z = 0
    if video == None:
        video = ""

    receptor = str(receptor)
    prefijo = str(prefijo)
    cuenta = str(cuenta)
    protocolo = str(protocolo)
    video = str(video)
    x = float(x)
    y = float(y)
    z = float(z)   

    fecha = float(fecha)

    prefecha = datetime.datetime.utcfromtimestamp(fecha)

    hora = prefecha.strftime("%H:%M:%S")
    fecha = prefecha.strftime("%Y-%m-%d")

    return receptor, prefijo, cuenta, protocolo, fecha, hora, video, x, y, z
