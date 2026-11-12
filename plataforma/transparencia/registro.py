"""T07 — Registro público: una entrada por (pedido, tipo, objetivo) con el estado REAL de cada proveedor."""
import json
import os
from typing import Dict, List, Optional

from plataforma.contratos import EntradaPublica, Expediente, Orden, Pedido


def _ultima_por_proveedor(ordenes: List[Orden]) -> List[Orden]:
    ultimas: Dict[str, Orden] = {}
    for o in ordenes:
        actual = ultimas.get(o["proveedor_id"])
        if actual is None or o["intentos"] > actual["intentos"]:
            ultimas[o["proveedor_id"]] = o
    return [ultimas[p] for p in sorted(ultimas)]


def estado_publico(ordenes: List[Orden]):
    """(estado, finalizado_min, motivo_fin) a partir de la última orden de cada proveedor."""
    estados = {o["estado"] for o in ordenes}
    if "aplicada" in estados:
        return "vigente", None, None
    if "recibida" in estados or not estados or estados <= {"fallida", "rechazada"}:
        return "en_curso", None, None
    finales = [o for o in ordenes if o["estado"] in ("levantada", "vencida")]
    fin = max((o.get("finalizada_min") or 0.0) for o in finales) if finales else None
    if any(o["estado"] == "levantada" for o in ordenes):
        motivo = next(o.get("motivo") for o in ordenes if o["estado"] == "levantada")
        return "levantado", fin, motivo
    return "vencido", fin, "vencimiento de la orden"


def armar_entradas(pedidos: List[Pedido], expedientes: Dict[str, Expediente], ordenes: List[Orden],
                   nombres: Dict[str, str]) -> List[EntradaPublica]:
    """nombres: juez_id/juzgado_id -> nombre público. Solo pedidos aprobados con al menos una orden."""
    entradas: List[EntradaPublica] = []
    for p in sorted(pedidos, key=lambda x: x["pedido_id"]):
        if p.get("estado") != "aprobado" or p["expediente_id"] not in expedientes:
            continue
        exp = expedientes[p["expediente_id"]]
        grupos: Dict[tuple, List[Orden]] = {}
        for o in ordenes:
            if o["pedido_id"] == p["pedido_id"] and o["estado"] != "enviando":
                grupos.setdefault((o["tipo"], o["objetivo"]), []).append(o)
        for (tipo, objetivo), grupo in sorted(grupos.items()):
            ultimas = _ultima_por_proveedor(grupo)
            estado, fin, motivo_fin = estado_publico(ultimas)
            entradas.append({
                "entrada_id": f"{p['pedido_id']}/{tipo}/{objetivo}",
                "pedido_id": p["pedido_id"], "expediente_id": exp["expediente_id"],
                "partido_id": exp["partido_id"], "tipo": tipo, "objetivo": objetivo,
                "motivo": exp["caso"]["motivo_clasificacion"],
                "juez_id": p["juez_id"], "juez_nombre": nombres.get(p["juez_id"], p["juez_id"]),
                "juzgado_id": p["juzgado_id"], "juzgado_nombre": nombres.get(p["juzgado_id"], p["juzgado_id"]),
                "ordenado_min": p["decidido_min"], "vence_min": max(o["vence_min"] for o in grupo),
                "estado": estado, "finalizado_min": fin, "motivo_fin": motivo_fin,
                "proveedores": [{"proveedor_id": o["proveedor_id"], "estado": o["estado"],
                                 "aplicada_min": o.get("aplicada_min"), "finalizada_min": o.get("finalizada_min")}
                                for o in ultimas],
            })
    return entradas


def nombres_publicos(juzgados_sim: dict) -> Dict[str, str]:
    """De la forma de GET /juzgados (sin claves) a {id: nombre} para jueces y juzgados."""
    nombres: Dict[str, str] = {}
    for jz in juzgados_sim.get("juzgados", []):
        nombres[jz["id"]] = jz["nombre"]
        for j in jz["jueces"]:
            nombres[j["id"]] = j["nombre"]
    return nombres


class RegistroPublico:
    def __init__(self, ruta_salida: str = "salida/registro_publico.json"):
        self.ruta_salida = ruta_salida
        self.entradas: List[EntradaPublica] = []

    def generar_entradas(self, pedido: Pedido, expediente: Expediente, ordenes: List[Orden],
                         juez_nombre: str, juzgado_nombre: str) -> List[EntradaPublica]:
        nombres = {pedido["juez_id"]: juez_nombre, pedido["juzgado_id"]: juzgado_nombre}
        return armar_entradas([pedido], {expediente["expediente_id"]: expediente}, ordenes, nombres)

    def generar_entrada(self, pedido: Pedido, expediente: Expediente, ordenes: List[Orden],
                        juez_nombre: str, juzgado_nombre: str) -> Optional[EntradaPublica]:
        """Compatibilidad: primera entrada del pedido (usar generar_entradas cuando hay IP y dominio)."""
        entradas = self.generar_entradas(pedido, expediente, ordenes, juez_nombre, juzgado_nombre)
        return entradas[0] if entradas else None

    def publicar(self, entradas: List[EntradaPublica]) -> None:
        """Reemplaza el registro con la foto actual (las entradas cambian de estado durante el partido)."""
        self.entradas = list(entradas)
        os.makedirs(os.path.dirname(self.ruta_salida) or ".", exist_ok=True)
        with open(self.ruta_salida, "w", encoding="utf-8") as f:
            json.dump({"entradas": self.entradas}, f, indent=2, ensure_ascii=False)
