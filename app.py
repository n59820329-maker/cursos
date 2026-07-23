from datetime import datetime
from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt



app = Flask(__name__)
app.secret_key = '123456789'

bcrypt = Bcrypt(app)

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database=''
    )
    return conn

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/login', methods=['POST'])
def login():
    correo = request.form['correo']
    password = request.form['password']
    rol = request.form['rol']
    if rol == 'admin': 
        if correo == 'neison@gmail.com' and password == '3127349142':
            return redirect('/admin')
        
        else:
            return "Credenciales de administrador incorrectas"
        
    elif rol == 'Estudiante':
         conn = get_db_connection()
         cursor = conn.cursor()
         cursor.execute(
             "SELECT * FROM usuarios WHERE correo=%s AND rol=%s",
             (correo, rol)  
         )
         user = cursor.fetchone()
         conn.close()
         if user and bcrypt.check_password_hash(user[3], password):  
             session['idUsuario'] = user[0]
             return redirect('/cursos')
         else:
              return "Credenciales incorrectas"
        

@app.route('/cursos')
def cursos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cursos")
    cursos = cursor.fetchall()
    idUsuario = session.get('idUsuario')
    cursor.close()
    conn.close()
    return render_template('cursos.html', cursos=cursos, idUsuario=idUsuario)


@app.route('/inscribirse', methods=['POST'])
def inscribirse():
    idUsuario = request.form['idUsuario']
    idCurso = request.form['idCurso']
    fecha = datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO inscripciones(idUsuario, idCurso, fecha) VALUES(%s, %s, %s)",
        (idUsuario, idCurso, fecha)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/cursos')

@app.route('/mis_cursos')
def mis_cursos():
    idUsuario = session.get('idUsuario')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cursos.idCurso,
               cursos.titulo,
               cursos.descripcion,
               cursos.categoria,
               cursos.nivel,
               cursos.imagen,
               inscripciones.fecha,
               inscripciones.idInscripcion
        FROM inscripciones
        INNER JOIN cursos
        ON inscripciones.idCurso = cursos.idCurso
        WHERE inscripciones.idUsuario = %s
    """, (idUsuario,))
    mis_cursos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('mis_cursos.html', mis_cursos=mis_cursos)

@app.route('/admin')
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.execute("SELECT * FROM cursos")
    cursos = cursor.fetchall()
    cursor.execute("select*FROM materiales")
    materiales = cursor.fetchall()
    cursor.execute("""
        SELECT inscripciones.idInscripcion,
               usuarios.nombre,
               cursos.titulo,
               inscripciones.fecha
        FROM inscripciones
        INNER JOIN usuarios ON inscripciones.idUsuario = usuarios.idUsuario
        INNER JOIN cursos ON inscripciones.idCurso = cursos.idCurso
        ORDER BY inscripciones.fecha DESC
    """)
    inscripciones = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('admin.html',
        usuarios=usuarios,
        cursos=cursos,
        inscripciones=inscripciones,
        materiales=materiales
    )

@app.route('/materiales/<int:idCurso>')
def materiales(idCurso):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cursos WHERE idCurso=%s", (idCurso,))
    curso = cursor.fetchone()
    cursor.execute("SELECT * FROM materiales WHERE idCurso=%s", (idCurso,))
    materiales = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('materiales.html', curso=curso, materiales=materiales)

@app.route('/addcurso')
def vistaAddCurso():
    return render_template('addcurso.html')

@app.route('/addcurso', methods=['POST'])
def addCurso():
    titulo = request.form['titulo']
    descripcion = request.form['descripcion']
    categoria = request.form['categoria']
    nivel = request.form['nivel']
    imagen = request.form['imagen']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cursos(titulo, descripcion, categoria, nivel, imagen) VALUES(%s, %s, %s, %s, %s)",
        (titulo, descripcion, categoria, nivel, imagen)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin')



@app.route('/addmaterial/<int:idCurso>')
def vistaAddMaterial(idCurso):
    return render_template('addmaterial.html', idCurso=idCurso)
@app.route('/addmaterial/<int:idCurso>', methods=['POST'])
def addMaterial(idCurso):
    titulo = request.form['titulo']
    tipo = request.form['tipo']
    if tipo == 'pdf':
        archivo = request.files['archivo']
        nombre_archivo = secure_filename(archivo.filename)
        archivo.save(os.path.join('static/materiales', nombre_archivo))
        link = nombre_archivo
    else:
        link = request.form['link']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO materiales(idCurso, titulo, tipo, link) VALUES(%s, %s, %s, %s)",
        (idCurso, titulo, tipo, link)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios(
            idUsuario INT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            correo VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL,
            rol VARCHAR(20) NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursos(
            idCurso INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(150) NOT NULL,
            descripcion TEXT NOT NULL,
            categoria VARCHAR(50) NOT NULL,
            nivel VARCHAR(30) NOT NULL,
            imagen VARCHAR(255) NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inscripciones(
            idInscripcion INT AUTO_INCREMENT PRIMARY KEY,
            idUsuario INT NOT NULL,
            idCurso INT NOT NULL,
            fecha DATETIME NOT NULL,
            FOREIGN KEY (idUsuario) REFERENCES usuarios(idUsuario),
            FOREIGN KEY (idCurso) REFERENCES cursos(idCurso)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiales(
            idMaterial INT AUTO_INCREMENT PRIMARY KEY,
            idCurso INT NOT NULL,
            titulo VARCHAR(150) NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            link VARCHAR(255) NOT NULL,
            FOREIGN KEY (idCurso) REFERENCES cursos(idCurso)
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route('/editcurso/<int:id>', methods=['GET', 'POST'])
def editcurso(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        nivel = request.form['nivel']
        imagen = request.form['imagen']
        cursor.execute(
            "UPDATE cursos SET titulo=%s, descripcion=%s, categoria=%s, nivel=%s, imagen=%s WHERE idCurso=%s",
            (titulo, descripcion, categoria, nivel, imagen, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/admin')
    else:
        cursor.execute("SELECT * FROM cursos WHERE idCurso=%s", (id,))
        curso = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template('editcurso.html', curso=curso)

@app.route('/deleteusuario/<int:id>')
def deleteusuario(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE idUsuario=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin')

@app.route('/deletecurso/<int:id>')
def deletecurso(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materiales WHERE idCurso=%s", (id,))
    cursor.execute("DELETE FROM inscripciones WHERE idCurso=%s", (id,))
    cursor.execute("DELETE FROM cursos WHERE idCurso=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin')

@app.route('/deleteinscripcion/<int:id>')
def deleteinscripcion(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inscripciones WHERE idInscripcion=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin')

@app.route('/deletematerial/<int:id>')
def deletematerial(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materiales WHERE idMaterial=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin')

@app.route('/salirdecurso/<int:id>')
def salirdecurso(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inscripciones WHERE idInscripcion=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/mis_cursos') 
    
@app.route('/add', methods=['POST'])
def add_user():
    idUsuario = request.form['idUsuario']
    nombre = request.form['nombre']
    correo = request.form['correo']
    password = request.form['password']
    rol = 'estudiante'
    password_cifrada = bcrypt.generate_password_hash(password).decode('utf-8')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuarios (idUsuario, nombre, correo, password, rol) VALUES (%s, %s, %s, %s, %s)",
        (idUsuario, nombre, correo, password_cifrada, rol)  
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
  app.run(debug=True)
