"""T07 — Transparencia pública. armar_entradas_publicas(partido_id) lee la base (lo usa GET /api/publico)."""
from typing import List

from plataforma.transparencia.registro import RegistroPublico, armar_entradas, estado_publico, nombres_publicos


def armar_entradas_publicas(partido_id: str) -> List[dict]:
    from plataforma import db
    from plataforma.contratos import EJEMPLO_SIM_JUZGADOS
    estado = db.estado_partido(partido_id) or {}
    nombres = nombres_publicos(estado.get("juzgados") or EJEMPLO_SIM_JUZGADOS)
    expedientes = {e["expediente_id"]: e for e in db.listar("expedientes", partido_id)}
    return armar_entradas(db.listar("pedidos", partido_id), expedientes, db.listar("ordenes", partido_id), nombres)


__all__ = ["RegistroPublico", "armar_entradas", "armar_entradas_publicas", "estado_publico", "nombres_publicos"]
