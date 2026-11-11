from plataforma.transparencia.registro import RegistroPublico
from plataforma.contratos import EJEMPLO_PEDIDO, EJEMPLO_EXPEDIENTE, EJEMPLO_ORDEN

def probar():
    registro = RegistroPublico(ruta_salida="salida/registro_publico.json")
    
    # Usamos los mocks de Alejo
    entrada = registro.generar_entrada(
        pedido=EJEMPLO_PEDIDO,
        expediente=EJEMPLO_EXPEDIENTE,
        ordenes=[EJEMPLO_ORDEN],
        juez_nombre="Dra. Laura Ficticia",
        juzgado_nombre="Juzgado de Garantías N.º 3"
    )
    
    registro.publicar(entrada)
    print("✅ Entrada publicada con éxito.")
    print(f"   Bloqueo: {entrada['tipo'].upper()} a {entrada['objetivo']}")
    print(f"   Juez: {entrada['juez_nombre']}")

if __name__ == "__main__":
    probar()