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
    ap.add_argument("--red", action="store_true",
                    help="escuchar en toda la red (0.0.0.0) para entrar desde el celular; exige JUEZ_PIN de 8+ caracteres")
    ap.add_argument("--juez-automatico", action="store_true",
                    help="SOLO PRUEBAS: el juez de turno aprueba, asume turnos y resuelve reclamos solo")
    ap.add_argument("--auditoria", default="salida/auditoria_interna.jsonl")
    ap.add_argument("--publico", default="salida/registro_publico.json")
    ap.add_argument("--exportar", type=Path, default=None)
    ap.add_argument("--base", action="store_true", help="usar la base de DATABASE_URL (es lo que pasa sin --local)")
    ap.add_argument("--sin-web", action="store_true", help="solo el motor, sin API ni pantalla (Vercel Sandbox)")
    ap.add_argument("--exportar-entrega", action="store_true", help="igual que --exportar entrega")
    a = ap.parse_args()
    if a.exportar_entrega and a.exportar is None:
        a.exportar = Path("entrega")
    Path("salida").mkdir(exist_ok=True)
    if a.local:
        os.environ["DATABASE_URL"] = "sqlite:///salida/plataforma.db"
        if not a.red:
            os.environ.setdefault("JUEZ_PIN", "1234")
    elif not os.environ.get("DATABASE_URL"):
        ap.error("sin --local hace falta DATABASE_URL")
    if a.red and not a.sin_web:
        pin = os.environ.get("JUEZ_PIN", "")
        if len(pin) < 8 or pin == "1234":
            ap.error("con --red hace falta JUEZ_PIN de al menos 8 caracteres (el 1234 de demo es solo para esta máquina)")

    import uvicorn
    from plataforma.motor.motor import Motor

    motor = Motor(a.sim, juez_automatico=a.juez_automatico, ruta_auditoria=a.auditoria, ruta_publico=a.publico)
    api = uvicorn.Server(uvicorn.Config("plataforma.api.app:app", host="0.0.0.0" if a.red else "127.0.0.1", port=a.puerto, log_level="warning"))
    if not a.sin_web:
        threading.Thread(target=api.run, daemon=True).start()
        print(f"[main] web del juez: http://localhost:{a.puerto}/juez/  (cada juez entra con su usuario y contraseña)")
        if os.environ.get("JUEZ_PIN") == "1234":   # solo el secreto de demo local: en un deploy real no se imprimen
            from plataforma.claves import clave_de
            import json
            for jz in json.loads((Path(__file__).resolve().parents[1] / "datos" / "juzgados.json").read_text(encoding="utf-8"))["juzgados"]:
                for j in jz["jueces"]:
                    print(f"[main]   {j.get('nombre', j['id'])}: usuario {j['id']}  contraseña {clave_de(j['id'])}")
    motor.correr()
    if a.exportar:
        from plataforma.motor.exportar import exportar
        print("[main] exportado:", exportar(motor.expedientes, Path(a.auditoria), a.exportar))
    api.should_exit = True


if __name__ == "__main__":
    main()
