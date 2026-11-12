"""Piezas compartidas de los videos de Tarjeta Roja (hacer_presentacion.py y hacer_short.py).

Requisitos (en un entorno aparte, no en requirements.txt): edge-tts, playwright, imageio-ffmpeg; Microsoft Edge
instalado; el modelo VRM en salida/video/modelo.vrm (muestra oficial de pixiv, licencia VRM 1.0 con uso comercial
permitido y sin crédito obligatorio). La app y el partido son los reales: se levantan la API, el simulador oficial y el
motor, y la pantalla del juez se maneja con clics.
"""
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import imageio_ffmpeg

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
D = RAIZ / "salida" / "video"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
PY = shutil.which("py") or "python"            # el Python del proyecto (con FastAPI, etc.)
APP = "http://127.0.0.1:8000"
PIN = "1234"
TASA = 24000


def api(ruta: str, cuerpo=None):
    req = urllib.request.Request(APP + ruta, data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
                                 headers={"Content-Type": "application/json", "X-Juez-Pin": PIN})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read() or b"null")


class JuezDeFondo(threading.Thread):
    """Firma lo que llega fuera de la escena del juez (en esa escena firma la pantalla, con clics)."""
    def __init__(self):
        super().__init__(daemon=True)
        self.pausado, self.fin, self.visto = False, False, {}

    def run(self):
        while not self.fin:
            time.sleep(0.5)
            if self.pausado:
                continue
            try:
                est = api("/api/estado")
                juez = (est.get("jueces_de_turno") or [None])[0]
                if not juez or not est.get("simulador_ok"):
                    continue
                if not est.get("turno_ratificado") or est.get("juez_ratificado") != juez:
                    try:
                        api("/api/turno/asumir", {"juez_id": juez})
                    except Exception:
                        pass
                    continue
                ahora = time.monotonic()
                listos = []
                for p in api("/api/pedidos?estado=pendiente")["pedidos"]:
                    visto = self.visto.setdefault(p["pedido_id"], ahora)
                    if ahora - visto > 2.5:
                        listos.append(p["pedido_id"])
                if listos:
                    api("/api/pedidos/aprobar", {"pedido_ids": listos, "juez_id": juez})
            except Exception as e:
                if not self.fin:
                    print("[juez de fondo]", e)


def levantar(cmd, log, env=None):
    return subprocess.Popen(cmd, cwd=RAIZ, env=dict(os.environ, PYTHONUTF8="1", **(env or {})),
                            stdout=open(D / log, "w", encoding="utf-8"), stderr=subprocess.STDOUT)
