"""T02 — Despacho: firma las órdenes aprobadas, las manda a cada proveedor, sigue su estado y reintenta.

Reglas (contratos.md §6, diseno.md §4, decisiones 9 y 12):
- A cada proveedor, el tipo que acepta (`objetivos` del pedido ya viene armado así).
- Cada envío, incluido cada reintento, se firma con el juez DE TURNO en el minuto del envío.
- Si cambió el turno y el entrante todavía no ratificó, los reintentos quedan en espera.
- `fallida` -> se reenvía con orden_id nuevo (intento + 1). Un 4xx al enviar es un error nuestro: se registra, no se repite.
- La clave del juez solo vive acá (datos/juzgados.json del simulador). Nunca sale por la API ni va a la base.
"""
import hashlib
import hmac
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Dict, List, Optional

from plataforma.contratos import mensaje_firma_levantar, mensaje_firma_orden

RAIZ = Path(__file__).resolve().parents[2]
Auditar = Callable[[str, str, dict, float], None]


def normalizar_sim(url: str) -> str:
    """En Windows 'localhost' prueba primero IPv6 (::1) y el simulador escucha solo en IPv4: cada consulta
    esperaba el timeout antes de caer a 127.0.0.1 (segundos por llamada). Se usa la IPv4 directo."""
    return url.rstrip("/").replace("://localhost", "://127.0.0.1")


def _http(base: str, ruta: str, cuerpo: Optional[dict] = None, timeout: float = 5.0):
    """(status, json). No levanta excepción por 4xx/5xx."""
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    req = urllib.request.Request(base + ruta, data=datos, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except ValueError:
            return e.code, {"error": str(e)}


class Despacho:
    def __init__(self, sim: str, corrida: str, auditar: Auditar,
                 ruta_juzgados: Path = RAIZ / "datos" / "juzgados.json"):
        self.sim = normalizar_sim(sim)
        self.corrida = corrida
        self.auditar = auditar
        datos = json.loads(Path(ruta_juzgados).read_text(encoding="utf-8"))
        self._claves: Dict[str, str] = {}
        self._juzgado_de: Dict[str, str] = {}
        for jz in datos["juzgados"]:
            for j in jz["jueces"]:
                self._claves[j["id"]] = j["clave_firma_demo"]
                self._juzgado_de[j["id"]] = jz["id"]
        self.lock = threading.RLock()
        self.ordenes: List[dict] = []          # historial completo (los reintentos se agregan)
        self.juez_ratificado: Optional[str] = None
        self.minuto = 0.0
        self.de_turno: List[str] = []

    # --- estado del turno (lo actualiza el motor en cada vuelta) ------------------------------

    def actualizar_turno(self, minuto: float, jueces_de_turno: List[str]) -> None:
        with self.lock:
            self.minuto = minuto
            self.de_turno = list(jueces_de_turno)
            if self.juez_ratificado is None and self.de_turno:
                self.juez_ratificado = self.de_turno[0]   # el primer turno del partido no necesita ratificar

    def turno_ratificado(self) -> bool:
        with self.lock:
            return bool(self.de_turno) and self.juez_ratificado == self.de_turno[0]

    def ratificar(self, juez_id: str) -> List[str]:
        """El juez entrante asume el turno: devuelve las órdenes vigentes que ratifica y libera los reintentos."""
        with self.lock:
            if juez_id not in self.de_turno:
                raise PermissionError(f"{juez_id} no está de turno en el minuto {self.minuto:.1f}")
            self.juez_ratificado = juez_id
            vigentes = [o["orden_id"] for o in self.ordenes if o["estado"] in ("recibida", "aplicada")]
            self.auditar(f"juez:{juez_id}", "turno_asumido", {"ratificadas": vigentes}, self.minuto)
            return vigentes

    # --- envío ------------------------------------------------------------------------------

    def juzgado_de(self, juez_id: str) -> str:
        return self._juzgado_de[juez_id]

    def _firmar(self, payload: dict) -> str:
        clave = self._claves[payload["juez_id"]]
        return hmac.new(clave.encode(), mensaje_firma_orden(payload).encode(), hashlib.sha256).hexdigest()

    def _refrescar_turno(self) -> None:
        """El simulador valida el turno cuando RECIBE la orden: se consulta justo antes de firmar."""
        try:
            estado, e = _http(self.sim, "/estado", timeout=3)
            if estado == 200:
                self.actualizar_turno(e["minuto_actual"], e["jueces_de_turno"])
        except OSError:
            pass

    def despachar(self, pedido: dict) -> List[dict]:
        """Manda una orden por objetivo del pedido, firmada por el juez de turno ahora."""
        self._refrescar_turno()
        with self.lock:
            juez = self.de_turno[0] if self.de_turno else None
            enviadas = []
            if self.minuto >= int(pedido["vence_min"]):
                # El proveedor la rechazaría (vence_min tiene que ser futuro) y cada rechazo cuenta en contra.
                self.auditar("despacho", "pedido_vencido_sin_enviar",
                             {"pedido_id": pedido["pedido_id"], "vence_min": int(pedido["vence_min"])})
                return enviadas
            for ob in pedido["objetivos"]:
                if juez is None:
                    break
                enviadas.append(self._enviar(pedido, ob, juez, intento=1, reemplaza=None))
            return enviadas

    def _enviar(self, pedido: dict, ob: dict, juez: str, intento: int, reemplaza: Optional[str]) -> dict:
        orden_id = f"ord-{self.corrida}-{pedido['pedido_id']}-{ob['proveedor_id']}-{intento}"
        payload = {"orden_id": orden_id, "expediente_id": pedido["expediente_id"], "tipo": ob["tipo"],
                   "objetivo": ob["objetivo"], "vence_min": int(pedido["vence_min"]),
                   "juzgado_id": self._juzgado_de[juez], "juez_id": juez}
        payload["firma"] = self._firmar(payload)
        orden = {"orden_id": orden_id, "pedido_id": pedido["pedido_id"], "expediente_id": pedido["expediente_id"],
                 "proveedor_id": ob["proveedor_id"], "tipo": ob["tipo"], "objetivo": ob["objetivo"],
                 "vence_min": payload["vence_min"], "juzgado_id": payload["juzgado_id"], "juez_id": juez,
                 "estado": "enviando", "intentos": intento, "reemplaza_a": reemplaza, "enviada_min": round(self.minuto, 3),
                 "recibida_min": None, "aplicada_min": None, "finalizada_min": None, "motivo": None, "consultar": None}
        self.ordenes.append(orden)
        try:
            estado, resp = _http(self.sim, f"/proveedores/{ob['proveedor_id']}/ordenes", payload)
        except OSError as e:     # red caída: queda como fallida y se reintenta en la próxima vuelta
            estado, resp = 0, {"error": f"Sin conexión con el proveedor: {e}"}
        if estado == 202:
            orden.update(estado="recibida", recibida_min=round(self.minuto, 3), consultar=resp.get("consultar"))
            self.auditar("despacho", "orden_enviada" if intento == 1 else "orden_reintentada",
                         {k: orden[k] for k in ("orden_id", "proveedor_id", "tipo", "objetivo", "vence_min", "juez_id")},
                         self.minuto)
        elif estado == 0:
            orden.update(estado="fallida", motivo=resp["error"])
            self.auditar("despacho", "orden_fallida", {"orden_id": orden_id, "motivo": resp["error"]}, self.minuto)
        else:
            orden.update(estado="rechazada", motivo=(resp or {}).get("error", f"HTTP {estado}"))
            self.auditar("despacho", "orden_rechazada", {"orden_id": orden_id, "motivo": orden["motivo"]}, self.minuto)
        return orden

    # --- seguimiento ------------------------------------------------------------------------

    def seguir(self, pedidos: Dict[str, dict]) -> None:
        """Consulta las órdenes activas, registra cambios y reintenta las fallidas (si el turno está ratificado)."""
        with self.lock:
            activas = [o for o in self.ordenes if o["estado"] == "recibida" or
                       (o["estado"] == "aplicada" and self.minuto >= o["vence_min"])]
        for o in activas:
            try:
                estado, vista = _http(self.sim, f"/proveedores/{o['proveedor_id']}/ordenes/{o['orden_id']}")
            except OSError:
                continue
            if estado != 200:
                continue
            with self.lock:
                nuevo = vista.get("estado")
                if nuevo == o["estado"]:
                    continue
                if nuevo == "aplicada":
                    o.update(estado="aplicada", aplicada_min=vista.get("aplicada_min"))
                    self.auditar(f"proveedor:{o['proveedor_id']}", "orden_aplicada", {"orden_id": o["orden_id"]},
                                 vista.get("aplicada_min") or self.minuto)
                elif nuevo in ("vencida", "levantada"):
                    o.update(estado=nuevo, finalizada_min=vista.get("finalizada_min"))
                    self.auditar(f"proveedor:{o['proveedor_id']}", f"orden_{nuevo}", {"orden_id": o["orden_id"]},
                                 vista.get("finalizada_min") or self.minuto)
                elif nuevo == "fallida":
                    o.update(estado="fallida", motivo=vista.get("motivo"))
                    self.auditar(f"proveedor:{o['proveedor_id']}", "orden_fallida",
                                 {"orden_id": o["orden_id"], "motivo": o["motivo"]}, self.minuto)
        self._reintentar(pedidos)

    def _reintentar(self, pedidos: Dict[str, dict]) -> None:
        with self.lock:
            hay_fallidas = any(o["estado"] == "fallida" for o in self.ordenes)
        if not hay_fallidas:
            return
        self._refrescar_turno()
        with self.lock:
            if not self.de_turno or not self.turno_ratificado():
                return                      # traspaso de turno pendiente: los reintentos esperan la ratificación
            juez = self.de_turno[0]
            ultimos: Dict[tuple, dict] = {}
            for o in self.ordenes:
                k = (o["pedido_id"], o["proveedor_id"])
                if k not in ultimos or o["intentos"] > ultimos[k]["intentos"]:
                    ultimos[k] = o
            for o in ultimos.values():
                if o["estado"] != "fallida" or self.minuto >= o["vence_min"] - 0.5:
                    continue
                pedido = pedidos[o["pedido_id"]]
                ob = {"proveedor_id": o["proveedor_id"], "tipo": o["tipo"], "objetivo": o["objetivo"]}
                self._enviar(pedido, ob, juez, intento=o["intentos"] + 1, reemplaza=o["orden_id"])

    def levantar(self, orden_id: str, juez_id: str, motivo: str) -> dict:
        """Levanta una orden activa con firma judicial (para reclamos, T06)."""
        with self.lock:
            o = next(x for x in self.ordenes if x["orden_id"] == orden_id)
            firma = hmac.new(self._claves[juez_id].encode(), mensaje_firma_levantar(orden_id, juez_id).encode(),
                             hashlib.sha256).hexdigest()
        estado, resp = _http(self.sim, f"/proveedores/{o['proveedor_id']}/ordenes/{orden_id}/levantar",
                             {"juez_id": juez_id, "firma": firma, "motivo": motivo})
        with self.lock:
            if estado == 200:
                o.update(estado="levantada", finalizada_min=resp.get("finalizada_min"), motivo=motivo)
                self.auditar(f"juez:{juez_id}", "orden_levantada", {"orden_id": orden_id, "motivo": motivo}, self.minuto)
            return {"ok": estado == 200, "respuesta": resp}

    def vista(self) -> List[dict]:
        with self.lock:
            return [dict(o) for o in self.ordenes]
