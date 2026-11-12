"""Baja a entrega/ el expediente y la auditoría de un partido corrido en la nube, por la API pública del sitio.

    py -m plataforma.motor.exportar_web --url https://desafio-futbol-karen.vercel.app

Sirve cuando el partido final corre en el Vercel Sandbox (no en esta notebook): no hace falta la clave de la base.
Verifica la cadena de hashes de la auditoría y el hash del expediente antes de escribir; si algo no coincide, no escribe.
"""
import argparse
import json
import tempfile
import urllib.request
from pathlib import Path

from plataforma.motor.exportar import exportar


def _get(url: str):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=30) as r:
        return json.loads(r.read())


def main() -> None:
    ap = argparse.ArgumentParser(description="Exporta expediente y auditoría desde la API pública del deploy")
    ap.add_argument("--url", default="https://desafio-futbol-karen.vercel.app")
    ap.add_argument("--destino", type=Path, default=Path("entrega"))
    ap.add_argument("--expediente", default=None, help="expediente a exportar (por defecto el primero del partido)")
    a = ap.parse_args()
    base = a.url.rstrip("/")

    estado = _get(f"{base}/api/estado")
    pid = estado.get("partido_id")
    eventos = _get(f"{base}/api/auditoria")["eventos"]
    if not eventos:
        raise SystemExit(f"El partido {pid} no tiene auditoría todavía")
    ids = sorted({p["expediente_id"] for p in _get(f"{base}/api/pedidos")["pedidos"]})
    exp_id = a.expediente or (ids[0] if ids else None)
    if not exp_id:
        raise SystemExit(f"El partido {pid} no tiene expedientes")
    expedientes = {exp_id: _get(f"{base}/api/expedientes/{exp_id}")}

    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "auditoria.jsonl"
        ruta.write_text("".join(json.dumps(ev, ensure_ascii=False) + "\n" for ev in eventos), encoding="utf-8")
        try:
            r = exportar(expedientes, ruta, a.destino, exp_id)
        except ValueError as e:
            raise SystemExit(f"No se exporta: {e}")
    print(f"[exportar_web] partido {pid} (minuto {estado.get('minuto_actual')}, finalizado={estado.get('finalizado')}): "
          f"{r['expediente_id']} y {r['eventos_auditoria']} eventos íntegros en {a.destino}/")


if __name__ == "__main__":
    main()
