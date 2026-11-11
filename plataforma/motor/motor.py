"""T05 — Motor: el loop que une simulador, cerebro (T01), evidencia (T03), juez (T04) y despacho (T02).

Estado en memoria (plan B de la decisión 20: todo corre en la notebook). Cuando T11 tenga plataforma/db,
se persiste ahí sin cambiar las formas: la API (api.py) devuelve exactamente lo de contratos.md §5.
"""
import copy
import json
import secrets
import shutil
import threading
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional

from plataforma.analisis import Cerebro
from plataforma.contratos import GRACIA_MIN, vence_min_para
from plataforma.despacho.despacho import Despacho, _http, normalizar_sim
from plataforma.evidencia.gestor import GestorEvidencia

RAIZ = Path(__file__).resolve().parents[2]
ESPERA_S = 0.25        # a x30, un cuarto de segundo real son ~0,12 minutos de partido


class Motor:
    def __init__(self, sim: str, juez_automatico: bool = False, salida: Path = RAIZ / "salida"):
        self.sim = normalizar_sim(sim)
        self.juez_automatico = juez_automatico
        self.corrida = secrets.token_hex(2)
        self.lock = threading.RLock()          # estado del motor (pedidos, expedientes)
        self._lock_aud = threading.Lock()      # SOLO la auditoría: nunca toma otro lock adentro (evita deadlocks)
        self.partido = self._pedir("/partido")
        self.proveedores = self._pedir("/proveedores")
        self.turnos = self._pedir("/juzgados").get("turnos", [])
        self.fin = float(self.partido["fin_min"])
        self.salida = Path(salida)
        self.ruta_auditoria = self.salida / f"auditoria_{self.partido['id']}_{self.corrida}.jsonl"
        self.evidencia = GestorEvidencia(str(self.ruta_auditoria))
        self.cerebro = Cerebro(self.partido, self._dns)
        self.despacho = Despacho(self.sim, self.corrida, self.auditar)
        self.pedidos: Dict[str, dict] = {}
        self.resumenes: Dict[str, dict] = {}
        self.expedientes: Dict[str, dict] = {}
        self.despachados: set = set()
        self.minuto = 0.0
        self.de_turno: List[str] = []
        self.ultimo_ok = 0.0
        self.desde = -1.0
        self.terminado = False
        self.descartados = 0

    # --- utilidades -------------------------------------------------------------------------

    def _pedir(self, ruta: str):
        estado, datos = _http(self.sim, ruta)
        if estado != 200:
            raise RuntimeError(f"El simulador respondió {estado} en {ruta}: {datos}")
        return datos

    def _dns(self, ip: str):
        estado, datos = _http(self.sim, f"/dns-pasivo?ip={ip}")
        return datos if estado == 200 else None

    def auditar(self, actor: str, accion: str, datos: dict, minuto: Optional[float] = None) -> None:
        with self._lock_aud:
            self.evidencia.registrar_evento(actor, accion, datos, round(minuto if minuto is not None else self.minuto, 3))

    # --- loop ---------------------------------------------------------------------------------

    def correr(self) -> None:
        self.auditar("motor", "partido_iniciado", {"partido_id": self.partido["id"], "corrida": self.corrida,
                                                   "juez_automatico": self.juez_automatico})
        while not self.terminado:
            try:
                self.vuelta()
            except Exception:  # un error en una vuelta no puede frenar el partido
                traceback.print_exc()
            time.sleep(ESPERA_S)

    def vuelta(self) -> None:
        estado = self._pedir("/estado")
        with self.lock:
            self.minuto = estado["minuto_actual"]
            self.de_turno = estado["jueces_de_turno"]
            self.ultimo_ok = time.monotonic()
        self.despacho.actualizar_turno(self.minuto, self.de_turno)

        lote = self._pedir(f"/detecciones?desde={self.desde}")
        for d in lote["detecciones"]:
            self._procesar(d)
        self.desde = lote["minuto_actual"]

        if self.juez_automatico:
            if self.de_turno and not self.despacho.turno_ratificado():
                self.despacho.ratificar(self.de_turno[0])
            pendientes = [p for p, x in self.pedidos.items() if x["estado"] == "pendiente"]
            if pendientes and self.de_turno:
                self.decidir(pendientes, self.de_turno[0], "aprobado")

        for pid, p in list(self.pedidos.items()):
            if p["estado"] == "aprobado" and pid not in self.despachados:
                self.despachados.add(pid)
                self.despacho.despachar(p)
        self.despacho.seguir(self.pedidos)

        if self.minuto >= self.fin + GRACIA_MIN + 0.5:
            self._cerrar()

    def _procesar(self, d: dict) -> None:
        caso, nuevo = self.cerebro.procesar(d)
        if not nuevo:
            return
        if caso["clasificacion"] != "pirata":
            with self.lock:
                self.descartados += 1
            self.auditar("analisis", "caso_descartado",
                         {"caso_id": caso["caso_id"], "host": caso["host"], "clasificacion": caso["clasificacion"],
                          "motivo": caso["motivo_clasificacion"]}, d["minuto"])
            return
        self.auditar("analisis", "caso_creado", {"caso_id": caso["caso_id"], "host": caso["host"], "ip": caso["ip"],
                                                "tipo_recomendado": caso["tipo_recomendado"]}, self.minuto)
        with self.lock:
            # Copia congelada: el cerebro sigue sumando detecciones al caso vivo, y el expediente ya está hasheado.
            with self._lock_aud:
                exp = self.evidencia.crear_expediente(copy.deepcopy(caso), d, self.partido["id"], round(self.minuto, 3))
            self.expedientes[exp["expediente_id"]] = exp
            pid = f"P-{len(self.pedidos) + 1:03d}"
            objetivos = []
            for pv in self.proveedores:
                if caso["tipo_recomendado"] == "ip" and "ip" in pv["capacidades"]:
                    objetivos.append({"proveedor_id": pv["id"], "tipo": "ip", "objetivo": caso["ip"]})
                elif "dominio" in pv["capacidades"]:
                    objetivos.append({"proveedor_id": pv["id"], "tipo": "dominio", "objetivo": caso["host"]})
            self.pedidos[pid] = {"pedido_id": pid, "expediente_id": exp["expediente_id"], "origen": "deteccion",
                                 "objetivos": objetivos, "vence_min": vence_min_para(self.fin),
                                 "creado_min": round(self.minuto, 3), "estado": "pendiente", "juez_id": None,
                                 "juzgado_id": None, "decidido_min": None, "motivo_rechazo": None}
            self.resumenes[pid] = {k: caso[k] for k in ("caso_id", "host", "ip", "organizacion", "marca",
                                                        "motivo_clasificacion", "ip_compartida", "dominios_en_ip",
                                                        "tipo_recomendado", "motivo_tipo", "primer_minuto")}
        self.auditar("motor", "pedido_creado", {"pedido_id": pid, "expediente_id": exp["expediente_id"],
                                               "objetivos": objetivos}, self.minuto)

    # --- decisiones del juez (las llama la API o el juez automático) -------------------------

    def decidir(self, pedido_ids: List[str], juez_id: str, nuevo: str, motivo: Optional[str] = None) -> dict:
        hechos, errores = [], []
        with self.lock:
            for pid in pedido_ids:
                p = self.pedidos.get(pid)
                if p is None:
                    errores.append({"pedido_id": pid, "error": "No existe el pedido"})
                elif juez_id not in self.de_turno:
                    errores.append({"pedido_id": pid, "error": f"{juez_id} no está de turno en el minuto {self.minuto:.1f}"})
                elif p["estado"] != "pendiente":
                    errores.append({"pedido_id": pid, "error": f"El pedido ya está {p['estado']}"})
                else:
                    p.update(estado=nuevo, juez_id=juez_id, juzgado_id=self.despacho.juzgado_de(juez_id),
                             decidido_min=round(self.minuto, 3), motivo_rechazo=motivo if nuevo == "rechazado" else None)
                    hechos.append(pid)
        for pid in hechos:
            self.auditar(f"juez:{juez_id}", "pedido_aprobado" if nuevo == "aprobado" else "pedido_rechazado",
                         {"pedido_id": pid, **({"motivo": motivo} if motivo else {})})
        return {"hechos": hechos, "errores": errores, "decidido_min": round(self.minuto, 3)}

    # --- vistas para la API ---------------------------------------------------------------

    def estado_api(self) -> dict:
        ordenes = self.despacho.vista()           # fuera del lock del motor: nunca anidar motor -> despacho
        ratificado = self.despacho.turno_ratificado()
        with self.lock:
            ps = list(self.pedidos.values())
            prox = min((t["hasta_min"] for t in self.turnos if t["hasta_min"] > self.minuto), default=None)
            return {
                "partido_id": self.partido["id"], "minuto_actual": self.minuto, "fin_min": self.fin,
                "finalizado": self.minuto >= self.fin, "jueces_de_turno": self.de_turno,
                "proximo_cambio_turno_min": prox if prox is not None and prox < self.fin else None,
                "simulador_ok": time.monotonic() - self.ultimo_ok < 5,
                "turno_ratificado": ratificado,
                "contadores": {
                    "casos_piratas": len(ps), "casos_descartados": self.descartados,
                    "pedidos_pendientes": sum(p["estado"] == "pendiente" for p in ps),
                    "pedidos_aprobados": sum(p["estado"] == "aprobado" for p in ps),
                    "pedidos_rechazados": sum(p["estado"] == "rechazado" for p in ps),
                    "ordenes_activas": sum(o["estado"] in ("recibida", "aplicada") for o in ordenes),
                    "ordenes_fallidas": sum(o["estado"] == "fallida" for o in ordenes),
                    "reclamos_pendientes": 0,
                },
            }

    def pedidos_api(self, filtro: Optional[str]) -> List[dict]:
        with self.lock:
            return [dict(p, resumen=self.resumenes[p["pedido_id"]]) for p in self.pedidos.values()
                    if filtro is None or p["estado"] == filtro]

    def publico_api(self) -> List[dict]:
        """Registro público: qué se bloqueó, cuándo, por orden de quién y hasta cuándo. Sin capturas ni claves."""
        return [{"objetivo": o["objetivo"], "tipo": o["tipo"], "proveedor_id": o["proveedor_id"],
                 "desde_min": o["aplicada_min"], "hasta_min": o["finalizada_min"] or o["vence_min"],
                 "juzgado_id": o["juzgado_id"], "juez_id": o["juez_id"], "estado": o["estado"],
                 "expediente_id": o["expediente_id"]}
                for o in self.despacho.vista() if o["aplicada_min"] is not None]

    # --- cierre ---------------------------------------------------------------------------

    def _cerrar(self) -> None:
        self.auditar("motor", "partido_cerrado", {"pedidos": len(self.pedidos),
                                                  "ordenes": len(self.despacho.ordenes)})
        with self.lock:
            self.terminado = True
            primero = next(iter(self.expedientes.values()), None)
            if primero:
                (self.salida / f"expediente_{self.partido['id']}_{self.corrida}.json").write_text(
                    json.dumps(primero, ensure_ascii=False, indent=2), encoding="utf-8")
        with self._lock_aud:
            integra = self.evidencia.verificar_integridad()
        print(f"\nPartido cerrado. Auditoría: {self.ruta_auditoria} (íntegra: {integra}).")

    def exportar_entrega(self, destino: Path) -> None:
        destino.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.ruta_auditoria, destino / "auditoria-final.jsonl")
        with self.lock:
            primero = next(iter(self.expedientes.values()), None)
        if primero:
            (destino / "expediente-final.json").write_text(json.dumps(primero, ensure_ascii=False, indent=2),
                                                           encoding="utf-8")
