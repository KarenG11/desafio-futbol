from plataforma.reclamos.gestor import GestorReclamos
from plataforma.contratos import EJEMPLO_RECLAMO, EJEMPLO_API_LEVANTAR_REQ

def probar():
    gestor = GestorReclamos()
    
    print("1. Recibiendo reclamo del simulador...")
    # Simulamos que esta IP afectó a 3 órdenes en distintos proveedores
    ordenes_afectadas = [
        "ord-c0a1-P-003-aurora-1",
        "ord-c0a1-P-003-andina-1",
        "ord-c0a1-P-003-cumbre-1"
    ]
    reclamo = gestor.recibir_reclamo(EJEMPLO_RECLAMO, ordenes_afectadas)
    print(f"   Reclamo {reclamo['reclamo_id']} recibido. Estado: {reclamo['estado']}")
    print(f"   Verificación: {reclamo['verificacion']}")
    
    print("\n2. El juez resuelve el reclamo y pide reemplazo...")
    resp = gestor.resolver_reclamo(EJEMPLO_API_LEVANTAR_REQ, minuto_actual=17.5)
    
    print(f"   Estado final: {resp['estado']}")
    print(f"   Órdenes levantadas:")
    for o in resp["ordenes_levantadas"]:
        print(f"     - Proveedor {o['proveedor_id']}: {o['orden_id']}")
    print(f"   Pedido de reemplazo generado: {resp['pedido_reemplazo_id']}")

if __name__ == "__main__":
    probar()