"""Plataforma completa en una sola terminal: motor + API/web del juez.

    python -m plataforma.main --sim http://localhost:8080 --local [--juez-automatico] [--puerto 8000]

--local usa SQLite en salida/plataforma.db (sin --local se usa DATABASE_URL, p. ej. Postgres).
La web del juez queda en http://localhost:<puerto>/juez/ y el registro público en /api/publico.
"""
import argparse
import os
import threading
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Motor + API de la plataforma")
    ap.add_argument("--sim", default="http://localhost:8080")
    ap.add_argument("--local", action="store_true", help="base SQLite local en salida/plataforma.db")
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--juez-automatico", action="store_true",
                    help="SOLO PRUEBAS: el juez de turno aprueba, asume turnos y resuelve reclamos solo")
    ap.add_argument("--auditoria", default="salida/auditoria_interna.jsonl")
    ap.add_argument("--publico", default="salida/registro_publico.json")
    ap.add_argument("--exportar", type=Path, default=None)
    a = ap.parse_args()
    Path("salida").mkdir(exist_ok=True)
    if a.local:
        os.environ["DATABASE_URL"] = "sqlite:///salida/plataforma.db"
        os.environ.setdefault("JUEZ_PIN", "1234")
    elif not os.environ.get("DATABASE_URL"):
        ap.error("sin --local hace falta DATABASE_URL")

    import uvicorn
    from plataforma.motor.motor import Motor

    motor = Motor(a.sim, juez_automatico=a.juez_automatico, ruta_auditoria=a.auditoria, ruta_publico=a.publico)
    api = uvicorn.Server(uvicorn.Config("plataforma.api.app:app", host="0.0.0.0", port=a.puerto, log_level="warning"))
    threading.Thread(target=api.run, daemon=True).start()
    print(f"[main] web del juez: http://localhost:{a.puerto}/juez/  (PIN: variable JUEZ_PIN; con --local, 1234 si no está definida)")
    motor.correr()
    if a.exportar:
        from plataforma.motor.exportar import exportar
        print("[main] exportado:", exportar(motor.expedientes, Path(a.auditoria), a.exportar))
    api.should_exit = True


if __name__ == "__main__":
    main()
