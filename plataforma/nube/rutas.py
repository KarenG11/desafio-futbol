"""Rutas del partido de demo online (T12). Las monta plataforma/api/app.py.

POST /api/demo/iniciar      (PIN de juez) prende un Vercel Sandbox con simulador + motor y vuelve enseguida.
GET  /api/demo/verificacion salida de evaluacion/verificar.py del último partido, cuando termina.
"""
import hmac
import os
import subprocess
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from plataforma import db

REPO = "https://github.com/alejogomezmdz14-hash/desafio-futbol.git"
COMANDO = ("python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q -r requirements.txt "
           "&& /tmp/venv/bin/python -m plataforma.nube.partido_demo > /tmp/partido_demo.log 2>&1")
ACTIVO_S = 30   # si el motor escribió hace menos de esto y el partido no terminó, hay un partido corriendo

router = APIRouter()


def _pin(x_juez_pin: Optional[str] = Header(default=None)) -> None:
    esperado = os.environ.get("JUEZ_PIN", "")
    if not esperado or not x_juez_pin or not hmac.compare_digest(x_juez_pin.encode(), esperado.encode()):
        raise HTTPException(status_code=401, detail={"error": "PIN de juez inválido"})


class PedidoDemo(BaseModel):
    juez_automatico: bool = False
    acelerar: float = 6.0


def _hay_partido_corriendo() -> bool:
    pid = db.partido_actual()
    estado = db.estado_partido(pid) if pid else None
    if not estado or estado.get("finalizado"):
        return False
    with db._sesion() as (_, cur, pg):
        cur.execute(db._q("SELECT actualizado_ts FROM partidos WHERE partido_id = ?", pg), (pid,))
        fila = cur.fetchone()
    if not fila:
        return False
    from datetime import datetime
    try:
        hace = (datetime.now().astimezone() - datetime.fromisoformat(fila[0])).total_seconds()
    except ValueError:
        return False
    return hace < ACTIVO_S


@router.post("/api/demo/iniciar", dependencies=[Depends(_pin)])
async def iniciar_demo(pedido: PedidoDemo):
    if not os.environ.get("DATABASE_URL"):
        raise HTTPException(status_code=409, detail={"error": "La demo necesita DATABASE_URL (base de Neon)"})
    if not 1 <= pedido.acelerar <= 30:
        raise HTTPException(status_code=400, detail={"error": "acelerar tiene que estar entre 1 y 30"})
    minutos = (105 + 5) / pedido.acelerar + 3          # partido + gracia + instalación
    if minutos > 42:
        raise HTTPException(status_code=400, detail={"error": "Con esa velocidad el partido no entra en una sesión"})
    if _hay_partido_corriendo():
        raise HTTPException(status_code=409, detail={"error": "Ya hay un partido corriendo"})

    from vercel import sandbox
    from vercel.sandbox import GitSource

    box = await sandbox.create_sandbox(
        source=GitSource(url=REPO, revision="main", depth=1),
        execution_time_limit=timedelta(minutes=min(44, minutos + 5)),
        persistent=False,
        tags={"tipo": "partido-demo"},
        env={
            "DATABASE_URL": os.environ["DATABASE_URL"],
            "DEMO_ACELERAR": str(pedido.acelerar),
            "DEMO_JUEZ_AUTOMATICO": "1" if pedido.juez_automatico else "0",
        },
    )
    await box.create_command("bash", ["-lc", COMANDO], cwd="/vercel/sandbox",
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {
        "sandbox": box.name,
        "acelerar": pedido.acelerar,
        "juez_automatico": pedido.juez_automatico,
        "duracion_min": round(minutos, 1),
        "mensaje": "Partido en marcha: en ~30 s aparece en la pantalla del juez.",
    }


@router.get("/api/demo/verificacion")
def verificacion(partido_id: Optional[str] = None):
    pid = partido_id or db.partido_actual()
    v = db.obtener_verificacion(pid) if pid else None
    return {"partido_id": pid, "verificacion": v}
