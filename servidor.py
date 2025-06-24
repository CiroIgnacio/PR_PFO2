from flask import Flask, request, jsonify, render_template_string, session
import sqlite3
import hashlib
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  

# Configuración de la base de datos
DATABASE = 'tareas.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Crear tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            contraseña_hash TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla de tareas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            completada BOOLEAN DEFAULT FALSE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente")

def hash_contraseña(contraseña):
    """Hashea una contraseña usando SHA-256 con salt"""
    salt = secrets.token_hex(16)
    contraseña_salted = contraseña + salt
    hash_obj = hashlib.sha256(contraseña_salted.encode())
    hash_hex = hash_obj.hexdigest()
    return salt + hash_hex

def verificar_contraseña(contraseña, hash_almacenado):
    """Verifica si una contraseña coincide con el hash almacenado"""
    salt = hash_almacenado[:32]
    hash_original = hash_almacenado[32:]
    
    contraseña_salted = contraseña + salt
    hash_obj = hashlib.sha256(contraseña_salted.encode())
    hash_nuevo = hash_obj.hexdigest()
    
    return hash_nuevo == hash_original

def requiere_login(f):
    """Decorador para endpoints que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return jsonify({'error': 'Acceso denegado. Debe iniciar sesion.'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    """Página de inicio con información de la API"""
    html_home = '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API Sistema de Gestión de Tareas</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background: #f4f4f4; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .endpoint { background: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { background: #007bff; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; }
            .example { background: #f8f9fa; padding: 10px; border-left: 4px solid #28a745; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>API Sistema de Gestión de Tareas</h1>
            <p>API REST desarrollada con Flask y SQLite para gestión de usuarios y tareas</p>
        </div>

        <h2>📋 Endpoints Disponibles</h2>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /registro</h3>
            <p><strong>Descripción:</strong> Registra un nuevo usuario en el sistema</p>
            <p><strong>Parámetros:</strong></p>
            <div class="example">
                <pre>{
    "usuario": "nombre_usuario",
    "contraseña": "contraseña_segura"
}</pre>
            </div>
        </div>

        <div class="endpoint">
            <h3><span class="method">POST</span> /login</h3>
            <p><strong>Descripción:</strong> Inicia sesión con credenciales de usuario</p>
            <p><strong>Parámetros:</strong></p>
            <div class="example">
                <pre>{
    "usuario": "nombre_usuario",
    "contraseña": "contraseña_segura"
}</pre>
            </div>
        </div>

        <div class="endpoint">
            <h3><span class="method">GET</span> /tareas</h3>
            <p><strong>Descripción:</strong> Muestra página de bienvenida para usuarios autenticados</p>
            <p><strong>Nota:</strong> Requiere haber iniciado sesión previamente</p>
        </div>

        <div class="endpoint">
            <h3><span class="method">POST</span> /logout</h3>
            <p><strong>Descripción:</strong> Cierra la sesión del usuario actual</p>
        </div>

        <h2>🔧 Cómo probar la API</h2>
        <p>Puedes usar herramientas como <strong>Postman</strong>, <strong>curl</strong> o cualquier cliente HTTP para probar los endpoints.</p>
        
        <div class="example">
            <h4>Ejemplo con curl:</h4>
            <pre># Registrar usuario
curl -X POST http://localhost:5000/registro \
  -H "Content-Type: application/json" \
  -d '{"usuario": "testuser", "contraseña": "password123"}'

# Iniciar sesión
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"usuario": "testuser", "contraseña": "password123"}' \
  -c cookies.txt

# Acceder a tareas (usando cookies de sesión)
curl -X GET http://localhost:5000/tareas \
  -b cookies.txt</pre>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_home)

@app.route('/registro', methods=['POST'])
def registro():
    """Endpoint para registrar nuevos usuarios"""
    try:
        data = request.get_json()
        
        if not data or 'usuario' not in data or 'contraseña' not in data:
            return jsonify({'error': 'Faltan campos requeridos: usuario y contraseña'}), 400
        
        usuario = data['usuario'].strip()
        contraseña = data['contraseña']
        
        if len(usuario) < 3:
            return jsonify({'error': 'El nombre de usuario debe tener al menos 3 caracteres'}), 400
        
        if len(contraseña) < 4:
            return jsonify({'error': 'La contraseña debe tener al menos 4 caracteres'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM usuarios WHERE usuario = ?', (usuario,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'El usuario ya existe'}), 409
        
        contraseña_hash = hash_contraseña(contraseña)
        
        cursor.execute(
            'INSERT INTO usuarios (usuario, contraseña_hash) VALUES (?, ?)',
            (usuario, contraseña_hash)
        )
        
        conn.commit()
        usuario_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'mensaje': 'Usuario registrado exitosamente',
            'usuario_id': usuario_id,
            'usuario': usuario
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    """Endpoint para iniciar sesión"""
    try:
        data = request.get_json()
        
        if not data or 'usuario' not in data or 'contraseña' not in data:
            return jsonify({'error': 'Faltan campos requeridos: usuario y contraseña'}), 400
        
        usuario = data['usuario'].strip()
        contraseña = data['contraseña']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, usuario, contraseña_hash FROM usuarios WHERE usuario = ?',
            (usuario,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        usuario_id, usuario_db, contraseña_hash = resultado
        
        if not verificar_contraseña(contraseña, contraseña_hash):
            return jsonify({'error': 'Contraseña incorrecta'}), 401
        
        session['usuario_id'] = usuario_id
        session['usuario'] = usuario_db
        
        return jsonify({
            'mensaje': 'Inicio de sesión exitoso',
            'usuario': usuario_db,
            'usuario_id': usuario_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@app.route('/logout', methods=['POST'])
@requiere_login
def logout():
    """Endpoint para cerrar sesión"""
    usuario = session.get('usuario')
    session.clear()
    return jsonify({'mensaje': f'Sesión cerrada para {usuario}'}), 200

@app.route('/tareas', methods=['GET'])
@requiere_login
def tareas():
    """Endpoint que muestra un HTML de bienvenida para usuarios autenticados"""
    usuario = session.get('usuario')
    usuario_id = session.get('usuario_id')
    
    html_tareas = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bienvenido - Sistema de Tareas</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .welcome-card {{
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: rgba(255, 255, 255, 0.15);
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }}
            .btn {{
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
            }}
            .btn:hover {{ background: #45a049; }}
            .emoji {{ font-size: 2em; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="emoji">🎉</div>
                <h1>¡Bienvenido al Sistema de Gestión de Tareas!</h1>
                <p>Hola <strong>{usuario}</strong>, has iniciado sesión correctamente</p>
            </div>

            <div class="welcome-card">
                <h2>📊 Información de tu cuenta</h2>
                <p><strong>Usuario:</strong> {usuario}</p>
                <p><strong>ID de usuario:</strong> {usuario_id}</p>
                <p><strong>Estado:</strong> ✅ Sesión activa</p>
                <p><strong>Fecha de acceso:</strong> {app.jinja_env.globals['moment']().format('DD/MM/YYYY HH:mm:ss') if 'moment' in app.jinja_env.globals else 'Ahora'}</p>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="emoji">📝</div>
                    <h3>Tareas Pendientes</h3>
                    <p>0</p>
                </div>
                <div class="stat-card">
                    <div class="emoji">✅</div>
                    <h3>Tareas Completadas</h3>
                    <p>0</p>
                </div>
                <div class="stat-card">
                    <div class="emoji">🎯</div>
                    <h3>Proyectos Activos</h3>
                    <p>0</p>
                </div>
            </div>

            <div class="welcome-card">
                <h2>🚀 ¿Qué puedes hacer aquí?</h2>
                <ul>
                    <li>✨ Crear y gestionar tus tareas personales</li>
                    <li>📅 Organizar tareas por fechas y prioridades</li>
                    <li>🏷️ Categorizar tareas por proyectos</li>
                    <li>📈 Seguir tu progreso y productividad</li>
                    <li>🔄 Sincronizar tus datos en tiempo real</li>
                </ul>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <p>🔒 Tu información está segura y protegida</p>
                <p>Sistema desarrollado con Flask y SQLite</p>
                
                <div style="margin-top: 20px;">
                    <a href="/" class="btn">🏠 Inicio</a>
                    <button onclick="logout()" class="btn" style="background: #f44336;">🚪 Cerrar Sesión</button>
                </div>
            </div>
        </div>

        <script>
            function logout() {{
                fetch('/logout', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }})
                .then(response => response.json())
                .then(data => {{
                    alert(data.mensaje || 'Sesión cerrada');
                    window.location.href = '/';
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    alert('Error al cerrar sesión');
                }});
            }}
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(html_tareas)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    init_db()
    
    print("🚀 Iniciando servidor Flask...")
    print("📊 Base de datos SQLite configurada")
    print("🔒 Sistema de autenticación activado")
    print("🌐 Servidor disponible en: http://localhost:5000")
    print("📖 Documentación de API disponible en: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)