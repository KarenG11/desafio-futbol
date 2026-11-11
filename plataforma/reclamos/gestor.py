from typing import Dict, List, Any
from plataforma.contratos import ReclamoSim, Reclamo, LevantarReclamoReq, LevantarReclamoResp

class GestorReclamos:
    def __init__(self):
        self.reclamos: Dict[str, Reclamo] = {}

    def recibir_reclamo(self, reclamo_sim: ReclamoSim, ordenes_afectadas: List[str]) -> Reclamo:
        """Procesa un reclamo entrante del simulador y lo convierte en gestión interna."""
        
        # Simulamos la verificación técnica (en un caso real, consultaríamos el DNS y el cerebro)
        verificacion = (
            f"{reclamo_sim['dominio']} no es un sitio pirata y comparte la IP con un sitio bloqueado. "
            f"Órdenes afectadas en {reclamo_sim['proveedor']}: {', '.join(ordenes_afectadas)}"
        )

        reclamo: Reclamo = {
            "reclamo_id": reclamo_sim["id"],
            "minuto": reclamo_sim["minuto"],
            "dominio": reclamo_sim["dominio"],
            "proveedor_id": reclamo_sim["proveedor"],
            "mensaje": reclamo_sim["mensaje"],
            "estado": "pendiente",
            "verificacion": verificacion,
            "orden_ids": ordenes_afectadas,
            "caso_id": "C-003", # En base al ejemplo de Alejo
            "juez_id": None,
            "decidido_min": None,
            "ordenes_levantadas": [],
            "pedido_reemplazo_id": None,
        }

        self.reclamos[reclamo["reclamo_id"]] = reclamo
        return reclamo

    def resolver_reclamo(self, req: LevantarReclamoReq, minuto_actual: float) -> LevantarReclamoResp:
        """El juez decide levantar la orden por un bloqueo erróneo."""
        
        reclamo_id = req["reclamo_id"]
        if reclamo_id not in self.reclamos:
            raise ValueError(f"Reclamo {reclamo_id} no encontrado")
            
        reclamo = self.reclamos[reclamo_id]
        
        # 1. Cambiamos el estado del reclamo
        reclamo["estado"] = "levantado"
        reclamo["juez_id"] = req["juez_id"]
        reclamo["decidido_min"] = minuto_actual
        
        # 2. Simulamos el levantamiento en todos los proveedores afectados
        ordenes_levantadas = []
        for orden_id in reclamo["orden_ids"]:
            # Extraemos el proveedor del ID de la orden (ej: ord-c0a1-P-003-andina-1 -> andina)
            partes = orden_id.split("-")
            proveedor_id = partes[-2] if len(partes) > 2 else "desconocido"
            
            ordenes_levantadas.append({
                "proveedor_id": proveedor_id,
                "orden_id": orden_id
            })
            
        reclamo["ordenes_levantadas"] = ordenes_levantadas
        
        # 3. Si se pide reemplazo, generamos un nuevo pedido
        pedido_reemplazo = None
        if req["reemplazar"]:
            pedido_reemplazo = f"P-REEMPLAZO-{reclamo_id}"
            reclamo["pedido_reemplazo_id"] = pedido_reemplazo

        # 4. Devolvemos la respuesta como dicta el contrato
        respuesta: LevantarReclamoResp = {
            "reclamo_id": reclamo_id,
            "estado": "levantado",
            "ordenes_levantadas": ordenes_levantadas,
            "errores": [],
            "pedido_reemplazo_id": pedido_reemplazo
        }
        
        return respuesta