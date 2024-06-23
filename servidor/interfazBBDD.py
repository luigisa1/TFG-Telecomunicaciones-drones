from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarmas.db'
app.config['SECRET_KEY'] = 'clave_secreta'
db = SQLAlchemy(app)

#Modelos, se difieren entre usuarios y alarmas
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    rol = db.Column(db.String(50), nullable=False)

class Alarmas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receptor = db.Column(db.String(50), nullable=False)
    prefijo = db.Column(db.String(50), nullable=False)
    cuenta = db.Column(db.String(50), db.ForeignKey('usuario.nombre'), nullable=False)
    protocolo = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.String(50), nullable=False)
    hora = db.Column(db.String(50), nullable=False)
    video = db.Column(db.String(50), nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    z = db.Column(db.Float, nullable=False)

#Rutas


@app.route('/')
def index():
    if 'nombre' in session:
        print(f"Usuario {session['nombre']} está en sesión.")  # Debug
        usuario = Usuario.query.filter_by(nombre=session['nombre']).first()
        if usuario:
            if usuario.rol == 'admin':
                alarmas = Alarmas.query.order_by(desc(Alarmas.fecha), desc(Alarmas.hora)).all()
            else:
                alarmas = Alarmas.query.filter_by(cuenta=usuario.nombre).order_by(desc(Alarmas.fecha), desc(Alarmas.hora)).all()
            return render_template('dashboard.html', alarmas=alarmas)
        else:
            print("Usuario no encontrado en la base de datos.")  # Debug
    else:
        print("No hay usuario en sesión.")  # Debug
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']
        usuario = Usuario.query.filter_by(nombre=nombre).first()
        if usuario and check_password_hash(usuario.password, password):
            session['nombre'] = nombre
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error = "Usuario o contraseña incorrectos")
    return render_template('login.html', error = "Otro tipo de error")
        

@app.route('/registro', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']
        rol = request.form['rol']

        # Usar el método predeterminado para hash de contraseñas
        hashed_password = generate_password_hash(password)

        # Verificar si el usuario ya existe
        existing_user = Usuario.query.filter_by(nombre=nombre).first()
        if existing_user is not None:
            return render_template('registro.html', error="El nombre de usuario ya existe")

        # Crear y guardar el nuevo usuario
        new_user = Usuario(nombre=nombre, password=hashed_password, rol=rol)
        db.session.add(new_user)
        db.session.commit()

        # Redireccionar al login o donde prefieras después del registro
        return render_template('login.html')
    return render_template('registro.html')



@app.route('/logout')
def logout():
    session.pop('nombre', None)  # Elimina el nombre de la sesión
    # Redirige al usuario a la página de login
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)
