"""T05 — Motor: el único componente que habla con el simulador.

Ciclo (~0,5 s reales): /estado -> detecciones -> cerebro -> expediente + pedido -> (juez) -> despacho firmado ->
seguimiento de proveedores -> reclamos -> solicitudes de la web -> estado en la base. Todo queda en la auditoría
interna encadenada (salida/auditoria_interna.jsonl + tabla auditoria). El registro oficial (salida/registro.jsonl)
lo escribe el simulador a partir de las llamadas reales.
"""
import time
import uuid
from typing import Any, Dict, List, Optional

from plataforma import db
from plataforma.analisis.cerebro import Cerebro
from plataforma.despacho import Despacho, Firmador, objetivos_por_proveedor, vence_para
from plataforma.evidencia.gestor import GestorEvidencia
from plataforma.motor.simulador import ClienteSimulador, ErrorRed
from plataforma.reclamos.gestor import GestorReclamos
from plataforma.transparencia import RegistroPublico, armar_entradas, nombres_publicos

GRACIA_MIN = 5.0          # el simulador cierra la ventana en fin_min + 5
MARGEN_TURNO_MIN = 0.25   # no firmar si al juez le quedan menos de 0,25 min de turno (latencia)


class Motor:
    def __init__(self, sim_url: str, juez_automatico: bool = False, ruta_auditoria: str = "salida/auditoria_interna.jsonl",
                 ruta_publico: str = "salida/registro_publico.json", ruta_juzgados=None, intervalo: float = 0.5,
                 log=print):
        self.sim = ClienteSimulador(sim_url)
        self.juez_automatico = juez_automatico
        self.intervalo = intervalo
        self.log = log
        self.firmador = Firmador(ruta_juzgados) if ruta_juzgados else Firmador()
        self.ruta_auditoria = ruta_auditoria
        self.publico = RegistroPublico(ruta_publico)
        self.corrida = uuid.uuid4().hex[:4]
        self.desde_det = -1e9
        self.desde_rec = -1e9
        self._t_estado = 0.0
        self._min_estado = 0.0
        self.acelerar = 1.0
        self.pedidos: Dict[str, dict] = {}
        self.expedientes: Dict[str, dict] = {}
        self.caso_de_expediente: Dict[str, dict] = {}
        self.juez_ratificado: Optional[str] = None
        self.turno_ratificado = True
        self.simulador_ok = True
        self.terminado = False

    # --- reloj y turnos --------------------------------------------------------------------
    def ahora(self) -> float:
        """Minuto simulado estimado (último /estado + tiempo real transcurrido x acelerar)."""
        return self._min_estado + (time.monotonic() - self._t_estado) * self.acelerar / 60.0

    def de_turno(self, minuto: float) -> List[str]:
        return [t["juez_id"] for t in self.turnos if t["desde_min"] <= minuto < t["hasta_min"]]

    def firmante(self) -> Optional[str]:
        """Juez de turno ratificado que sigue de turno durante todo el margen de envío; si no, None (fail-closed)."""
        if not self.simulador_ok:
            return None
        ahora = self.ahora()
        for juez in self.de_turno(ahora):
            if juez == self.juez_ratificado and juez in self.de_turno(ahora + MARGEN_TURNO_MIN) \
                    and self.firmador.conoce(juez):
                return juez
        return None

    # --- auditoría -------------------------------------------------------------------------
    def auditar(self, actor: str, accion: str, datos: Dict[str, Any]) -> None:
        self.evidencia.registrar_evento(actor, accion, datos, round(self.ahora(), 3))

    # --- arranque --------------------------------------------------------------------------
    def iniciar(self) -> None:
        self.partido = self.sim.get_ok("/partido")
        self.pid = self.partido["id"]
        self.proveedores = self.sim.get_ok("/proveedores")
        self.juzgados_pub = self.sim.get_ok("/juzgados")
        self.turnos = self.juzgados_pub["turnos"]
        self.fin_min = float(self.partido["fin_min"])
        db.crear_esquema()
        db.reiniciar_partido(self.pid)
        self.evidencia = GestorEvidencia(self.ruta_auditoria, reiniciar=True,
                                         al_registrar=lambda ev: db.agregar_auditoria(self.pid, ev))
        self.cerebro = Cerebro(self.partido, self._dns_ip)
        self.despacho = Despacho(self.sim, self.firmador, self.corrida, self.auditar,
                                 lambda o: db.guardar("ordenes", self.pid, o["orden_id"], o))
        self.reclamos = GestorReclamos(self.despacho.ordenes, self.cerebro.casos, self._dominios_de_ip,
                                       self._caso_de_pedido)
        self._leer_estado()
        self.juez_ratificado = (self.de_turno(self.ahora()) or [None])[0]
        self.auditar("motor", "motor_iniciado", {"partido_id": self.pid, "corrida": self.corrida,
                     "fin_min": self.fin_min, "juez_de_turno": self.juez_ratificado,
                     "juez_automatico": self.juez_automatico,
                     "proveedores": [p["id"] for p in self.proveedores]})
        self.log(f"[motor] partido {self.pid} corrida {self.corrida} desde min {self.ahora():.2f}")

    def _dns_ip(self, ip: str):
        estado, datos = self.sim.get(f"/dns-pasivo?ip={ip}")
        return datos if estado == 200 else None

    def _dominios_de_ip(self, ip: str) -> List[str]:
        """Para verificar un reclamo: DNS pasivo consultado de nuevo (el del caso puede estar desactualizado)."""
        conocidos = {d for c in self.cerebro.casos() if c["ip"] == ip for d in c["dominios_en_ip"]}
        return sorted(conocidos | set((self._dns_ip(ip) or {}).get("dominios", [])))

    def _caso_de_pedido(self, pedido_id: str) -> Optional[dict]:
        p = self.pedidos.get(pedido_id)
        return self.caso_de_expediente.get(p["expediente_id"]) if p else None

    def _leer_estado(self) -> dict:
        t0 = time.monotonic()
        try:
            est = self.sim.get_ok("/estado")
            self.simulador_ok = True
        except ErrorRed:
            self.simulador_ok = False
            raise
        self._t_estado = (t0 + time.monotonic()) / 2
        self._min_estado = float(est["minuto_actual"])
        self.acelerar = float(est.get("acelerar", 1.0))
        self.estado_sim = est
        return est

    # --- ciclo -----------------------------------------------------------------------------
    def ciclo(self) -> None:
        try:
            est = self._leer_estado()
        except ErrorRed as e:
            self.log(f"[motor] simulador no responde: {e}")
            self._publicar_estado()
            return
        self._controlar_turno(est)
        self._procesar_detecciones()
        if self.juez_automatico:
            self._juez_automatico()
        self._despachar_aprobados()
        self.despacho.seguir([p["id"] for p in self.proveedores], self.firmante(), self.ahora(), self.fin_min)
        self._procesar_reclamos()
        self._procesar_solicitudes()
        self._publicar_estado()
        if self.ahora() >= self.fin_min + GRACIA_MIN + 0.5:
            self.terminado = True

    def _controlar_turno(self, est: dict) -> None:
        de_turno = est.get("jueces_de_turno") or []
        if self.juez_ratificado not in de_turno and self.turno_ratificado:
            self.turno_ratificado = False
            self.auditar("motor", "cambio_de_turno", {"saliente": self.juez_ratificado, "entrantes": de_turno,
                         "nota": "envíos en espera hasta que el entrante asuma el turno"})
        if self.juez_automatico and not self.turno_ratificado and de_turno:
            self._asumir_turno(de_turno[0], modo="automatico_prueba")

    def _asumir_turno(self, juez_id: str, modo: str) -> dict:
        if juez_id not in self.de_turno(self.ahora()) or not self.firmador.conoce(juez_id):
            return {"error": f"{juez_id} no está de turno al minuto {self.ahora():.2f}"}
        vigentes = [o["orden_id"] for o in self.despacho.ordenes.values() if o["estado"] in ("recibida", "aplicada")]
        self.juez_ratificado, self.turno_ratificado = juez_id, True
        self.auditar(f"juez:{juez_id}", "turno_asumido", {"juez_id": juez_id, "modo": modo, "ratificadas": vigentes})
        self.despacho.reintentar_espera(self.firmante(), self.ahora(), self.fin_min)
        return {"juez_id": juez_id, "ratificadas": vigentes, "decidido_min": round(self.ahora(), 3)}

    def _procesar_detecciones(self) -> None:
        resp = self.sim.get_ok(f"/detecciones?desde={self.desde_det}")
        for d in resp["detecciones"]:
            caso, nuevo = self.cerebro.procesar(d)
            if not nuevo:
                self.auditar("analisis", "deteccion_repetida", {"deteccion_id": d["id"], "caso_id": caso["caso_id"]})
                db.guardar("casos", self.pid, caso["caso_id"], caso)
                continue
            db.guardar("casos", self.pid, caso["caso_id"], caso)
            if caso["clasificacion"] != "pirata":
                self.auditar("analisis", "caso_descartado", {"caso_id": caso["caso_id"], "host": caso["host"],
                             "clasificacion": caso["clasificacion"], "motivo": caso["motivo_clasificacion"]})
                continue
            self.auditar("analisis", "caso_creado", {"caso_id": caso["caso_id"], "host": caso["host"],
                         "ip": caso["ip"], "tipo_recomendado": caso["tipo_recomendado"], "motivo": caso["motivo_tipo"]})
            vence = vence_para(self.fin_min, self.ahora()) or int(self.fin_min)
            exp = self.evidencia.crear_expediente(caso, d, self.pid, round(self.ahora(), 3), vence)
            self.expedientes[exp["expediente_id"]] = exp
            self.caso_de_expediente[exp["expediente_id"]] = caso
            db.guardar("expedientes", self.pid, exp["expediente_id"], exp)
            self._crear_pedido(exp["expediente_id"], caso["tipo_recomendado"], caso, "deteccion", vence)
        self.desde_det = resp["minuto_actual"]

    def _crear_pedido(self, expediente_id: str, tipo: str, caso: dict, origen: str, vence: int,
                      excluir: Optional[set] = None, juez_aprueba: Optional[str] = None) -> Optional[str]:
        objetivos = [o for o in objetivos_por_proveedor(tipo, caso["ip"], caso["host"], self.proveedores)
                     if not excluir or (o["proveedor_id"], o["tipo"], o["objetivo"]) not in excluir]
        if not objetivos:
            return None
        pedido = {"pedido_id": f"P-{len(self.pedidos) + 1:03d}", "expediente_id": expediente_id, "origen": origen,
                  "objetivos": objetivos, "vence_min": vence, "creado_min": round(self.ahora(), 3),
                  "estado": "pendiente", "juez_id": None, "juzgado_id": None, "decidido_min": None,
                  "motivo_rechazo": None}
        self.pedidos[pedido["pedido_id"]] = pedido
        db.guardar("pedidos", self.pid, pedido["pedido_id"], pedido)
        self.auditar("motor", "pedido_creado", {"pedido_id": pedido["pedido_id"], "expediente_id": expediente_id,
                     "origen": origen, "objetivos": objetivos, "vence_min": vence})
        if juez_aprueba:
            self._aprobar(pedido["pedido_id"], juez_aprueba, "reemplazo aprobado al levantar el reclamo")
        return pedido["pedido_id"]

    def _aprobar(self, pedido_id: str, juez_id: str, modo: str) -> None:
        if db.decidir_pedido(self.pid, pedido_id, "aprobado", juez_id, self.firmador.juzgado_de[juez_id],
                             round(self.ahora(), 3)):
            self.auditar(f"juez:{juez_id}", "pedido_aprobado", {"pedido_id": pedido_id, "modo": modo})

    def _juez_automatico(self) -> None:
        juez = self.firmante()
        if juez is None:
            return
        for p in db.listar("pedidos", self.pid, estado="pendiente"):
            self._aprobar(p["pedido_id"], juez, "automatico_prueba")

    def _despachar_aprobados(self) -> None:
        for p in db.pedidos_para_despachar(self.pid):
            if p["pedido_id"] not in self.pedidos:
                continue
            self.pedidos[p["pedido_id"]].update({k: p[k] for k in ("estado", "juez_id", "juzgado_id", "decidido_min")})
            db.marcar_despachado(self.pid, p["pedido_id"])
            self.despacho.despachar_pedido(p, self.firmante(), self.ahora(), self.fin_min)
        for p in db.listar("pedidos", self.pid, estado="rechazado"):
            local = self.pedidos.get(p["pedido_id"])
            if local and local["estado"] == "pendiente":
                local.update(estado="rechazado", juez_id=p["juez_id"], motivo_rechazo=p["motivo_rechazo"])
                self.auditar(f"juez:{p['juez_id']}", "pedido_rechazado", {"pedido_id": p["pedido_id"],
                             "motivo": p["motivo_rechazo"]})

    # --- reclamos y solicitudes ------------------------------------------------------------
    def _procesar_reclamos(self) -> None:
        resp = self.sim.get_ok(f"/reclamos?desde={self.desde_rec}")
        for rs in resp["reclamos"]:
            if rs["id"] in self.reclamos.reclamos:
                continue
            r = self.reclamos.recibir_reclamo(rs)
            db.guardar("reclamos", self.pid, r["reclamo_id"], r)
            self.auditar("reclamos", "reclamo_recibido", {"reclamo_id": r["reclamo_id"], "dominio": r["dominio"],
                         "proveedor_id": r["proveedor_id"], "orden_ids": r["orden_ids"]})
            if r["estado"] == "descartado":
                self.auditar("reclamos", "reclamo_descartado", {"reclamo_id": r["reclamo_id"],
                             "verificacion": r["verificacion"]})
            self.desde_rec = max(self.desde_rec, rs["minuto"])
        if self.juez_automatico:
            juez = self.firmante()
            for r in list(self.reclamos.reclamos.values()):
                if r["estado"] == "pendiente" and juez:
                    self.levantar_reclamo(r["reclamo_id"], juez, "Sitio legítimo afectado (verificado por DNS pasivo)",
                                          True, modo="automatico_prueba")

    def levantar_reclamo(self, reclamo_id: str, juez_id: str, motivo: str, reemplazar: bool, modo: str) -> dict:
        if juez_id != self.firmante():
            return {"reclamo_id": reclamo_id, "estado": "pendiente", "ordenes_levantadas": [], "pedido_reemplazo_id": None,
                    "errores": [{"error": f"{juez_id} no es el juez de turno ratificado"}]}

        def crear_reemplazo(reclamo):
            caso = next(c for c in self.cerebro.casos() if c["caso_id"] == reclamo["caso_id"])
            exp_id = next(e for e, c in self.caso_de_expediente.items() if c["caso_id"] == caso["caso_id"])
            ya = {(o["proveedor_id"], o["tipo"], o["objetivo"]) for o in self.despacho.ordenes.values()
                  if o["estado"] in ("recibida", "aplicada")}
            vence = vence_para(self.fin_min, self.ahora())
            if vence is None:
                return None
            return self._crear_pedido(exp_id, "dominio", caso, f"reclamo:{reclamo['reclamo_id']}", vence,
                                      excluir=ya, juez_aprueba=juez_id)

        resp = self.reclamos.resolver_reclamo(
            reclamo_id, juez_id, reemplazar, round(self.ahora(), 3),
            lambda oid: self.despacho.levantar(oid, juez_id, f"Reclamo {reclamo_id}: {motivo}", self.ahora()),
            crear_reemplazo)
        r = self.reclamos.reclamos[reclamo_id]
        db.guardar("reclamos", self.pid, reclamo_id, r)
        if resp["estado"] == "levantado":
            self.auditar(f"juez:{juez_id}", "reclamo_levantado", {"reclamo_id": reclamo_id, "modo": modo,
                         "ordenes_levantadas": resp["ordenes_levantadas"],
                         "pedido_reemplazo_id": resp["pedido_reemplazo_id"]})
            for lev in resp["ordenes_levantadas"]:
                o = self.despacho.ordenes.get(lev["orden_id"])
                if o and o["tipo"] == "ip":
                    self.cerebro.marcar_ip_compartida(
                        o["objetivo"], f"Reclamo {reclamo_id} verificado: la IP {o['objetivo']} aloja sitios "
                                       "legítimos; desde ahora se bloquea solo por dominio")
            self._despachar_aprobados()
        return resp

    def _procesar_solicitudes(self) -> None:
        for s in db.solicitudes_pendientes(self.pid):
            d = s["datos"]
            if s["tipo"] == "asumir_turno":
                res = self._asumir_turno(d.get("juez_id", ""), modo="web")
            elif s["tipo"] == "levantar":
                try:
                    res = self.levantar_reclamo(d["reclamo_id"], d["juez_id"], d.get("motivo", ""),
                                                bool(d.get("reemplazar", True)), modo="web")
                except (KeyError, ValueError) as e:
                    res = {"error": str(e)}
            else:
                res = {"error": f"tipo de solicitud desconocido: {s['tipo']}"}
            db.resolver_solicitud(self.pid, s["solicitud_id"], res)

    # --- estado público --------------------------------------------------------------------
    def _publicar_estado(self) -> None:
        ordenes = list(self.despacho.ordenes.values()) if hasattr(self, "despacho") else []
        pedidos = db.listar("pedidos", self.pid)
        casos = self.cerebro.casos()
        proximo = [t["desde_min"] for t in self.turnos if t["desde_min"] > self.ahora()]
        estado = {
            "partido_id": self.pid, "minuto_actual": round(self.ahora(), 2), "fin_min": self.fin_min,
            "finalizado": self.ahora() >= self.fin_min, "jueces_de_turno": self.de_turno(self.ahora()),
            "proximo_cambio_turno_min": min(proximo) if proximo else None, "simulador_ok": self.simulador_ok,
            "turno_ratificado": self.turno_ratificado, "juez_ratificado": self.juez_ratificado,
            "juzgados": self.juzgados_pub,
            "licenciatarios": self.partido.get("licenciatarios", []),
            "contadores": {
                "casos_piratas": sum(c["clasificacion"] == "pirata" for c in casos),
                "casos_descartados": sum(c["clasificacion"] != "pirata" for c in casos),
                "pedidos_pendientes": sum(p["estado"] == "pendiente" for p in pedidos),
                "pedidos_aprobados": sum(p["estado"] == "aprobado" for p in pedidos),
                "pedidos_rechazados": sum(p["estado"] == "rechazado" for p in pedidos),
                "ordenes_activas": sum(o["estado"] in ("recibida", "aplicada") for o in ordenes),
                "ordenes_fallidas": sum(o["estado"] == "fallida" for o in ordenes),
                "reclamos_pendientes": sum(r["estado"] == "pendiente" for r in self.reclamos.reclamos.values()),
            },
        }
        db.guardar_estado_partido(self.pid, estado)
        self.publico.publicar(armar_entradas(pedidos, self.expedientes, ordenes, nombres_publicos(self.juzgados_pub)))

    def correr(self, max_ciclos: Optional[int] = None) -> None:
        self.iniciar()
        n = 0
        while not self.terminado and (max_ciclos is None or n < max_ciclos):
            t0 = time.monotonic()
            self.ciclo()
            n += 1
            time.sleep(max(0.0, self.intervalo - (time.monotonic() - t0)))
        self.auditar("motor", "partido_finalizado", {"ordenes": len(self.despacho.ordenes),
                     "pedidos": len(self.pedidos), "reclamos": len(self.reclamos.reclamos)})
        self.log(f"[motor] fin de la corrida en min {self.ahora():.2f}; auditoría en {self.ruta_auditoria}")
