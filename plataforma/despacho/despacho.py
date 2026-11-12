"""T02 — Despacho: firma, envía, sigue y reintenta las órdenes de cada pedido aprobado.

Reglas (coordinacion/diseno.md §4):
- Objetivo por proveedor según `capacidades`: si el pedido es por IP, los que aceptan IP reciben la IP y los
  que solo aceptan dominio reciben el host del stream. Si es por dominio, todos reciben el host.
- Firma con el juez de turno en el minuto del envío (HMAC demo). Si el turno cambió y el entrante no
  ratificó, el envío queda en espera.
- Seguimiento con GET /proveedores/<id>/ordenes. `fallida` -> reenvío inmediato con orden_id nuevo.
- POST rechazado: 409 se resuelve adoptando la orden o con orden_id nuevo; 422 por vencimiento se abandona;
  403 (turno/firma) queda en espera; errores de red se reintentan con el mismo orden_id (idempotente).
"""
import math
from typing import Any, Callable, Dict, List, Optional

from plataforma.contratos import ORDEN_ID_FORMATO
from plataforma.motor.simulador import ClienteSimulador, ErrorRed

MAX_INTENTOS = 8
Auditar = Callable[[str, str, Dict[str, Any]], None]


def vence_para(fin_min: float, ahora: float) -> Optional[int]:
    """Vencimiento entero > ahora y <= fin del partido. None si el partido ya terminó."""
    if ahora >= fin_min:
        return None
    vence = int(fin_min)
    if vence <= ahora:
        vence = math.floor(ahora) + 1
    return vence if vence <= math.ceil(fin_min) else None


def objetivos_por_proveedor(tipo_caso: str, ip: str, host: str, proveedores: List[dict]) -> List[dict]:
    objetivos = []
    for p in proveedores:
        usa_ip = tipo_caso == "ip" and "ip" in p["capacidades"]
        if not usa_ip and "dominio" not in p["capacidades"]:
            continue
        objetivos.append({"proveedor_id": p["id"], "tipo": "ip" if usa_ip else "dominio",
                          "objetivo": ip if usa_ip else host})
    return objetivos


class Despacho:
    def __init__(self, sim: ClienteSimulador, firmador, corrida: str, auditar: Auditar,
                 guardar_orden: Callable[[dict], None]):
        self.sim = sim
        self.firmador = firmador
        self.corrida = corrida
        self.auditar = auditar
        self.guardar_orden = guardar_orden
        self.ordenes: Dict[str, dict] = {}          # orden_id -> Orden (contratos §6)
        self.en_espera: List[dict] = []             # envíos esperando juez de turno ratificado

    # --- envío -----------------------------------------------------------------------------
    def despachar_pedido(self, pedido: dict, firmante: Optional[str], ahora: float, fin_min: float) -> None:
        for ob in pedido["objetivos"]:
            self._enviar(pedido, ob, 1, None, firmante, ahora, fin_min)

    def _enviar(self, pedido: dict, ob: dict, intento: int, reemplaza: Optional[str],
                firmante: Optional[str], ahora: float, fin_min: float) -> None:
        tarea = {"pedido": pedido, "ob": ob, "intento": intento, "reemplaza": reemplaza}
        if firmante is None:
            self.en_espera.append(tarea)
            self.auditar("despacho", "orden_en_espera", {"pedido_id": pedido["pedido_id"],
                         "proveedor_id": ob["proveedor_id"], "motivo": "sin juez de turno ratificado"})
            return
        vence = vence_para(fin_min, ahora)
        if vence is None:
            self.auditar("despacho", "orden_no_enviada", {"pedido_id": pedido["pedido_id"],
                         "proveedor_id": ob["proveedor_id"], "motivo": "el partido terminó"})
            return
        if intento > MAX_INTENTOS:
            self.auditar("despacho", "orden_abandonada", {"pedido_id": pedido["pedido_id"],
                         "proveedor_id": ob["proveedor_id"], "motivo": f"más de {MAX_INTENTOS} intentos"})
            return
        orden_id = ORDEN_ID_FORMATO.format(corrida=self.corrida, pedido_id=pedido["pedido_id"],
                                           proveedor_id=ob["proveedor_id"], intento=intento)
        payload = {"orden_id": orden_id, "expediente_id": pedido["expediente_id"], "tipo": ob["tipo"],
                   "objetivo": ob["objetivo"], "vence_min": vence,
                   "juzgado_id": self.firmador.juzgado_de[firmante], "juez_id": firmante}
        payload["firma"] = self.firmador.firmar_orden(payload)
        orden = {k: payload[k] for k in payload if k != "firma"}
        orden.update({"pedido_id": pedido["pedido_id"], "proveedor_id": ob["proveedor_id"], "estado": "enviando",
                      "intentos": intento, "reemplaza_a": reemplaza, "enviada_min": round(ahora, 3),
                      "recibida_min": None, "aplicada_min": None, "finalizada_min": None, "motivo": None,
                      "consultar": None})
        try:
            estado, resp = self.sim.post(f"/proveedores/{ob['proveedor_id']}/ordenes", payload)
        except ErrorRed as e:
            self.auditar("despacho", "orden_error_red", {"orden_id": orden_id, "error": str(e)})
            self.en_espera.append(tarea)   # se reintenta con el mismo orden_id en el próximo ciclo
            return
        accion = "orden_reenviada" if intento > 1 else "orden_enviada"
        if estado == 202:
            orden.update(estado="recibida", recibida_min=round(ahora, 3), consultar=resp.get("consultar"))
            self._registrar(orden)
            self.auditar("despacho", accion, {"orden_id": orden_id, "proveedor_id": ob["proveedor_id"],
                         "tipo": ob["tipo"], "objetivo": ob["objetivo"], "vence_min": vence, "juez_id": firmante,
                         "reemplaza_a": reemplaza})
            return
        motivo = (resp or {}).get("error", f"HTTP {estado}")
        if estado == 409:
            ok, vista = self.sim.get(f"/proveedores/{ob['proveedor_id']}/ordenes/{orden_id}")
            if ok == 200 and vista.get("objetivo") == ob["objetivo"]:
                orden.update(estado=vista["estado"], recibida_min=vista.get("recibida_min"))
                self._registrar(orden)
                return
            self._enviar(pedido, ob, intento + 1, orden_id, firmante, ahora, fin_min)
            return
        orden.update(estado="rechazada", motivo=motivo)
        self._registrar(orden)
        self.auditar("despacho", "orden_rechazada", {"orden_id": orden_id, "proveedor_id": ob["proveedor_id"],
                     "http": estado, "motivo": motivo})
        if estado == 403:
            self.en_espera.append({"pedido": pedido, "ob": ob, "intento": intento + 1, "reemplaza": orden_id})

    def _registrar(self, orden: dict) -> None:
        self.ordenes[orden["orden_id"]] = orden
        self.guardar_orden(orden)

    # --- seguimiento -----------------------------------------------------------------------
    def seguir(self, proveedores: List[str], firmante: Optional[str], ahora: float, fin_min: float) -> None:
        activos = {o["proveedor_id"] for o in self.ordenes.values() if o["estado"] in ("recibida", "aplicada")}
        for pid in proveedores:
            if pid not in activos:
                continue
            try:
                estado, vistas = self.sim.get(f"/proveedores/{pid}/ordenes")
            except ErrorRed:
                continue
            if estado != 200:
                continue
            for v in vistas:
                o = self.ordenes.get(v["orden_id"])
                if o is None or o["estado"] == v["estado"]:
                    continue
                o["estado"] = v["estado"]
                for campo in ("aplicada_min", "finalizada_min", "motivo"):
                    if v.get(campo) is not None:
                        o[campo] = v[campo]
                self.guardar_orden(o)
                self.auditar(f"proveedor:{pid}", f"orden_{v['estado']}", {"orden_id": o["orden_id"],
                             "tipo": o["tipo"], "objetivo": o["objetivo"], "aplicada_min": o.get("aplicada_min"),
                             "finalizada_min": o.get("finalizada_min"), "motivo": o.get("motivo")})
                if v["estado"] == "fallida":
                    pedido = {"pedido_id": o["pedido_id"], "expediente_id": o["expediente_id"]}
                    ob = {"proveedor_id": pid, "tipo": o["tipo"], "objetivo": o["objetivo"]}
                    self._enviar(pedido, ob, o["intentos"] + 1, o["orden_id"], firmante, ahora, fin_min)
        self.reintentar_espera(firmante, ahora, fin_min)

    def reintentar_espera(self, firmante: Optional[str], ahora: float, fin_min: float) -> None:
        if firmante is None or not self.en_espera:
            return
        pendientes, self.en_espera = self.en_espera, []
        for t in pendientes:
            self._enviar(t["pedido"], t["ob"], t["intento"], t["reemplaza"], firmante, ahora, fin_min)

    # --- levantar --------------------------------------------------------------------------
    def levantar(self, orden_id: str, juez_id: str, motivo: str, ahora: float) -> Optional[str]:
        """Devuelve None si se levantó, o el error."""
        o = self.ordenes[orden_id]
        cuerpo = {"juez_id": juez_id, "firma": self.firmador.firmar_levantar(orden_id, juez_id), "motivo": motivo}
        try:
            estado, resp = self.sim.post(f"/proveedores/{o['proveedor_id']}/ordenes/{orden_id}/levantar", cuerpo)
        except ErrorRed as e:
            return str(e)
        if estado != 200:
            return (resp or {}).get("error", f"HTTP {estado}")
        o.update(estado="levantada", finalizada_min=resp.get("finalizada_min", round(ahora, 3)), motivo=motivo)
        self.guardar_orden(o)
        self.auditar(f"juez:{juez_id}", "orden_levantada", {"orden_id": orden_id, "proveedor_id": o["proveedor_id"],
                     "tipo": o["tipo"], "objetivo": o["objetivo"], "motivo": motivo})
        return None
