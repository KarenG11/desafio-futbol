import json
import os
from typing import List
from plataforma.contratos import Pedido, Expediente, Orden, EntradaPublica

class RegistroPublico:
    def __init__(self, ruta_salida: str = "salida/registro_publico.json"):
        self.ruta_salida = ruta_salida
        self.entradas = []

    def generar_entrada(self, pedido: Pedido, expediente: Expediente, ordenes: List[Orden], juez_nombre: str, juzgado_nombre: str) -> EntradaPublica:
        """Transforma datos internos en una entrada pública y transparente."""
        
        # Tomamos la primera orden para sacar los datos generales (tipo, objetivo)
        primera_orden = ordenes[0]
        
        # Armamos el estado de los proveedores
        provs = []
        for o in ordenes:
            provs.append({
                "proveedor_id": o["proveedor_id"],
                "estado": o["estado"],
                "aplicada_min": o["aplicada_min"],
                "finalizada_min": o["finalizada_min"]
            })

        entrada: EntradaPublica = {
            "entrada_id": f"{pedido['pedido_id']}/{primera_orden['tipo']}/{primera_orden['objetivo']}",
            "pedido_id": pedido["pedido_id"],
            "expediente_id": expediente["expediente_id"],
            "partido_id": expediente["partido_id"],
            "tipo": primera_orden["tipo"],
            "objetivo": primera_orden["objetivo"],
            "motivo": expediente["caso"]["motivo_clasificacion"],
            "juez_id": pedido["juez_id"] or "desconocido",
            "juez_nombre": juez_nombre,
            "juzgado_id": pedido["juzgado_id"] or "desconocido",
            "juzgado_nombre": juzgado_nombre,
            "ordenado_min": pedido["decidido_min"] or 0.0,
            "vence_min": pedido["vence_min"],
            "estado": "en_curso", # Se actualizaría según la orden real
            "finalizado_min": None,
            "motivo_fin": None,
            "proveedores": provs
        }
        
        return entrada

    def publicar(self, entrada: EntradaPublica):
        """Guarda la entrada en el registro público."""
        self.entradas.append(entrada)
        self._guardar_en_disco()

    def _guardar_en_disco(self):
        os.makedirs(os.path.dirname(self.ruta_salida), exist_ok=True)
        with open(self.ruta_salida, "w", encoding="utf-8") as f:
            json.dump({"entradas": self.entradas}, f, indent=2, ensure_ascii=False)