"""Video horizontal (16:9, para proyector) de venta de Tarjeta Roja, menos de 3 minutos, con Roja y la app real.

    salida/video/.venv/Scripts/python.exe entrega/video/hacer_presentacion.py

Requisitos en comun.py. Deja salida/video/tarjeta-roja-presentacion.mp4 (1920x1080).
"""
import json
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hacer_short as hs  # noqa: E402
import comun as hv  # noqa: E402

D, AQUI, APP, PIN = hv.D, hv.AQUI, hv.APP, hv.PIN
ACELERAR, NOMBRE = 30, "presentacion"


def grabar(segmentos: list):
    for f in (D / "plataforma.db", D / "registro.jsonl"):
        f.unlink(missing_ok=True)
    base = "sqlite:///salida/video/plataforma.db"
    procesos = [hv.levantar([hv.PY, "-m", "uvicorn", "plataforma.api.app:app", "--port", "8000"], "api.log",
                            {"DATABASE_URL": base, "JUEZ_PIN": PIN}),
                hv.levantar([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1", "-d", str(D)], "http.log")]
    juez = hv.JuezDeFondo()
    S = {s["id"]: s for s in segmentos}
    # El pedido real del minuto 37,6 tiene que llegar ~3 s después de que empieza la escena del juez.
    t_j, seg_min, objetivo, previa = S["firma"]["inicio"], 60 / ACELERAR, 37.6, 6.0
    try:
        time.sleep(4)
        with sync_playwright() as p:
            nav = p.chromium.launch(channel="msedge", args=["--use-angle=d3d11", "--enable-gpu"])
            ctx = nav.new_context(viewport={"width": 1280, "height": 720}, record_video_dir=str(D / "crudo_presentacion"),
                                  record_video_size={"width": 1280, "height": 720})
            t_rec = time.monotonic()
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: print("[escena] error:", e))
            pg.goto("http://127.0.0.1:8765/escenario_presentacion.html", wait_until="domcontentloaded", timeout=120000)
            pg.wait_for_function("window.listo === true", timeout=90000)
            pg.evaluate(f"app('{APP}/', 'navegador', 'tarjetaroja.ar')")
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
            ev = pg.evaluate

            def esperar(hasta, cada=None):
                while time.monotonic() - t0 < hasta:
                    if cada:
                        cada()
                    time.sleep(0.15)

            def palabra(seg_id, n):
                ps = S[seg_id]["palabras"]
                return ps[min(n, len(ps) - 1)]["t"]

            def inicio(seg_id, antes=0.1):
                esperar(S[seg_id]["inicio"] - antes)

            def ir(sel, bloque="start"):
                try:
                    app.locator(sel).first.evaluate(f"e => e.scrollIntoView({{block: '{bloque}'}})", timeout=3000)
                except Exception as e:
                    print("[escena] ir", sel, e)

            def resaltar(sel, texto=None, blanca=False):
                try:
                    caja = app.locator(sel).first.bounding_box(timeout=3000)
                    v = ev("(() => { const r = document.getElementById('app').getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })()")
                except Exception as e:
                    print("[escena] resaltar", sel, e); return
                if not caja:
                    return
                x = max(caja["x"], v[0] + 4); y = max(caja["y"], v[1] + 4)
                w = min(caja["x"] + caja["width"], v[0] + v[2] - 4) - x; h = min(caja["y"] + caja["height"], v[1] + v[3] - 4) - y
                if w > 10 and h > 10:
                    ev(f"resaltar({x}, {y}, {w}, {h})")
                    if texto:
                        ev(f"pildora({json.dumps(texto)}, {min(x + w - 80, 1060)}, {min(y + h - 8, 540)}, {str(blanca).lower()})")

            firmado = {"si": False}

            def firmar():
                try:
                    if app.locator("#pin").is_visible(timeout=100):
                        juez = (hv.api("/api/estado").get("jueces_de_turno") or [None])[0]
                        if juez and app.locator(f"#usuario option[value='{juez}']").count():
                            app.locator("#usuario").select_option(juez); app.locator("#pin").fill(hv.clave_de(juez))
                            app.locator("#form-pin button[type=submit]").click(timeout=800)
                    b = app.locator("#firmar-todos")
                    if not firmado["si"] and b.is_visible(timeout=100) and b.is_enabled(timeout=100):
                        resaltar(".pedido")
                        time.sleep(2.0); b.evaluate("b => b.click()"); firmado["si"] = True
                        ev("limpiar(); pildora('Firmado ✓', 1020, 520)")
                        print(f"[escena] firmó en la pantalla (t={time.monotonic() - t0:.1f})", flush=True)
                except Exception:
                    pass

            tab = []

            def tilda(item):
                tab.append(item); ev(f"tablilla({json.dumps(tab, ensure_ascii=False)})")

            # 01 gancho y problema
            ev("pose('saluda')")
            esperar(palabra("gancho", 9)); ev("sello('Pirata')")
            inicio("problema"); ev("limpiar(); pose('abre')")
            esperar(palabra("problema", 4)); ev("relojito('2 h', 'de partido')")
            esperar(palabra("problema", 11)); ev("pildora('cambia en minutos', 800, 470)")
            esperar(palabra("problema", 17)); ev("pildora('oficios · mails', 560, 520, true)")
            # 02 solución
            inicio("solucion", 0.45); ev("transicion('franjas')"); inicio("solucion", 0.05)
            ev("limpiar(); quitar('reloj'); pose('festeja')")
            esperar(palabra("solucion", 5)); ev("pildora('Observa', 560, 470); pildora('Analiza', 760, 470); pildora('Actúa', 950, 470)")
            # 03 en cancha
            inicio("cancha"); ev(f"limpiar(); app('{APP}/partido', 'navegador', 'tarjetaroja.ar/partido'); pose('senala')")
            esperar(S["cancha"]["inicio"] + 1.2); resaltar("#rojas", "piratas expulsados")
            esperar(palabra("cancha", 12))
            try:
                n = int(re.findall(r"\d+", app.locator("#d-expulsados").inner_text(timeout=1000))[0])
            except Exception:
                n = 3
            ev(f"rojas({max(1, min(n, 6))})")
            # 04 observa
            inicio("observa", 0.45); ev("transicion('puntos')"); inicio("observa", 0.05)
            ev(f"limpiar(); quitar('rojas'); app('{APP}/monitoreo', 'navegador', 'tarjetaroja.ar/monitoreo'); paso(0); pose('senala')")
            tilda("Detecta")
            esperar(palabra("observa", 12)); ir("#t-descartados", "center"); time.sleep(0.4); resaltar("#descartados .descartado", "descartado solo")
            # 05 analiza
            inicio("analiza"); ev("limpiar(); paso(1); pose('abre')"); ir("#t-streams"); time.sleep(0.4)
            resaltar("#streams .medalla--cian", "solo el nombre")
            esperar(palabra("analiza", 12)); ev("pildora('0 sitios legítimos', 560, 520)")
            # 06 evidencia
            inicio("evidencia"); ev("limpiar(); pose('senala')"); tilda("Expediente")
            ir("#t-integridad", "center"); time.sleep(0.4); resaltar("#integridad", "cadena íntegra")
            # 07 firma (pedido real)
            juez.pausado = True
            inicio("firma", 0.45); ev("transicion('franjas')"); inicio("firma", 0.05)
            ev(f"limpiar(); app('{APP}/juez/', 'celular'); paso(2); pose('arriba')")
            esperar(S["firma"]["fin"] + 0.3, firmar)
            tilda("Firma")
            juez.pausado = False
            # 08 actúa
            inicio("actua"); ev(f"limpiar(); app('{APP}/monitoreo', 'navegador', 'tarjetaroja.ar/monitoreo'); paso(3); pose('senala')")
            esperar(S["actua"]["inicio"] + 1.0); ir("#t-streams"); time.sleep(0.4); resaltar("#streams .stream .proveedores")
            esperar(palabra("actua", 4)); ev("sello('Bloqueado'); pose('festeja')"); tilda("Bloquea")
            esperar(palabra("actua", 12)); ev("limpiar(); pildora('reintento automático', 760, 470)")
            # 09 velocidad
            inicio("velocidad"); ev("limpiar(); pose('abre')"); resaltar("#streams .stream__tiempo", "al primer bloqueo")
            esperar(palabra("velocidad", 9)); ev("relojito(\"<1'\", 'al bloqueo')")
            # 10 registro
            inicio("registro", 0.45); ev("transicion('puntos')"); inicio("registro", 0.05)
            ev(f"limpiar(); quitar('reloj'); app('{APP}/registro', 'navegador', 'tarjetaroja.ar/registro'); paso(4); pose('senala')")
            tilda("Vence")
            esperar(S["registro"]["inicio"] + 1.5)
            try:
                ir("#buscar", "center"); app.locator("#buscar").press_sequentially("pelotaya", delay=110, timeout=5000)
            except Exception as e:
                print("[escena] buscar", e)
            time.sleep(0.5); resaltar("#entradas .entrada", "quién · por qué · hasta cuándo")
            # 11 resultados
            inicio("resultados"); ev(f"limpiar(); paso(null); app('{APP}/', 'navegador', 'tarjetaroja.ar'); pose('festeja')")
            esperar(S["resultados"]["inicio"] + 0.8); ir("#t-resultados")
            esperar(palabra("resultados", 9)); ev("sello('7 de 7')")
            esperar(palabra("resultados", 14)); ev("limpiar(); pildora('≈ 3 %', 820, 470)")
            esperar(palabra("resultados", 19)); ev("pildora('0 sitios legítimos', 620, 520)")
            # 12 modelo
            inicio("modelo"); ev("limpiar(); pose('abre')"); ir("#t-modelo")
            esperar(palabra("modelo", 13)); time.sleep(0.2); resaltar(".precio--destacado", "paga el titular")
            esperar(palabra("modelo", 18)); ev("pildora('juzgados y proveedores: gratis', 640, 520, true)")
            # 13 cierre
            inicio("cierre", 0.45); ev("transicion('franjas')"); inicio("cierre", 0.05)
            ev(f"limpiar(); quitar('tablilla'); app('{APP}/partidos', 'navegador', 'tarjetaroja.ar/partidos'); pose('saluda')")
            esperar(S["cierre"]["fin"] + 0.5); ev("telon()")
            esperar(S["cierre"]["fin"] + 3.0)
            desbordes = pg.evaluate("window.desbordes")
            print(f"[bordes] {len(desbordes)} indicador(es) tocan el borde", flush=True)
            for x in desbordes:
                print(f"  t={x['t']} s {x['k']} {x['r']}", flush=True)
            desfase = t0 - t_rec
            video = Path(pg.video.path())
            ctx.close(); nav.close()
            return video, desfase
    finally:
        juez.fin = True
        for pr in procesos:
            pr.terminate()


def main():
    D.mkdir(parents=True, exist_ok=True)
    if not (D / "modelo.vrm").exists():
        sys.exit("Falta salida/video/modelo.vrm")
    shutil.copy(AQUI / "escenario_presentacion.html", D / "escenario_presentacion.html")
    guion = json.loads((AQUI / "guion_presentacion.json").read_text(encoding="utf-8"))
    segmentos = hs.voz(guion, NOMBRE)
    duracion = segmentos[-1]["fin"] + 3.0
    if duracion >= 180:
        sys.exit(f"El guion dura {duracion:.0f} s: tiene que ser menos de 3 minutos")
    video, desfase = grabar(segmentos)
    print(f"[video] {hs.montar(video, desfase, duracion, NOMBRE, '1920:1080')} ({duracion:.0f} s, desfase {desfase:.2f} s)")


if __name__ == "__main__":
    main()
