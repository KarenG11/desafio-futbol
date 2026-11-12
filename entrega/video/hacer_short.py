"""Short vertical (9:16) de Tarjeta Roja con Roja, al estilo de referencia: titular palabra por palabra, ventana con la
app real, resaltados, sellos, stickers y transiciones de franjas y semitono.

    salida/video/.venv/Scripts/python.exe entrega/video/hacer_short.py

Mismos requisitos que hacer_video.py. Deja salida/video/tarjeta-roja-short.mp4 (1080x1920).
"""
import asyncio
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import wave
from array import array
from pathlib import Path

import edge_tts
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hacer_video as hv  # noqa: E402

D, AQUI, APP, PIN, TASA, FFMPEG = hv.D, hv.AQUI, hv.APP, hv.PIN, hv.TASA, hv.FFMPEG
ANTES, ENTRE, ACELERAR = 0.6, 0.35, 30


def palabras_de(texto: str):
    """[(palabra visible, es_clave)] respetando *marcas*; las marcas pueden abarcar varias palabras."""
    out, clave = [], False
    for token in texto.split():
        empieza, termina = token.startswith("*"), token.rstrip(".,;:!?").endswith("*")
        if empieza:
            clave = True
        out.append((token.replace("*", ""), clave))
        if termina:
            clave = False
    return out


def voz(guion: dict) -> list:
    async def sintetizar(i, seg):
        limpio = seg["texto"].replace("*", "")
        com = edge_tts.Communicate(limpio, guion["voz"], rate=guion["velocidad"], boundary="WordBoundary")
        audio, marcas = bytearray(), []
        async for ch in com.stream():
            if ch["type"] == "audio":
                audio.extend(ch["data"])
            elif ch["type"] == "WordBoundary":
                marcas.append(ch["offset"] / 1e7)
        mp3 = D / f"short{i:02d}.mp3"
        mp3.write_bytes(bytes(audio))
        wav = D / f"short{i:02d}.wav"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(mp3), "-ac", "1", "-ar", str(TASA), str(wav)], check=True)
        return wav, marcas

    async def todos():
        return await asyncio.gather(*(sintetizar(i, s) for i, s in enumerate(guion["segmentos"])))

    resultados = asyncio.run(todos())
    muestras, segmentos, t = array("h", [0] * int(ANTES * TASA)), [], ANTES
    for seg, (ruta, marcas) in zip(guion["segmentos"], resultados):
        with wave.open(str(ruta)) as w:
            datos = array("h", w.readframes(w.getnframes()))
        dur = len(datos) / TASA
        ps = palabras_de(seg["texto"])
        if len(marcas) != len(ps):     # números o símbolos leídos como varias palabras: reparto proporcional
            marcas = [dur * k / len(ps) for k in range(len(ps))]
        segmentos.append({"id": seg["id"], "etiqueta": seg["etiqueta"], "inicio": round(t, 3), "fin": round(t + dur, 3),
                          "palabras": [{"t": round(t + m, 3), "texto": p, "clave": c} for (p, c), m in zip(ps, marcas)]})
        muestras.extend(datos); muestras.extend([0] * int(ENTRE * TASA)); t += dur + ENTRE
    muestras.extend([0] * int(2.2 * TASA))
    with wave.open(str(D / "narracion_short.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(TASA); w.writeframes(muestras.tobytes())
    paso = TASA // 30
    rms = [(sum(x * x for x in muestras[i:i + paso]) / paso) ** 0.5 for i in range(0, len(muestras) - paso, paso)]
    tope = sorted(rms)[int(len(rms) * 0.97)] or 1
    (D / "envolvente.json").write_text(json.dumps([round(min(1.0, r / tope), 3) for r in rms]))
    (D / "linea.json").write_text(json.dumps({"segmentos": segmentos}, ensure_ascii=False))
    print(f"[voz] {len(segmentos)} tramos, {t:.1f} s", flush=True)
    return segmentos


def grabar(segmentos: list):
    for f in (D / "plataforma.db", D / "registro.jsonl"):
        f.unlink(missing_ok=True)
    base = "sqlite:///salida/video/plataforma.db"
    procesos = [hv.levantar([hv.PY, "-m", "uvicorn", "plataforma.api.app:app", "--port", "8000"], "api.log",
                            {"DATABASE_URL": base, "JUEZ_PIN": PIN}),
                hv.levantar([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1", "-d", str(D)], "http.log")]
    juez = hv.JuezDeFondo()
    S = {s["id"]: s for s in segmentos}
    t_j, seg_min, objetivo, previa = S["firma"]["inicio"], 60 / ACELERAR, 37.6, 6.0
    try:
        time.sleep(4)
        with sync_playwright() as p:
            nav = p.chromium.launch(channel="msedge", args=["--use-angle=d3d11", "--enable-gpu"])
            ctx = nav.new_context(viewport={"width": 720, "height": 1280}, record_video_dir=str(D / "crudo_short"),
                                  record_video_size={"width": 720, "height": 1280})
            t_rec = time.monotonic()
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: print("[escena] error:", e))
            pg.goto("http://127.0.0.1:8765/escenario_short.html")
            pg.wait_for_function("window.listo === true", timeout=90000)
            pg.evaluate(f"app('{APP}/partidos', 'navegador', 'tarjetaroja.ar/partidos')")

            procesos.append(hv.levantar([hv.PY, "simulador/servidor.py", "--acelerar", str(ACELERAR), "--puerto", "8090",
                                         "--inicio-min", f"{objetivo - (t_j + 1.5 + previa) / seg_min:.2f}",
                                         "--log", "salida/video/registro.jsonl"], "simulador.log"))
            while True:
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8090/estado", timeout=2) as r:
                        m1 = float(json.loads(r.read())["minuto_actual"]); t1 = time.monotonic(); break
                except Exception:
                    time.sleep(0.2)
            procesos.append(hv.levantar([hv.PY, "-m", "plataforma.motor", "--sim", "http://127.0.0.1:8090", "--db", base,
                                         "--auditoria", "salida/video/auditoria.jsonl", "--publico", "salida/video/publico.json"], "motor.log"))
            juez.start()
            t_ini = t1 + (objetivo - m1) * seg_min - t_j - 1.5
            print(f"[partido] minuto {m1:.2f}; arranca en {t_ini - time.monotonic():.1f} s", flush=True)
            time.sleep(max(0.0, t_ini - time.monotonic()))
            pg.evaluate("iniciar()")
            t0 = time.monotonic()
            app = pg.frame_locator("#app")

            def esperar(hasta, cada=None):
                while time.monotonic() - t0 < hasta:
                    if cada:
                        cada()
                    time.sleep(0.15)

            def palabra(seg_id, n):
                ps = S[seg_id]["palabras"]
                return ps[min(n, len(ps) - 1)]["t"]

            def ir(sel, bloque="start"):
                try:
                    app.locator(sel).first.evaluate(f"e => e.scrollIntoView({{block: '{bloque}'}})", timeout=3000)
                except Exception as e:
                    print("[escena] ir", sel, e)

            def resaltar(sel, texto=None, blanca=False, dx=0, dy=0):
                try:
                    caja = app.locator(sel).first.bounding_box(timeout=3000)
                    v = pg.evaluate("(() => { const r = document.getElementById('app').getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })()")
                except Exception as e:
                    print("[escena] resaltar", sel, e); return
                if not caja:
                    return
                x = max(caja["x"], v[0] + 4); y = max(caja["y"], v[1] + 4)
                w = min(caja["x"] + caja["width"], v[0] + v[2] - 4) - x; h = min(caja["y"] + caja["height"], v[1] + v[3] - 4) - y
                if w > 10 and h > 10:
                    pg.evaluate(f"resaltar({x}, {y}, {w}, {h})")
                    if texto:
                        pg.evaluate(f"pildora({json.dumps(texto)}, {min(x + w - 60 + dx, 520)}, {y + h - 8 + dy}, {str(blanca).lower()})")

            firmado = {"si": False}

            def firmar():
                try:
                    if app.locator("#pin").is_visible(timeout=100):
                        app.locator("#pin").fill(PIN); app.locator("#form-pin button[type=submit]").click(timeout=800)
                    b = app.locator("#firmar-todos")
                    if not firmado["si"] and b.is_visible(timeout=100) and b.is_enabled(timeout=100):
                        resaltar(".pedido")
                        time.sleep(1.4); b.evaluate("b => b.click()"); firmado["si"] = True
                        pg.evaluate("limpiar(); pildora('Firmado ✓', 330, 700)")
                        print(f"[escena] firmó en la pantalla (t={time.monotonic() - t0:.1f})", flush=True)
                except Exception:
                    pass

            # --- 01 problema
            pg.evaluate("pose('saluda')")
            esperar(palabra("problema", 4)); pg.evaluate("relojito('2 h', 'de partido')")
            esperar(palabra("problema", 9)); pg.evaluate("pose('abre')"); resaltar(".encuentro--vivo", "en vivo")
            # --- 02 marca
            esperar(S["marca"]["inicio"] - 0.45); pg.evaluate("transicion('franjas')"); esperar(S["marca"]["inicio"] - 0.05)
            pg.evaluate(f"limpiar(); quitar('reloj'); app('{APP}/', 'navegador', 'tarjetaroja.ar'); pose('festeja')")
            esperar(palabra("marca", 3)); pg.evaluate("pildora('tarjetaroja.ar', 210, 690, true)")
            # --- 03 detecta
            esperar(S["detecta"]["inicio"] - 0.1)
            pg.evaluate(f"limpiar(); app('{APP}/partido', 'navegador', 'tarjetaroja.ar/partido'); paso(0); pose('senala'); tablilla(['Detecta'])")
            esperar(S["detecta"]["inicio"] + 1.2); ir("#t-tarjetas"); time.sleep(0.4); resaltar("#tarjetas .evento--ambar", "Marca de agua ✓")
            esperar(palabra("detecta", 7)); pg.evaluate("paso(1); tablilla(['Detecta', 'Expediente'])")
            # --- 04 firma (el pedido real del minuto 37,6 llega ~1,5 s después)
            juez.pausado = True
            esperar(S["firma"]["inicio"] - 0.1)
            pg.evaluate(f"limpiar(); app('{APP}/juez/', 'celular'); paso(2); pose('arriba')")
            esperar(S["firma"]["fin"] + 0.2, firmar)
            pg.evaluate("tablilla(['Detecta', 'Expediente', 'Firma'])")
            juez.pausado = False
            # --- 05 bloquea
            esperar(S["bloquea"]["inicio"] - 0.1)
            pg.evaluate(f"limpiar(); app('{APP}/monitoreo', 'navegador', 'tarjetaroja.ar/monitoreo'); paso(3); pose('senala')")
            esperar(S["bloquea"]["inicio"] + 1.0); ir("#t-streams"); time.sleep(0.4); resaltar("#streams .stream .proveedores")
            esperar(palabra("bloquea", 4)); pg.evaluate("sello('Bloqueado'); pose('festeja'); tablilla(['Detecta', 'Expediente', 'Firma', 'Bloquea'])")
            esperar(palabra("bloquea", 8)); pg.evaluate("relojito(\"<1'\", 'al bloqueo')")
            # --- 06 colateral
            esperar(S["colateral"]["inicio"] - 0.1)
            pg.evaluate("limpiar(); pose('abre')")
            resaltar("#streams .medalla--cian", "solo el nombre")
            esperar(palabra("colateral", 9)); pg.evaluate("pildora('0 sitios legítimos', 200, 690)")
            # --- 07 tarjetas
            esperar(S["tarjetas"]["inicio"] - 0.45); pg.evaluate("transicion('puntos')"); esperar(S["tarjetas"]["inicio"] - 0.05)
            pg.evaluate(f"limpiar(); quitar('reloj'); paso(null); app('{APP}/partido', 'navegador', 'tarjetaroja.ar/partido'); pose('saluda')")
            esperar(S["tarjetas"]["inicio"] + 0.8); resaltar("#rojas", None)
            esperar(palabra("tarjetas", 5))
            try:
                n = int(re.findall(r"\d+", app.locator("#d-expulsados").inner_text(timeout=1000))[0])
            except Exception:
                n = 4
            pg.evaluate(f"rojas({max(1, min(n, 6))})")
            # --- 08 resultado
            esperar(S["resultado"]["inicio"] - 0.1)
            pg.evaluate(f"limpiar(); quitar('rojas'); app('{APP}/', 'navegador', 'tarjetaroja.ar'); paso(4); pose('festeja'); tablilla(['Detecta', 'Expediente', 'Firma', 'Bloquea', 'Vence'])")
            esperar(S["resultado"]["inicio"] + 0.7); ir("#t-resultados"); time.sleep(0.3)
            esperar(palabra("resultado", 2)); pg.evaluate("sello('7 de 7')")
            # --- 09 cierre
            esperar(S["cierre"]["inicio"] - 0.45); pg.evaluate("transicion('franjas')"); esperar(S["cierre"]["inicio"] - 0.05)
            pg.evaluate(f"limpiar(); paso(null); quitar('tablilla'); app('{APP}/juez/demo.html', 'navegador', 'tarjetaroja.ar/demo'); pose('saluda')")
            esperar(palabra("cierre", 5)); pg.evaluate("pildora('tarjetaroja.ar/demo', 170, 690, true)")
            esperar(S["cierre"]["fin"] + 0.5); pg.evaluate("telon()")
            esperar(S["cierre"]["fin"] + 2.2)
            desfase = t0 - t_rec
            video = Path(pg.video.path())
            ctx.close(); nav.close()
            return video, desfase
    finally:
        juez.fin = True
        for pr in procesos:
            pr.terminate()


def montar(video: Path, desfase: float, duracion: float) -> Path:
    salida = D / "tarjeta-roja-short.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(video), "-i", str(D / "narracion_short.wav"),
                    "-filter_complex", f"[0:v]trim=start={desfase:.3f},setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos[v]",
                    "-map", "[v]", "-map", "1:a", "-t", f"{duracion:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(salida)], check=True)
    return salida


def main():
    D.mkdir(parents=True, exist_ok=True)
    if not (D / "modelo.vrm").exists():
        sys.exit("Falta salida/video/modelo.vrm")
    shutil.copy(AQUI / "escenario_short.html", D / "escenario_short.html")
    guion = json.loads((AQUI / "guion_short.json").read_text(encoding="utf-8"))
    segmentos = voz(guion)
    video, desfase = grabar(segmentos)
    print(f"[video] {montar(video, desfase, segmentos[-1]['fin'] + 2.2)} (desfase {desfase:.2f} s)")


if __name__ == "__main__":
    main()
