"""API pública de la plataforma (T11, contratos v1.4 §5).

Se despliega en Vercel (entrypoint: plataforma.api.app:app) y también se usa en modo local.
No guarda estado en memoria ni lee claves de firma: todo sale de `plataforma.db`.
"""
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from plataforma import claves, db
from plataforma.contratos import (
    EJEMPLO_SIM_JUZGADOS,
    ESTADOS_ORDEN_ACTIVA,
    HASH_INICIAL,
    hash_evento_auditoria,
)

RAIZ = Path(__file__).resolve().parents[2]
WEB_DIR = RAIZ / "plataforma" / "web"
SITIO_DIR = RAIZ / "plataforma" / "sitio"

# Mapa público juez_id -> juzgado_id (de EJEMPLO_SIM_JUZGADOS; nunca lee datos/juzgados.json).
_JUZGADO_DE_JUEZ: Dict[str, str] = {
    juez["id"]: juzgado["id"]
    for juzgado in EJEMPLO_SIM_JUZGADOS["juzgados"]
    for juez in juzgado["jueces"]
}

app = FastAPI(title="Plataforma Federal de Órdenes de Bloqueo en Vivo")


@app.on_event("startup")
def _startup() -> None:
    try:
        db.crear_esquema()
    except Exception:
        pass


@app.exception_handler(HTTPException)
async def _http_error(_, exc: HTTPException):
    detalle = exc.detail
    if isinstance(detalle, dict) and "error" in detalle:
        return JSONResponse(status_code=exc.status_code, content=detalle)
    return JSONResponse(status_code=exc.status_code, content={"error": str(detalle)})


_FALLOS_PIN: Dict[str, List[float]] = {}
MAX_FALLOS_PIN = 5          # por cliente y por minuto
ESPERA_SOLICITUD_SEG = float(os.environ.get("ESPERA_SOLICITUD_SEG", "8"))


def _limitar_intentos(request: Optional[Request]) -> Tuple[str, List[float]]:
    cliente = request.client.host if request is not None and request.client else "?"
    ahora = time.monotonic()
    fallos = [t for t in _FALLOS_PIN.get(cliente, []) if ahora - t < 60]
    if len(fallos) >= MAX_FALLOS_PIN:
        raise HTTPException(status_code=429, detail={"error": "Demasiados intentos; esperá un minuto"})
    return cliente, fallos


def juez_sesion(x_juez_token: Optional[str] = Header(default=None)) -> str:
    """Quién decide: el juez de la sesión firmada (cada juez entra con su usuario y contraseña)."""
    juez_id = claves.leer_token(x_juez_token)
    if not juez_id:
        raise HTTPException(status_code=401, detail={"error": "Sesión de juez inválida o vencida: volvé a ingresar"})
    return juez_id


def _juez_del_cuerpo(cuerpo: Dict[str, Any], juez: str) -> str:
    """El juez es el de la sesión; si la pantalla manda otro, se rechaza (nadie firma por otro)."""
    pedido = cuerpo.get("juez_id")
    if pedido and pedido != juez:
        raise HTTPException(status_code=403, detail={"error": f"La sesión es de {juez}: no puede firmar como {pedido}"})
    return juez


def _jueces_conocidos() -> Dict[str, str]:
    est = db.estado_partido(db.partido_actual()) if db.partido_actual() else None
    juzgados = (est or {}).get("juzgados") or EJEMPLO_SIM_JUZGADOS
    return {j["id"]: j.get("nombre", j["id"]) for jz in juzgados["juzgados"] for j in jz["jueces"]}


@app.post("/api/juez/ingresar")
def api_juez_ingresar(cuerpo: Dict[str, Any], request: Request = None):
    cliente, fallos = _limitar_intentos(request)
    juez_id = (cuerpo.get("juez_id") or "").strip()
    jueces = _jueces_conocidos()
    if juez_id not in jueces or not claves.clave_valida(juez_id, cuerpo.get("clave") or ""):
        _FALLOS_PIN[cliente] = fallos + [time.monotonic()]
        raise HTTPException(status_code=401, detail={"error": "Usuario o contraseña incorrectos"})
    return {"token": claves.emitir_token(juez_id), "juez_id": juez_id, "nombre": jueces[juez_id]}


@app.get("/api/juez/jueces")
def api_juez_jueces():
    """Usuarios que pueden ingresar (los jueces del partido). Sin contraseñas."""
    return {"jueces": [{"juez_id": k, "nombre": v} for k, v in _jueces_conocidos().items()]}


@app.get("/api/juez/yo")
def api_juez_yo(juez: str = Depends(juez_sesion)):
    est = db.estado_partido(db.partido_actual()) if db.partido_actual() else None
    de_turno = juez in (est or {}).get("jueces_de_turno", [])
    return {"juez_id": juez, "nombre": _jueces_conocidos().get(juez, juez), "de_turno": de_turno,
            "ratificado": bool(est and est.get("turno_ratificado") and est.get("juez_ratificado") == juez)}


def _control_turno(pid: str, juez_id: str, exigir_ratificado: bool = True) -> Dict[str, Any]:
    """Fail-closed: sin estado del motor, con el simulador caído o con un juez fuera de turno, no se decide nada."""
    est = db.estado_partido(pid)
    if est is None or not est.get("simulador_ok", False):
        raise HTTPException(status_code=503, detail="El motor no reporta estado del partido: no se puede decidir")
    if juez_id not in _juzgado_de_juez(est):
        raise HTTPException(status_code=400, detail=f"Juez desconocido: {juez_id}")
    minuto = round(float(est["minuto_actual"]), 2)
    if juez_id not in est.get("jueces_de_turno", []):
        raise HTTPException(status_code=409, detail=f"{juez_id} no está de turno en el minuto {minuto}")
    if exigir_ratificado and (not est.get("turno_ratificado", False) or est.get("juez_ratificado", juez_id) != juez_id):
        raise HTTPException(status_code=409, detail=f"{juez_id} tiene que asumir el turno antes de decidir")
    return est


def _juzgado_de_juez(est: Optional[Dict[str, Any]]) -> Dict[str, str]:
    juzgados = (est or {}).get("juzgados") or EJEMPLO_SIM_JUZGADOS
    return {j["id"]: jz["id"] for jz in juzgados["juzgados"] for j in jz["jueces"]}


def _esperar_solicitud(pid: str, solicitud_id: str) -> Optional[Dict[str, Any]]:
    limite = time.monotonic() + ESPERA_SOLICITUD_SEG
    while time.monotonic() < limite:
        s = db.obtener_solicitud(pid, solicitud_id)
        if s and s["resultado"] is not None:
            return s["resultado"]
        time.sleep(0.25)
    return None


def _partido_o_defecto(partido_id: Optional[str] = None) -> str:
    pid = partido_id or db.partido_actual()
    return pid or "demo"


def _resumen_de_caso(caso: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "caso_id": caso["caso_id"],
        "host": caso["host"],
        "ip": caso["ip"],
        "organizacion": caso.get("organizacion"),
        "marca": caso.get("marca"),
        "motivo_clasificacion": caso["motivo_clasificacion"],
        "ip_compartida": caso["ip_compartida"],
        "dominios_en_ip": caso.get("dominios_en_ip", []),
        "tipo_recomendado": caso["tipo_recomendado"],
        "motivo_tipo": caso["motivo_tipo"],
        "primer_minuto": caso["primer_minuto"],
    }


def _recalcular_contadores(pid: str, estado_base: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza los contadores de pedidos con el estado vivo de la tabla pedidos."""
    pedidos = db.listar("pedidos", pid)
    ordenes = db.listar("ordenes", pid)
    reclamos = db.listar("reclamos", pid)
    casos = db.listar("casos", pid)
    contadores = dict(estado_base.get("contadores") or {})
    if casos:
        contadores["casos_piratas"] = sum(1 for c in casos if c.get("clasificacion") == "pirata")
        contadores["casos_descartados"] = sum(1 for c in casos if c.get("clasificacion") != "pirata")
    contadores["pedidos_pendientes"] = sum(1 for p in pedidos if p.get("estado") == "pendiente")
    contadores["pedidos_aprobados"] = sum(1 for p in pedidos if p.get("estado") == "aprobado")
    contadores["pedidos_rechazados"] = sum(1 for p in pedidos if p.get("estado") == "rechazado")
    if ordenes:
        contadores["ordenes_activas"] = sum(1 for o in ordenes if o.get("estado") in ESTADOS_ORDEN_ACTIVA)
        contadores["ordenes_fallidas"] = sum(1 for o in ordenes if o.get("estado") == "fallida")
    if reclamos:
        contadores["reclamos_pendientes"] = sum(1 for r in reclamos if r.get("estado") == "pendiente")
    res = dict(estado_base)
    res["contadores"] = contadores
    return res


@app.get("/api/estado")
def api_estado(partido_id: Optional[str] = None):
    pid = _partido_o_defecto(partido_id)
    est = db.estado_partido(pid)
    if est is None:   # sin motor: nada de valores inventados
        return {
            "partido_id": pid,
            "minuto_actual": None,
            "fin_min": None,
            "finalizado": False,
            "jueces_de_turno": [],
            "proximo_cambio_turno_min": None,
            "simulador_ok": False,
            "turno_ratificado": False,
            "contadores": {
                "casos_piratas": 0,
                "casos_descartados": 0,
                "pedidos_pendientes": 0,
                "pedidos_aprobados": 0,
                "pedidos_rechazados": 0,
                "ordenes_activas": 0,
                "ordenes_fallidas": 0,
                "reclamos_pendientes": 0,
            },
        }
    return _recalcular_contadores(pid, est)


@app.get("/api/pedidos")
def api_pedidos(estado: Optional[str] = None, partido_id: Optional[str] = None):
    pid = _partido_o_defecto(partido_id)
    pedidos = db.listar("pedidos", pid, estado=estado) if estado else db.listar("pedidos", pid)
    expedientes_cache: Dict[str, Optional[Dict[str, Any]]] = {}
    resultado: List[Dict[str, Any]] = []
    for p in pedidos:
        item = dict(p)
        if "resumen" not in item or not item["resumen"]:
            eid = item.get("expediente_id", "")
            if eid not in expedientes_cache:
                expedientes_cache[eid] = db.obtener("expedientes", pid, eid)
            exp = expedientes_cache[eid]
            if exp and "caso" in exp:
                item["resumen"] = _resumen_de_caso(exp["caso"])
        resultado.append(item)
    return {"pedidos": resultado}


@app.get("/api/expedientes/{expediente_id}")
def api_expediente(expediente_id: str, partido_id: Optional[str] = None):
    pid = _partido_o_defecto(partido_id)
    exp = db.obtener("expedientes", pid, expediente_id)
    if exp is None:
        raise HTTPException(status_code=404, detail=f"No existe el expediente {expediente_id}")
    return exp


def _procesar_decision_pedidos(cuerpo: Dict[str, Any], nuevo_estado: str, juez: str, partido_id: Optional[str] = None) -> Dict[str, Any]:
    pid = _partido_o_defecto(partido_id)
    pedido_ids = cuerpo.get("pedido_ids")
    juez_id = _juez_del_cuerpo(cuerpo, juez)
    if not isinstance(pedido_ids, list):
        raise HTTPException(status_code=400, detail="Faltan pedido_ids")

    motivo: Optional[str] = None
    if nuevo_estado == "rechazado":
        motivo = (cuerpo.get("motivo") or "").strip()
        if not motivo:
            raise HTTPException(status_code=400, detail="Rechazar requiere un motivo")

    est_partido = _control_turno(pid, juez_id)
    minuto_actual = round(float(est_partido["minuto_actual"]), 2)
    juzgado_id = _juzgado_de_juez(est_partido)[juez_id]

    decididos: List[str] = []
    errores: List[Dict[str, str]] = []

    for req_pid in pedido_ids:
        actual = db.obtener("pedidos", pid, req_pid)
        if actual is None:
            errores.append({"pedido_id": req_pid, "error": "No existe el pedido"})
            continue
        if actual.get("estado") != "pendiente":
            errores.append({"pedido_id": req_pid, "error": f"El pedido ya está {actual.get('estado')}"})
            continue
        ok = db.decidir_pedido(
            partido_id=pid,
            pedido_id=req_pid,
            estado=nuevo_estado,
            juez_id=juez_id,
            juzgado_id=juzgado_id,
            decidido_min=minuto_actual,
            motivo=motivo,
        )
        if ok:
            decididos.append(req_pid)
        else:
            errores.append({"pedido_id": req_pid, "error": "El pedido ya fue decidido"})

    clave_lista = "aprobados" if nuevo_estado == "aprobado" else "rechazados"
    return {clave_lista: decididos, "errores": errores, "decidido_min": minuto_actual}


@app.post("/api/pedidos/aprobar")
def api_aprobar(cuerpo: Dict[str, Any], partido_id: Optional[str] = None, juez: str = Depends(juez_sesion)):
    return _procesar_decision_pedidos(cuerpo, "aprobado", juez, partido_id)


@app.post("/api/pedidos/rechazar")
def api_rechazar(cuerpo: Dict[str, Any], partido_id: Optional[str] = None, juez: str = Depends(juez_sesion)):
    return _procesar_decision_pedidos(cuerpo, "rechazado", juez, partido_id)


@app.get("/api/ordenes")
def api_ordenes(partido_id: Optional[str] = None):
    pid = _partido_o_defecto(partido_id)
    return {"ordenes": db.listar("ordenes", pid)}


@app.get("/api/auditoria")
def api_auditoria(partido_id: Optional[str] = None):
    pid = _partido_o_defecto(partido_id)
    return {"eventos": db.auditoria(pid)}


@app.get("/api/auditoria/integridad")
def api_auditoria_integridad(partido_id: Optional[str] = None):
    pid = _partido_o_defecto(partido_id)
    prev = HASH_INICIAL
    eventos = db.auditoria(pid)
    for ev in eventos:
        if ev.get("hash_prev") != prev or ev.get("hash") != hash_evento_auditoria(ev):
            return {"partido_id": pid, "integra": False, "eventos": len(eventos), "falla_en_seq": ev.get("seq")}
        prev = ev["hash"]
    return {"partido_id": pid, "integra": True, "eventos": len(eventos), "ultimo_hash": prev}


@app.get("/api/reclamos")
def api_reclamos(partido_id: Optional[str] = None):
    pid = _partido_o_defecto(partido_id)
    return {"reclamos": db.listar("reclamos", pid)}


@app.post("/api/turno/asumir")
def api_asumir_turno(cuerpo: Dict[str, Any], partido_id: Optional[str] = None, juez: str = Depends(juez_sesion)):
    pid = _partido_o_defecto(partido_id)
    juez_id = _juez_del_cuerpo(cuerpo, juez)
    est = _control_turno(pid, juez_id, exigir_ratificado=False)
    sid = db.crear_solicitud(pid, "asumir_turno", {"juez_id": juez_id, "decidido_min": est["minuto_actual"]})
    return _respuesta_solicitud(pid, sid)


def _respuesta_solicitud(pid: str, sid: str):
    resultado = _esperar_solicitud(pid, sid)
    if resultado is None:   # el motor todavía no la procesó: no se informa un resultado que no ocurrió
        return JSONResponse(status_code=202, content={"solicitud_id": sid, "estado": "pendiente"})
    if "error" in resultado:
        raise HTTPException(status_code=409, detail=resultado["error"])
    if resultado.get("errores") and resultado.get("estado") != "levantado":
        return JSONResponse(status_code=502, content=resultado)
    return resultado


@app.get("/api/solicitudes/{solicitud_id}")
def api_solicitud(solicitud_id: str, partido_id: Optional[str] = None):
    pid = _partido_o_defecto(partido_id)
    s = db.obtener_solicitud(pid, solicitud_id)
    if s is None:
        raise HTTPException(status_code=404, detail=f"No existe la solicitud {solicitud_id}")
    return s


@app.post("/api/reclamos/levantar")
def api_levantar_reclamo(cuerpo: Dict[str, Any], partido_id: Optional[str] = None, juez: str = Depends(juez_sesion)):
    pid = _partido_o_defecto(partido_id)
    reclamo_id = cuerpo.get("reclamo_id")
    juez_id = _juez_del_cuerpo(cuerpo, juez)
    motivo = (cuerpo.get("motivo") or "").strip()
    reemplazar = bool(cuerpo.get("reemplazar", True))
    if not reclamo_id or not motivo:
        raise HTTPException(status_code=400, detail="Faltan reclamo_id o motivo")
    reclamo = db.obtener("reclamos", pid, reclamo_id)
    if reclamo is None:
        raise HTTPException(status_code=404, detail=f"No existe el reclamo {reclamo_id}")
    if reclamo.get("estado") != "pendiente":
        raise HTTPException(status_code=409, detail=f"El reclamo ya está {reclamo.get('estado')}")
    est = _control_turno(pid, juez_id)
    sid = db.crear_solicitud(pid, "levantar", {"reclamo_id": reclamo_id, "juez_id": juez_id, "motivo": motivo,
                                               "reemplazar": reemplazar, "decidido_min": est["minuto_actual"]})
    return _respuesta_solicitud(pid, sid)


@app.get("/api/publico")
def api_publico(partido_id: Optional[str] = None):
    from plataforma.transparencia import armar_entradas_publicas
    pid = _partido_o_defecto(partido_id)
    return {"entradas": armar_entradas_publicas(pid)}
@app.get("/")
def raiz():
    return FileResponse(SITIO_DIR / "index.html")


@app.get("/monitoreo")
def monitoreo():
    return FileResponse(SITIO_DIR / "monitoreo.html")


@app.get("/registro")
def registro():
    return FileResponse(SITIO_DIR / "registro.html")


@app.get("/partidos")
def partidos():
    return FileResponse(SITIO_DIR / "partidos.html")


@app.get("/partido")
def partido():
    return FileResponse(SITIO_DIR / "partido.html")


app.mount("/sitio", StaticFiles(directory=str(SITIO_DIR)), name="sitio")
if WEB_DIR.exists():
    app.mount("/juez", StaticFiles(directory=str(WEB_DIR), html=True), name="juez")


# T12: partido de demo online (Vercel Sandbox). Las rutas viven en plataforma/nube/.
from plataforma.nube.rutas import router as _router_demo  # noqa: E402

app.include_router(_router_demo)
