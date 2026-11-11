from plataforma.evidencia.gestor import GestorEvidencia
from plataforma.contratos import EJEMPLO_CASO, EJEMPLO_DETECCION

def probar():
    gestor = GestorEvidencia(ruta_auditoria="salida/test_auditoria.jsonl")
    
    print("Creando expediente...")
    exp = gestor.crear_expediente(
        caso=EJEMPLO_CASO, 
        deteccion=EJEMPLO_DETECCION, 
        partido_id="practica-01", 
        minuto_actual=2.1
    )
    
    print(f"Expediente creado: {exp['expediente_id']}")
    print(f"Hash del expediente: {exp['hash']}")
    print("Auditoría registrada con éxito.")

if __name__ == "__main__":
    probar()