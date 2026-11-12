"""python -m plataforma.motor --sim http://localhost:8080 [--juez-automatico] [--exportar entrega]"""
import argparse
import os
from pathlib import Path

from plataforma.motor.motor import Motor


def main() -> None:
    ap = argparse.ArgumentParser(description="Motor de la plataforma (habla con el simulador y escribe la base)")
    ap.add_argument("--sim", default="http://localhost:8080")
    ap.add_argument("--db", default=None, help="DATABASE_URL (por defecto sqlite:///salida/plataforma.db)")
    ap.add_argument("--juez-automatico", action="store_true",
                    help="SOLO PRUEBAS: el juez de turno aprueba pedidos, asume turnos y resuelve reclamos solo")
    ap.add_argument("--auditoria", default="salida/auditoria_interna.jsonl")
    ap.add_argument("--publico", default="salida/registro_publico.json")
    ap.add_argument("--exportar", type=Path, default=None,
                    help="al terminar, escribe expediente-final.json y auditoria-final.jsonl en esa carpeta")
    ap.add_argument("--expediente", default=None, help="expediente a exportar (por defecto el primero)")
    a = ap.parse_args()
    if a.db:
        os.environ["DATABASE_URL"] = a.db
    os.environ.setdefault("DATABASE_URL", "sqlite:///salida/plataforma.db")
    Path("salida").mkdir(exist_ok=True)
    motor = Motor(a.sim, juez_automatico=a.juez_automatico, ruta_auditoria=a.auditoria, ruta_publico=a.publico)
    motor.correr()
    if a.exportar:
        from plataforma.motor.exportar import exportar
        print("[motor] exportado:", exportar(motor.expedientes, Path(a.auditoria), a.exportar, a.expediente))


if __name__ == "__main__":
    main()
