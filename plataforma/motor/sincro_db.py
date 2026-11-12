"""DISEÑO ANTERIOR — NO SE USA con el motor integrado (plataforma/motor/motor.py).

Era el puente que copiaba a la base el estado del motor en memoria (--base).
Se conserva solo como registro del trabajo del equipo (decisión 33 de coordinacion/decisiones.md). El motor actual
escribe directo en la base (plataforma/db) y la API es plataforma/api/app.py. Este módulo se niega a importarse para
que nadie lo use por accidente: sus llamadas no corresponden a la clase Motor actual.

Texto original:
Puente entre el motor (en memoria) y la base de T11 (plataforma/db), para que la web en Vercel vea y decida.

Reglas (contratos §10, decisiones 15 a 19):
- El motor ESCRIBE: estado del partido, casos, expedientes, pedidos (solo al crearlos), órdenes, reclamos y auditoría.
- La web solo cambia la decisión de los pedidos (aprobado o rechazado) e inserta solicitudes (asumir_turno, levantar).
- El motor LEE esas decisiones y solicitudes, y las ejecuta. Un pedido nunca se reescribe desde acá: pisaría la
  decisión del juez.
- Solo se escribe lo que cambió (huella por fila), para no saturar una base remota en cada vuelta.
"""

raise ImportError(f"{__name__} es del diseño anterior y no se usa con el motor integrado; ver el docstring.")

import json
import os
from typing import Dict, Optional

from plataforma import db
from plataforma.contratos import json_canonico


class SincroDB:
    def __init__(self, motor, partido_db_id: str):
        self.motor = motor
        self.pid = partido_db_id
        self._huellas: Dict[str, bytes] = {}
        self._pedidos_subidos: set = set()
        self._rechazos_vistos: set = set()
        self._aud_offset = 0
        db.usar_conexion_persistente()
        db.crear_esquema()

    def _cambio(self, clave: str, obj) -> bool:
        h = json_canonico(obj)
        if self._huellas.get(clave) == h:
            return False
        self._huellas[clave] = h
        return True

    # --- motor -> base ----------------------------------------------------------------------

    def empujar(self) -> None:
        m = self.motor
        estado = m.estado_api()
        db.guardar_estado_partido(self.pid, estado)
        for caso in m.cerebro.casos():
            if self._cambio(f"caso:{caso['caso_id']}", caso):
                db.guardar("casos", self.pid, caso["caso_id"], caso)
        for eid, exp in list(m.expedientes.items()):
            if self._cambio(f"exp:{eid}", {"h": exp["hash"]}):
                db.guardar("expedientes", self.pid, eid, exp)
        for pid_, p in list(m.pedidos.items()):
            if pid_ not in self._pedidos_subidos:
                db.guardar("pedidos", self.pid, pid_, dict(p, resumen=m.resumenes[pid_]), estado=p["estado"],
                           juez_id=p["juez_id"], juzgado_id=p["juzgado_id"], decidido_min=p["decidido_min"],
                           motivo_rechazo=p["motivo_rechazo"], despachado=pid_ in m.despachados)
                self._pedidos_subidos.add(pid_)
        for o in m.despacho.vista():
            if self._cambio(f"ord:{o['orden_id']}", o):
                db.guardar("ordenes", self.pid, o["orden_id"], o)
        for r in list(m.reclamos.values()):
            if self._cambio(f"rec:{r['reclamo_id']}", r):
                db.guardar("reclamos", self.pid, r["reclamo_id"], r)
        self._subir_auditoria()

    def _subir_auditoria(self) -> None:
        ruta = self.motor.ruta_auditoria
        if not os.path.exists(ruta):
            return
        with open(ruta, encoding="utf-8") as f:
            f.seek(self._aud_offset)
            for linea in f:
                if linea.strip():
                    db.agregar_auditoria(self.pid, json.loads(linea))
            self._aud_offset = f.tell()

    # --- base -> motor ------------------------------------------------------------------------

    def traer(self) -> None:
        m = self.motor
        for p in db.pedidos_para_despachar(self.pid):
            local = m.pedidos.get(p["pedido_id"])
            if local is None:
                continue
            m.aplicar_decision(p["pedido_id"], "aprobado", p["juez_id"], p.get("decidido_min"))
            db.marcar_despachado(self.pid, p["pedido_id"])
        for p in db.listar("pedidos", self.pid, estado="rechazado"):
            if p["pedido_id"] not in self._rechazos_vistos:
                self._rechazos_vistos.add(p["pedido_id"])
                m.aplicar_decision(p["pedido_id"], "rechazado", p["juez_id"], p.get("decidido_min"),
                                   p.get("motivo_rechazo"))
        for s in db.solicitudes_pendientes(self.pid):
            datos = s["datos"] or {}
            try:
                if s["tipo"] == "asumir_turno":
                    resultado = {"ratificadas": m.despacho.ratificar(datos.get("juez_id"))}
                elif s["tipo"] == "levantar":
                    resultado = m.levantar_por_reclamo(datos.get("reclamo_id"), datos.get("juez_id"),
                                                       datos.get("motivo", ""), bool(datos.get("reemplazar", True)))
                else:
                    resultado = {"error": f"Solicitud desconocida: {s['tipo']}"}
            except Exception as e:  # una solicitud mala no frena el partido; queda resuelta con el error
                resultado = {"error": str(e)}
            db.resolver_solicitud(self.pid, s["solicitud_id"], resultado)

    def decidir_en_base(self, pedido_id: str, estado: str, juez_id: str, juzgado_id: str, minuto: float,
                        motivo: Optional[str] = None) -> bool:
        """Para el juez automático o la API local: decide en la base como lo haría la web."""
        return db.decidir_pedido(self.pid, pedido_id, estado, juez_id, juzgado_id, minuto, motivo)
