"""Plataforma completa en una notebook: motor + API + pantalla del juez.

    python -m plataforma.main --sim http://localhost:8080                      # aprueba un juez desde /juez
    python -m plataforma.main --sim http://localhost:8080 --juez-automatico    # solo para pruebas aceleradas
    python -m plataforma.main --sim URL --exportar-entrega                     # al cerrar, copia a entrega/

La pantalla del juez queda en http://localhost:8000/juez/. El PIN sale de la variable JUEZ_PIN o, si no está, se genera
al azar y se imprime al arrancar. Con --red escucha en toda la red local (para entrar desde el celular por wifi).
"""
import argparse
import os
import secrets
import sys
import threading
from pathlib import Path

import uvicorn

from plataforma.motor.api import crear_app
from plataforma.motor.motor import RAIZ, Motor


def main() -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Plataforma federal de órdenes de bloqueo en vivo")
    p.add_argument("--sim", default="http://localhost:8080", help="dirección del simulador")
    p.add_argument("--juez-automatico", action="store_true", help="aprueba solo (SOLO para pruebas)")
    p.add_argument("--puerto", type=int, default=8000)
    p.add_argument("--sin-web", action="store_true", help="solo el motor, sin API ni pantalla")
    p.add_argument("--red", action="store_true",
                   help="escuchar en toda la red local (para el celular del juez); por defecto solo esta máquina")
    p.add_argument("--exportar-entrega", action="store_true", help="al cerrar, copia expediente y auditoría a entrega/")
    args = p.parse_args()

    motor = Motor(args.sim, juez_automatico=args.juez_automatico)
    print(f"Motor conectado a {args.sim}: {motor.partido['nombre']} (corrida {motor.corrida})", flush=True)
    if args.juez_automatico:
        print("ATENCIÓN: juez automático encendido. Solo para pruebas; en el partido final va apagado.", flush=True)

    hilo = threading.Thread(target=motor.correr, daemon=True)
    hilo.start()
    if args.sin_web:
        hilo.join()
    else:
        # Sin PIN fijo: o lo define el juzgado en JUEZ_PIN, o se genera uno al azar por corrida y se muestra acá.
        pin = os.environ.get("JUEZ_PIN") or f"{secrets.randbelow(10**6):06d}"
        host = "0.0.0.0" if args.red else "127.0.0.1"
        print(f"Pantalla del juez: http://localhost:{args.puerto}/juez/  (PIN: {pin})", flush=True)
        if args.red:
            print("Escuchando en toda la red local para que el juez entre desde el celular por wifi.", flush=True)
        servidor = uvicorn.Server(uvicorn.Config(crear_app(motor, pin), host=host, port=args.puerto, log_level="warning"))
        threading.Thread(target=servidor.run, daemon=True).start()
        hilo.join()
        servidor.should_exit = True
    if args.exportar_entrega:
        motor.exportar_entrega(RAIZ / "entrega")
        print("Expediente y auditoría copiados a entrega/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
