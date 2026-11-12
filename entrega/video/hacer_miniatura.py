"""Miniatura de YouTube (1280x720, PNG) con Roja y el logo de Tarjeta Roja.

    salida/video/.venv/Scripts/python.exe entrega/video/hacer_miniatura.py

Deja salida/video/tarjeta-roja-miniatura.png (y una copia .jpg de menos de 2 MB, el límite de YouTube).
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c  # noqa: E402


def main():
    if not (c.D / "modelo.vrm").exists():
        sys.exit("Falta salida/video/modelo.vrm")
    shutil.copy(c.AQUI / "miniatura.html", c.D / "miniatura.html")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "--bind", "127.0.0.1", "-d", str(c.D)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    png = c.D / "tarjeta-roja-miniatura.png"
    try:
        time.sleep(1)
        with sync_playwright() as p:
            nav = p.chromium.launch(channel="msedge", args=["--use-angle=d3d11", "--enable-gpu"])
            pg = nav.new_page(viewport={"width": 1280, "height": 720})
            pg.on("pageerror", lambda e: print("[miniatura] error:", e))
            pg.goto("http://127.0.0.1:8766/miniatura.html", wait_until="domcontentloaded", timeout=120000)
            pg.wait_for_function("window.listo === true", timeout=90000)
            pg.evaluate("document.fonts.ready")
            time.sleep(1.5)
            pg.screenshot(path=str(png))
            nav.close()
    finally:
        srv.terminate()
    jpg = png.with_suffix(".jpg")
    subprocess.run([c.FFMPEG, "-y", "-loglevel", "error", "-i", str(png), "-q:v", "2", str(jpg)], check=True)
    print(f"[miniatura] {png} y {jpg} ({jpg.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
