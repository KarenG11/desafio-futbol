"""Arma el video de venta de Tarjeta Roja con Roja, la asistente virtual 3D.

    salida/video/.venv/Scripts/python.exe entrega/video/hacer_video.py

Requisitos (en un entorno aparte, no en requirements.txt): edge-tts, playwright, imageio-ffmpeg; Microsoft Edge
instalado; el modelo VRM en salida/video/modelo.vrm (muestra oficial de pixiv, licencia VRM 1.0 con uso comercial
permitido y sin crédito obligatorio). La app y el partido son los reales: se levantan la API, el simulador oficial y el
motor, y la pantalla del juez se maneja con clics. Deja el video en salida/video/tarjeta-roja-roja.mp4.
"""
import asyncio
import json
import math
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import wave
from array import array
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
D = RAIZ / "salida" / "video"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
PY = shutil.which("py") or "python"            # el Python del proyecto (con FastAPI, etc.)
APP = "http://127.0.0.1:8000"
PIN = "1234"
TASA = 24000
ANTES, ENTRE = 1.0, 0.45                         # silencio inicial y entre tramos (s)
ACELERAR = 30


# --- 1. Voz -----------------------------------------------------------------------------
def voz(guion: dict) -> list:
    async def sintetizar(i, texto):
        mp3 = D / f"tramo{i:02d}.mp3"
        await edge_tts.Communicate(texto, guion["voz"], rate=guion["velocidad"]).save(str(mp3))
        wav = D / f"tramo{i:02d}.wav"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(mp3), "-ac", "1", "-ar", str(TASA), str(wav)], check=True)
        return wav

    async def todos():
        return await asyncio.gather(*(sintetizar(i, s["texto"]) for i, s in enumerate(guion["segmentos"])))

    wavs = asyncio.run(todos())
    muestras, segmentos, t = array("h"), [], 0.0
    muestras.extend([0] * int(ANTES * TASA)); t = ANTES
    for seg, ruta in zip(guion["segmentos"], wavs):
        with wave.open(str(ruta)) as w:
            datos = array("h", w.readframes(w.getnframes()))
        dur = len(datos) / TASA
        segmentos.append({"id": seg["id"], "inicio": round(t, 3), "fin": round(t + dur, 3), "texto": seg["texto"],
                          "frases": frases(seg["texto"])})
        muestras.extend(datos); muestras.extend([0] * int(ENTRE * TASA)); t += dur + ENTRE
    muestras.extend([0] * int(2.5 * TASA))
    with wave.open(str(D / "narracion.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(TASA); w.writeframes(muestras.tobytes())

    paso = TASA // 30
    rms = [math.sqrt(sum(x * x for x in muestras[i:i + paso]) / paso) for i in range(0, len(muestras) - paso, paso)]
    tope = sorted(rms)[int(len(rms) * 0.97)] or 1
    (D / "envolvente.json").write_text(json.dumps([round(min(1.0, r / tope), 3) for r in rms]))
    (D / "linea.json").write_text(json.dumps({"segmentos": segmentos}, ensure_ascii=False))
    print(f"[voz] {len(segmentos)} tramos, {t:.1f} s de narración")
    return segmentos


def frases(texto: str) -> list:
    partes = []
    for f in re.split(r"(?<=[.!?:])\s+", texto):
        while len(f) > 95:
            corte = f.rfind(", ", 0, len(f) // 2 + 20)
            if corte < 30:
                break
            partes.append(f[:corte + 1]); f = f[corte + 2:]
        partes.append(f)
    return partes


# --- 2. Partido real y juez de fondo -------------------------------------------------------
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
                print("[juez de fondo]", e)


def levantar(cmd, log, env=None):
    import os
    return subprocess.Popen(cmd, cwd=RAIZ, env=dict(os.environ, PYTHONUTF8="1", **(env or {})),
                            stdout=open(D / log, "w", encoding="utf-8"), stderr=subprocess.STDOUT)


# --- 3. Grabación --------------------------------------------------------------------------
def grabar(segmentos: list) -> tuple:
    db = D / "plataforma.db"
    for f in (db, D / "registro.jsonl"):
        f.unlink(missing_ok=True)
    base = "sqlite:///salida/video/plataforma.db"
    procesos = [levantar([PY, "-m", "uvicorn", "plataforma.api.app:app", "--port", "8000"], "api.log",
                         {"DATABASE_URL": base, "JUEZ_PIN": PIN}),
                levantar([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1", "-d", str(D)], "http.log")]
    juez = JuezDeFondo()
    inicio = {s["id"]: s for s in segmentos}
    # La escena del juez arranca en t_j: el pedido del minuto 37,5 tiene que llegar ~4 s después y el cambio de turno
    # (minuto 50) cae ~29 s más tarde, dentro del tramo "turno". El partido arranca antes de la narración, en un minuto
    # negativo, y la narración se larga recién cuando el minuto real del simulador lo permite.
    t_j = inicio["juez"]["inicio"]
    seg_por_min = 60 / ACELERAR
    objetivo = 37.6
    try:
        time.sleep(4)
        with sync_playwright() as p:
            nav = p.chromium.launch(channel="msedge", args=["--use-angle=d3d11", "--enable-gpu", "--autoplay-policy=no-user-gesture-required"])
            ctx = nav.new_context(viewport={"width": 1280, "height": 720}, record_video_dir=str(D / "crudo"),
                                  record_video_size={"width": 1280, "height": 720})
            t_rec = time.monotonic()
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: print("[escena] error:", e))
            pg.goto("http://127.0.0.1:8765/escenario.html")
            pg.wait_for_function("window.listo === true", timeout=90000)
            pg.evaluate(f"escena('{APP}/', 'pantalla', 'Portada')")
            time.sleep(3)

            previa = 6.0
            procesos.append(levantar([PY, "simulador/servidor.py", "--acelerar", str(ACELERAR), "--puerto", "8090",
                                      "--inicio-min", f"{objetivo - (t_j + 4 + previa) / seg_por_min:.2f}",
                                      "--log", "salida/video/registro.jsonl"], "simulador.log"))
            while True:
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8090/estado", timeout=2) as r:
                        m1 = float(json.loads(r.read())["minuto_actual"]); t1 = time.monotonic(); break
                except Exception:
                    time.sleep(0.2)
            procesos.append(levantar([PY, "-m", "plataforma.motor", "--sim", "http://127.0.0.1:8090", "--db", base,
                                      "--auditoria", "salida/video/auditoria.jsonl", "--publico", "salida/video/publico.json"],
                                     "motor.log"))
            juez.start()
            t_inicio = t1 + (objetivo - m1) * seg_por_min - t_j - 4
            print(f"[partido] simulador en el minuto {m1:.2f}; la narración arranca en {t_inicio - time.monotonic():.1f} s", flush=True)
            time.sleep(max(0.0, t_inicio - time.monotonic()))
            pg.evaluate("iniciar()")
            t0 = time.monotonic()
            app = pg.frame_locator("#app")

            def ir(sel, bloque="start"):
                try:
                    app.locator(sel).first.evaluate(f"e => e.scrollIntoView({{behavior: 'smooth', block: '{bloque}'}})", timeout=4000)
                except Exception as e:
                    print("[escena] scroll", sel, e)

            def esperar(hasta, cada=None):
                while time.monotonic() - t0 < hasta:
                    if cada:
                        cada()
                    time.sleep(0.3)

            def firmar_en_pantalla():
                try:
                    if app.locator("#pin").is_visible(timeout=200):
                        app.locator("#pin").fill(PIN); app.locator("#form-pin button[type=submit]").click(timeout=1000)
                    b = app.locator("#firmar-todos")
                    if b.is_visible(timeout=200) and b.is_enabled(timeout=200):
                        time.sleep(3.0); b.click(timeout=1000)
                        print(f"[escena] el juez firmó en la pantalla (t={time.monotonic() - t0:.1f} s)", flush=True)
                    asumir = app.get_by_role("button", name=re.compile("Asumir turno"))
                    if asumir.count() and asumir.first.is_visible(timeout=200):
                        time.sleep(1.0); asumir.first.click(timeout=1000)
                        print(f"[escena] el juez asumió el turno (t={time.monotonic() - t0:.1f} s)", flush=True)
                except Exception:
                    pass

            for seg in segmentos:
                esperar(seg["inicio"] - 0.4)
                i = seg["id"]
                if i == "portada":
                    pg.evaluate(f"escena('{APP}/', 'pantalla', 'Portada')")
                elif i == "problema":
                    ir("#t-problema")
                elif i == "monitoreo":
                    pg.evaluate(f"escena('{APP}/monitoreo', 'pantalla', 'Monitoreo en vivo')")
                elif i == "descartados":
                    ir("#t-descartados", "center")
                elif i == "kpis":
                    ir(".kpis", "center")
                elif i == "juez":
                    juez.pausado = True
                    pg.evaluate(f"escena('{APP}/juez/', 'celular', 'Pantalla del juez')")
                elif i == "integridad":
                    juez.pausado = False
                    pg.evaluate(f"escena('{APP}/monitoreo', 'pantalla', 'Auditoría')")
                    esperar(seg["inicio"] + 1.2)
                    ir("#t-integridad", "center")
                elif i == "registro":
                    pg.evaluate(f"escena('{APP}/registro', 'pantalla', 'Registro público')")
                elif i == "resultados":
                    pg.evaluate(f"escena('{APP}/', 'pantalla', 'Resultados')")
                    esperar(seg["inicio"] + 1.0)
                    ir("#t-resultados")
                elif i == "modelo":
                    ir("#t-modelo")
                elif i == "cierre":
                    ir(".heroe", "start")
                if i in ("juez", "juez2", "turno"):
                    esperar(seg["fin"], firmar_en_pantalla)
                elif i == "registro":
                    esperar(seg["inicio"] + 4)
                    try:
                        app.locator("#buscar").press_sequentially("pelotaya", delay=120, timeout=5000)
                    except Exception as e:
                        print("[escena] buscar", e)
            esperar(segmentos[-1]["fin"] + 0.6)
            pg.evaluate("telon('Tarjeta Roja')")
            esperar(segmentos[-1]["fin"] + 2.5)
            desfase = t0 - t_rec
            video = pg.video.path()
            ctx.close(); nav.close()
            return Path(video), desfase
    finally:
        juez.fin = True
        for pr in procesos:
            pr.terminate()


# --- 4. Montaje ----------------------------------------------------------------------------
def montar(video: Path, desfase: float, duracion: float) -> Path:
    salida = D / "tarjeta-roja-roja.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(video), "-i", str(D / "narracion.wav"),
                    "-filter_complex", f"[0:v]trim=start={desfase:.3f},setpts=PTS-STARTPTS[v]",
                    "-map", "[v]", "-map", "1:a", "-t", f"{duracion:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(salida)],
                   check=True)
    return salida


def main():
    D.mkdir(parents=True, exist_ok=True)
    if not (D / "modelo.vrm").exists():
        sys.exit("Falta salida/video/modelo.vrm")
    shutil.copy(AQUI / "escenario.html", D / "escenario.html")
    guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
    segmentos = voz(guion)
    video, desfase = grabar(segmentos)
    salida = montar(video, desfase, segmentos[-1]["fin"] + 2.5)
    print(f"[video] {salida} (desfase {desfase:.2f} s)")


if __name__ == "__main__":
    main()
