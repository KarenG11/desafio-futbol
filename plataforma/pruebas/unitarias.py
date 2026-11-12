"""Corre todas las pruebas con asserts de la plataforma; termina con código 1 si alguna falla.

    python -m plataforma.pruebas.unitarias
"""
import subprocess
import sys

MODULOS = [
    "plataforma.analisis.test_cerebro",
    "plataforma.evidencia.test_evidencia",
    "plataforma.reclamos.test_reclamos",
    "plataforma.transparencia.test_registro",
    "plataforma.db.test_db_api",
    "plataforma.despacho.test_despacho",   # levanta el simulador oficial en un puerto libre
]


def main() -> None:
    fallidos = []
    for m in MODULOS:
        r = subprocess.run([sys.executable, "-m", m], capture_output=True, text=True)
        estado = "OK" if r.returncode == 0 else "FALLÓ"
        print(f"{estado:6} {m}")
        if r.returncode:
            fallidos.append(m)
            print(r.stdout[-2000:], r.stderr[-2000:], sep="\n")
    print(f"\n{len(MODULOS) - len(fallidos)} de {len(MODULOS)} módulos OK")
    sys.exit(1 if fallidos else 0)


if __name__ == "__main__":
    main()
