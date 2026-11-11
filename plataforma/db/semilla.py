"""Carga datos de ejemplo coherentes en la base de datos (T11, Paso 8).

Uso:
    PYTHONUTF8=1 python -m plataforma.db.semilla
"""
import copy
from typing import Any, Dict

from plataforma import db
from plataforma.contratos import (
    EJEMPLO_API_ESTADO,
    EJEMPLO_AUDITORIA,
    EJEMPLO_CASO,
    EJEMPLO_EXPEDIENTE,
    EJEMPLO_ORDEN,
    EJEMPLO_ORDEN_FALLIDA,
    EJEMPLO_ORDEN_REINTENTO,
    EJEMPLO_PEDIDO_PENDIENTE,
    EJEMPLO_RECLAMO_GESTION,
    hash_expediente,
)

PARTIDO_DEMO = "demo"


def cargar_semilla(partido_id: str = PARTIDO_DEMO) -> None:
    db.crear_esquema()

    # 1. Caso 1 (de contratos.py) y Caso 2 (ejemplo con IP compartida -> bloqueo por dominio)
    caso1 = copy.deepcopy(EJEMPLO_CASO)
    caso2: Dict[str, Any] = {
        "caso_id": "C-002",
        "host": "live.golazo-cdn.test",
        "ip": "198.51.100.25",
        "asn": 64501,
        "organizacion": "Nube Austral CDN (ficticio)",
        "sitio": "golazo-cdn.test",
        "pagina": "https://golazo-cdn.test/partido",
        "deteccion_ids": ["D-0002"],
        "primer_minuto": 4.0,
        "marca": "LP26-PRA-OFI-S048211",
        "marca_origen": "Señal oficial del titular (plataforma propia)",
        "clasificacion": "pirata",
        "motivo_clasificacion": "Marca de agua de la señal oficial del partido (LP26-PRA-OFI) en un dominio no autorizado",
        "dominios_en_ip": ["live.golazo-cdn.test", "panaderia-la-espiga.test", "estudio-contable-sur.test"],
        "ip_compartida": True,
        "tipo_recomendado": "dominio",
        "motivo_tipo": "La IP es compartida con sitios de otros dominios (panaderia-la-espiga.test, estudio-contable-sur.test)",
    }
    db.guardar("casos", partido_id, caso1["caso_id"], caso1)
    db.guardar("casos", partido_id, caso2["caso_id"], caso2)

    # 2. Expedientes 1 y 2
    exp1 = copy.deepcopy(EJEMPLO_EXPEDIENTE)
    exp1["partido_id"] = partido_id
    exp1["hash"] = hash_expediente(exp1)

    exp2 = copy.deepcopy(EJEMPLO_EXPEDIENTE)
    exp2["expediente_id"] = "EXP-2026-000002"
    exp2["partido_id"] = partido_id
    exp2["caso"] = caso2
    exp2["creado_min"] = 4.1
    exp2["capturas"][0]["deteccion_id"] = "D-0002"
    exp2["capturas"][0]["capturada_min"] = 4.0
    exp2["hash"] = hash_expediente(exp2)

    db.guardar("expedientes", partido_id, exp1["expediente_id"], exp1)
    db.guardar("expedientes", partido_id, exp2["expediente_id"], exp2)

    # 3. Dos pedidos pendientes (P-001 por IP + dominio en valle, P-002 solo por dominio)
    ped1 = copy.deepcopy(EJEMPLO_PEDIDO_PENDIENTE)
    ped2: Dict[str, Any] = {
        "pedido_id": "P-002",
        "expediente_id": "EXP-2026-000002",
        "origen": "deteccion",
        "objetivos": [
            {"proveedor_id": "aurora", "tipo": "dominio", "objetivo": "live.golazo-cdn.test"},
            {"proveedor_id": "andina", "tipo": "dominio", "objetivo": "live.golazo-cdn.test"},
            {"proveedor_id": "valle", "tipo": "dominio", "objetivo": "live.golazo-cdn.test"},
            {"proveedor_id": "cumbre", "tipo": "dominio", "objetivo": "live.golazo-cdn.test"},
        ],
        "vence_min": 105,
        "creado_min": 4.1,
        "estado": "pendiente",
        "juez_id": None,
        "juzgado_id": None,
        "decidido_min": None,
        "motivo_rechazo": None,
    }
    db.guardar("pedidos", partido_id, ped1["pedido_id"], ped1, estado="pendiente", despachado=False)
    db.guardar("pedidos", partido_id, ped2["pedido_id"], ped2, estado="pendiente", despachado=False)

    # 4. Órdenes de ejemplo
    for o in (EJEMPLO_ORDEN, EJEMPLO_ORDEN_FALLIDA, EJEMPLO_ORDEN_REINTENTO):
        db.guardar("ordenes", partido_id, o["orden_id"], copy.deepcopy(o))

    # 5. Reclamo de ejemplo
    reclamo = copy.deepcopy(EJEMPLO_RECLAMO_GESTION)
    db.guardar("reclamos", partido_id, reclamo["reclamo_id"], reclamo)

    # 6. Auditoría corta (idempotente: solo inserta los seq que no estén)
    ultimo = db.ultimo_evento_auditoria(partido_id)
    seq_actual = ultimo["seq"] if ultimo else 0
    for ev in EJEMPLO_AUDITORIA:
        if ev["seq"] > seq_actual:
            db.agregar_auditoria(partido_id, copy.deepcopy(ev))

    # 7. Estado vivo del partido
    estado = copy.deepcopy(EJEMPLO_API_ESTADO)
    estado["partido_id"] = partido_id
    estado["contadores"]["casos_piratas"] = 2
    estado["contadores"]["pedidos_pendientes"] = 2
    estado["contadores"]["pedidos_aprobados"] = 0
    db.guardar_estado_partido(partido_id, estado)

    print(f"Semilla cargada OK para partido_id='{partido_id}' (2 casos, 2 expedientes, 2 pedidos pendientes, 3 órdenes, 4 eventos de auditoría).")


if __name__ == "__main__":
    cargar_semilla()
