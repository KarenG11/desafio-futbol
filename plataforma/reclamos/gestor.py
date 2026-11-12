"""T06 — Reclamos de sitios afectados por un bloqueo (coordinacion/diseno.md §6, contratos §8).

El feed GET /reclamos no trae orden_id: se correlaciona por proveedor, minuto y objetivo (dominio igual, o IP
cuyo DNS pasivo incluye el dominio). Un reclamo se DESCARTA si el dominio es un objetivo pirata o si no hay
ninguna orden nuestra activa que lo explique. Si procede queda PENDIENTE hasta que el juez decide; recién se
marca LEVANTADO cuando todos los proveedores confirmaron el levantamiento.
"""
from typing import Any, Callable, Dict, List, Optional

from plataforma.contratos import LevantarReclamoResp, Reclamo, ReclamoSim

ACTIVAS = ("recibida", "aplicada")


def _activa_en(orden: dict, minuto: float) -> bool:
    if orden["estado"] in ACTIVAS:
        return True
    fin = orden.get("finalizada_min")
    return orden.get("aplicada_min") is not None and fin is not None and orden["aplicada_min"] <= minuto < fin


class GestorReclamos:
    def __init__(self, ordenes: Dict[str, dict], casos: Callable[[], List[dict]],
                 dominios_de_ip: Callable[[str], List[str]], caso_de_pedido: Callable[[str], Optional[dict]]):
        self.ordenes = ordenes                  # orden_id -> Orden (las del despacho, vivas)
        self.casos = casos
        self.dominios_de_ip = dominios_de_ip
        self.caso_de_pedido = caso_de_pedido
        self.reclamos: Dict[str, Reclamo] = {}

    def _es_pirata(self, dominio: str) -> Optional[dict]:
        dominio = dominio.lower()
        for c in self.casos():
            if c["clasificacion"] == "pirata" and dominio in (c["host"], (c.get("pagina") or "").lower()):
                return c
        return None

    def correlacionar(self, rs: ReclamoSim) -> List[str]:
        dominio = rs["dominio"].lower()
        encontradas = []
        for o in self.ordenes.values():
            if o["proveedor_id"] != rs["proveedor"] or not _activa_en(o, rs["minuto"]):
                continue
            if o["tipo"] == "dominio" and o["objetivo"].lower() == dominio:
                encontradas.append(o["orden_id"])
            elif o["tipo"] == "ip" and dominio in {d.lower() for d in self.dominios_de_ip(o["objetivo"])}:
                encontradas.append(o["orden_id"])
        return encontradas

    def recibir_reclamo(self, rs: ReclamoSim) -> Reclamo:
        if rs["id"] in self.reclamos:
            return self.reclamos[rs["id"]]
        orden_ids = self.correlacionar(rs)
        pirata = self._es_pirata(rs["dominio"])
        caso = self.caso_de_pedido(self.ordenes[orden_ids[0]]["pedido_id"]) if orden_ids else None
        if pirata is not None:
            estado, verif = "descartado", (f"{rs['dominio']} es el objetivo pirata del caso {pirata['caso_id']} "
                                           f"({pirata['motivo_clasificacion']}): el bloqueo es correcto.")
        elif not orden_ids:
            estado, verif = "descartado", (f"No hay ninguna orden nuestra activa en {rs['proveedor']} al minuto "
                                           f"{rs['minuto']} que afecte a {rs['dominio']}.")
        else:
            o = self.ordenes[orden_ids[0]]
            estado = "pendiente"
            verif = (f"{rs['dominio']} no es un objetivo pirata y queda afectado por la orden {o['orden_id']} "
                     f"({o['tipo']} {o['objetivo']}) en {rs['proveedor']}. Procede levantar y, si corresponde, "
                     f"reemplazar por bloqueo de dominio.")
        reclamo: Reclamo = {
            "reclamo_id": rs["id"], "minuto": rs["minuto"], "dominio": rs["dominio"],
            "proveedor_id": rs["proveedor"], "mensaje": rs["mensaje"], "estado": estado,
            "verificacion": verif, "orden_ids": orden_ids,
            "caso_id": (caso or pirata or {}).get("caso_id"), "juez_id": None, "decidido_min": None,
            "ordenes_levantadas": [], "pedido_reemplazo_id": None,
        }
        self.reclamos[rs["id"]] = reclamo
        return reclamo

    def ordenes_a_levantar(self, reclamo: Reclamo) -> List[dict]:
        """Todas las órdenes activas del mismo pedido y objetivo, en TODOS los proveedores."""
        claves = {(self.ordenes[i]["pedido_id"], self.ordenes[i]["tipo"], self.ordenes[i]["objetivo"])
                  for i in reclamo["orden_ids"]}
        return [o for o in self.ordenes.values()
                if (o["pedido_id"], o["tipo"], o["objetivo"]) in claves and o["estado"] in ACTIVAS]

    def resolver_reclamo(self, reclamo_id: str, juez_id: str, reemplazar: bool, minuto: float,
                         levantar: Callable[[str], Optional[str]],
                         crear_reemplazo: Callable[[Reclamo], Optional[str]]) -> LevantarReclamoResp:
        """levantar(orden_id) -> None si el proveedor confirmó, o el error. No inventa confirmaciones."""
        reclamo = self.reclamos.get(reclamo_id)
        if reclamo is None:
            raise ValueError(f"Reclamo {reclamo_id} no encontrado")
        if reclamo["estado"] != "pendiente":
            raise ValueError(f"Reclamo {reclamo_id} ya está {reclamo['estado']}")
        levantadas: List[Dict[str, str]] = []
        errores: List[Dict[str, Any]] = []
        for o in self.ordenes_a_levantar(reclamo):
            error = levantar(o["orden_id"])
            if error is None:
                levantadas.append({"proveedor_id": o["proveedor_id"], "orden_id": o["orden_id"]})
            else:
                errores.append({"proveedor_id": o["proveedor_id"], "orden_id": o["orden_id"], "error": error})
        reclamo["ordenes_levantadas"] = reclamo["ordenes_levantadas"] + levantadas
        if not errores:
            reclamo["estado"] = "levantado"
            reclamo["juez_id"] = juez_id
            reclamo["decidido_min"] = minuto
            if reemplazar:
                reclamo["pedido_reemplazo_id"] = crear_reemplazo(reclamo)
        return {"reclamo_id": reclamo_id, "estado": reclamo["estado"], "ordenes_levantadas": levantadas,
                "errores": errores, "pedido_reemplazo_id": reclamo["pedido_reemplazo_id"]}
