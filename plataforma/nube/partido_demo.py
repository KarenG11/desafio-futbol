"""Corre un partido completo DENTRO del Vercel Sandbox y deja el resultado en la base.

    python -m plataforma.nube.partido_demo                     # simulador de práctica + motor, aprueba el juez desde la web
    DEMO_JUEZ_AUTOMATICO=1 python -m plataforma.nube.partido_demo   # aprueba solo (para mostrar el circuito sin juez)

Variables: DATABASE_URL (obligatoria, la de Neon), DEMO_ACELERAR (por defecto 6) y DEMO_SIM (si viene, no levanta el
simulador local y se conecta a esa dirección: modo partido final).
Al terminar corre evaluacion/verificar.py y guarda la salida en la tabla verificaciones.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
REGISTRO = RAIZ / "salida" / "registro.jsonl"
PUERTO_SIM = int(os.environ.get("DEMO_PUERTO_SIM", "8080"))
TOPE_S = 40 * 60          # nunca más de 40 minutos reales (la sesión de Hobby dura 45)


def log(msg: str) -> None:
    print(f"[demo] {msg}", flush=True)


def main() -> int:
    if not os.environ.get("DATABASE_URL"):
        log("Falta DATABASE_URL.")
        return 2
    env = dict(os.environ, PYTHONUTF8="1")
    acelerar = os.environ.get("DEMO_ACELERAR", "6")
    sim_externo = os.environ.get("DEMO_SIM")
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)

    sim = None
    if sim_externo:
        url_sim = sim_externo
        log(f"Modo final: motor contra {url_sim}")
    else:
        url_sim = f"http://localhost:{PUERTO_SIM}"
        sim = subprocess.Popen([sys.executable, "simulador/servidor.py", "--acelerar", acelerar,
                                "--puerto", str(PUERTO_SIM), "--log", str(REGISTRO)], cwd=RAIZ, env=env)
        log(f"Simulador de práctica levantado a x{acelerar}")
        time.sleep(3)

    args_motor = [sys.executable, "-m", "plataforma.main", "--sim", url_sim, "--base", "--sin-web"]
    if os.environ.get("DEMO_JUEZ_AUTOMATICO") == "1":
        args_motor.append("--juez-automatico")
    motor = subprocess.Popen(args_motor, cwd=RAIZ, env=env)
    log("Motor conectado a la base: la web de Vercel ya muestra el partido")

    inicio = time.monotonic()
    while motor.poll() is None and time.monotonic() - inicio < TOPE_S:
        time.sleep(5)
    if motor.poll() is None:
        log("Se cumplió el tope de tiempo: corto el motor")
        motor.terminate()

    if sim is not None:
        # El simulador escribe ventana_cerrada en fin + 5 min de gracia; el motor cierra medio minuto después.
        sim.terminate()
        salida = subprocess.run([sys.executable, "evaluacion/verificar.py", "--log", str(REGISTRO)],
                                cwd=RAIZ, env=env, capture_output=True, text=True).stdout
        from plataforma import db
        partido = db.partido_actual()
        if partido:
            db.guardar_verificacion(partido, salida)
            log(f"Verificador guardado para {partido}")
        print(salida, flush=True)
    try:   # libera el lugar de demo que reservó POST /api/demo/iniciar
        from plataforma.nube.rutas import _liberar
        _liberar()
    except Exception as e:
        log(f"No pude liberar la reserva (vence sola a los 45 min): {e}")
    log("Listo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
