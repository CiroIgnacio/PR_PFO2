import requests
import json
import time
import sys

# Configuración
BASE_URL = "http://localhost:5000"
session = requests.Session()

def print_separator():
    print("\n" + "="*60 + "\n")

def print_test_header(test_name):
    print(f"🧪 PRUEBA: {test_name}")
    print("-" * 40)

def print_response(response, show_headers=False):
    print(f"Status Code: {response.status_code}")
    if show_headers:
        print(f"Headers: {dict(response.headers)}")
    
    try:
        json_data = response.json()
        print("Response JSON:")
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
    except:
        print("Response Text:")
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)

def test_home_page():
    """Prueba la página principal"""
    print_test_header("Página Principal (GET /)")
    
    try:
        response = session.get(f"{BASE_URL}/")
        print_response(response)
        
        if response.status_code == 200:
            print("ÉXITO: Página principal cargada correctamente")
        else:
            print(" ERROR: No se pudo cargar la página principal")
            
    except Exception as e:
        print(f" ERROR: DE CONEXIÓN: {e}")
        return False
    
    return True

def test_user_registration():
    """Prueba el registro de usuarios"""
    print_test_header("Registro de Usuario (POST /registro)")
    
    # Datos de prueba
    test_users = [
        {"usuario": "testuser1", "contraseña": "password123"},
        {"usuario": "admin", "contraseña": "admin123"},
        {"usuario": "user", "contraseña": "1234"}
    ]
    passed = True

    for user_data in test_users:
        print(f"\n📝 Registrando usuario: {user_data['usuario']}")
        
        response = session.post(
            f"{BASE_URL}/registro",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        print_response(response)
        
        if response.status_code == 201:
            print(f"ÉXITO: Usuario {user_data['usuario']} registrado")
        elif response.status_code == 409:
            print(f"ADVERTENCIA: Usuario {user_data['usuario']} ya existe")
        else:
            print(f" ERROR: No se pudo registrar {user_data['usuario']}")
            passed = False
    
    return passed

def test_user_login():
    """Prueba el inicio de sesión"""
    print_test_header("Inicio de Sesión (POST /login)")
    
    # Login exitoso
    login_data = {"usuario": "testuser1", "contraseña": "password123"}
    print(f"🔑 Iniciando sesión con: {login_data['usuario']}")
    
    response = session.post(
        f"{BASE_URL}/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print_response(response)
    
    if response.status_code == 200:
        print("ÉXITO: Inicio de sesión correcto")
        return True
    else:
        print(" ERROR: No se pudo iniciar sesión")
        return False

def test_login_failures():
    """Prueba casos de falla en login"""
    print_test_header("Pruebas de Falla en Login")
    
    passed = True
    print("🔑 Probando usuario inexistente")
    response = session.post(
        f"{BASE_URL}/login",
        json={"usuario": "noexiste", "contraseña": "password"},
        headers={"Content-Type": "application/json"}
    )
    print_response(response)
    
    if response.status_code == 404:
        print("ÉXITO: Manejo correcto de usuario inexistente")
    else:
        passed = False
    
    # Contraseña incorrecta
    print("\n🔑 Probando contraseña incorrecta")
    response = session.post(
        f"{BASE_URL}/login",
        json={"usuario": "testuser1", "contraseña": "wrongpassword"},
        headers={"Content-Type": "application/json"}
    )
    print_response(response)
    
    if response.status_code == 401:
        print("ÉXITO: Manejo correcto de contraseña incorrecta")
    else:
        passed = False
    
    return passed

def test_protected_routes():
    """Prueba rutas protegidas"""
    print_test_header("Acceso a Tareas (GET /tareas)")
    
    response = session.get(f"{BASE_URL}/tareas")
    print_response(response)
    
    if response.status_code == 200:
        print("ÉXITO: Acceso a tareas autorizado")
        return True
    else:
        print("ERROR: No se pudo acceder a tareas")
        return False

def test_logout():
    """Prueba el cierre de sesión"""
    print_test_header("Cierre de Sesión (POST /logout)")
    
    response = session.post(
        f"{BASE_URL}/logout",
        headers={"Content-Type": "application/json"}
    )
    
    print_response(response)
    
    if response.status_code == 200:
        print("ÉXITO: Sesión cerrada correctamente")
        return True
    else:
        print(" ERROR: No se pudo cerrar sesión")
        return False

def test_unauthorized_access():
    """Prueba acceso sin autorización después del logout"""
    print_test_header("Acceso No Autorizado (después de logout)")
    
    response = session.get(f"{BASE_URL}/tareas")
    print_response(response)
    
    if response.status_code == 401:
        print("ÉXITO: Acceso denegado correctamente")
        return True
    else:
        print("ERROR: Sistema permitió acceso no autorizado")
        return False

def main():
    """Función principal que ejecuta todas las pruebas"""
    print(f"Servidor: {BASE_URL}")
    
    tests = [
        ("Conectividad", test_home_page),
        ("Registro", test_user_registration),
        ("Login Exitoso", test_user_login),
        ("Fallas de Login", test_login_failures),
        ("Rutas Protegidas", test_protected_routes),
        ("Logout", test_logout),
        ("Acceso No Autorizado", test_unauthorized_access)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print_separator()
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f" ERROR: INESPERADO en {test_name}: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  
    
    # Resumen final
    print_separator()
    print("📊 RESUMEN DE PRUEBAS")
    print("-" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASÓ" if result else "FALLÓ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado final: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("¡TODAS LAS PRUEBAS PASARON! La API funciona correctamente.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa la implementación.")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n ERROR: fatal: {e}")
        sys.exit(1)