"""Ensayo del cerebro (T01) contra el simulador real, por HTTP. Solo lee: no manda órdenes.

    python simulador/servidor.py --acelerar 30            # en otra terminal
    python -m plataforma.analisis.ensayo_en_vivo --sim http://localhost:8080 [--verdad evaluacion/verdad_practica.json]

Imprime cada caso apenas aparece, con la demora entre el aviso del radar y la decisión, y al final lo compara con
la verdad del escenario si se la pasás. Sirve para probar el escenario del partido final sin depender del motor.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from plataforma.analisis import Cerebro


def pedir(base: str, ruta: str):
    try:
        with urllib.request.urlopen(base + ruta, timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def main() -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--sim", default="http://localhost:8080")
    p.add_argument("--verdad", type=Path)
    args = p.parse_args()
    base = args.sim.rstrip("/")

    partido = pedir(base, "/partido")
    cerebro = Cerebro(partido, lambda ip: pedir(base, f"/dns-pasivo?ip={ip}"))
    print(f"Partido: {partido['nombre']} (fin en el minuto {partido['fin_min']})\n")
    desde, fin = -1.0, float(partido["fin_min"])
    while True:
        lote = pedir(base, f"/detecciones?desde={desde}")
        for d in lote["detecciones"]:
            caso, nuevo = cerebro.procesar(d)
            if nuevo:
                demora = lote["minuto_actual"] - d["minuto"]
                tipo = caso["tipo_recomendado"] if caso["clasificacion"] == "pirata" else "-"
                print(f"min {d['minuto']:6.1f}  {caso['caso_id']}  {caso['host']:32} {caso['clasificacion']:20} "
                      f"{tipo:8} (decidido {demora:.2f} min después del aviso)")
        desde = lote["minuto_actual"]
        if desde >= fin:
            break
        time.sleep(0.5)

    casos = cerebro.casos()
    piratas = [c for c in casos if c["clasificacion"] == "pirata"]
    print(f"\n{len(casos)} casos, {len(piratas)} piratas, {len(casos) - len(piratas)} descartados")
    if not args.verdad:
        return 0
    verdad = json.loads(args.verdad.read_text(encoding="utf-8"))
    esperado = {(f["host"], f["ip"]): (s["clase"], f["bloqueo_recomendado"]) for s in verdad["streams"] for f in s["fases"]}
    errores = 0
    for c in casos:
        clase, rec = esperado.get((c["host"], c["ip"]), ("desconocido", None))
        bien = (c["clasificacion"] == "pirata") == (clase == "pirata") and (clase != "pirata" or c["tipo_recomendado"] == rec)
        errores += not bien
        if not bien:
            print(f"  DIFERENCIA {c['host']} {c['ip']}: {c['clasificacion']}/{c['tipo_recomendado']} vs {clase}/{rec}")
    faltan = set(esperado) - {(c["host"], c["ip"]) for c in casos}
    print(f"Contra la verdad: {len(casos) - errores} de {len(esperado)} bien" + (f", faltan {faltan}" if faltan else ""))
    return 1 if errores or faltan else 0


if __name__ == "__main__":
    sys.exit(main())
