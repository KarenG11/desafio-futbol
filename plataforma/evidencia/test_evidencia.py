import os
import json
from plataforma.evidencia.gestor import GestorEvidencia
from plataforma.contratos import EJEMPLO_CASO, EJEMPLO_DETECCION

def probar():
    ruta_test = "salida/test_auditoria.jsonl"
    
    # Borramos el archivo si existe para arrancar limpio
    if os.path.exists(ruta_test):
        os.remove(ruta_test)

    gestor = GestorEvidencia(ruta_auditoria=ruta_test)
    
    print("1. Creando expediente...")
    exp = gestor.crear_expediente(
        caso=EJEMPLO_CASO, 
        deteccion=EJEMPLO_DETECCION, 
        partido_id="practica-01", 
        minuto_actual=2.1
    )
    
    print(f"   Expediente creado: {exp['expediente_id']}")
    print(f"   Hash del expediente: {exp['hash']}")
    
    print("\n2. Verificando Integridad Original...")
    gestor.verificar_integridad()
    
    # --- PRUEBA DE ALTERACIÓN ---
    print("\n3. Simulando un ataque (alterando el archivo)...")
    with open(ruta_test, "r", encoding="utf-8") as f:
        lineas = f.readlines()
    
    # Alteramos el JSON de la primera línea (cambiamos el actor a "hacker")
    evento = json.loads(lineas[0])
    evento["actor"] = "hacker_infiltrado" 
    lineas[0] = json.dumps(evento) + "\n"
    
    with open(ruta_test, "w", encoding="utf-8") as f:
        f.writelines(lineas)
        
    print("   Archivo alterado. El actor original ahora dice 'hacker_infiltrado'.")
    
    print("\n4. Verificando Integridad Después del Ataque...")
    gestor.verificar_integridad()

if __name__ == "__main__":
    probar()