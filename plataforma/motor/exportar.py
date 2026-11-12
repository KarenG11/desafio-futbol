"""Exporta un expediente y la auditoría interna de una corrida a entrega/ (README oficial, entregable 3)."""
import json
import shutil
from pathlib import Path
from typing import Optional

from plataforma.contratos import HASH_INICIAL, hash_evento_auditoria, hash_expediente


def verificar_cadena(ruta: Path) -> int:
    """Devuelve la cantidad de eventos si la cadena es válida; lanza ValueError si no."""
    prev, n = HASH_INICIAL, 0
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        ev = json.loads(linea)
        if ev["hash_prev"] != prev or ev["hash"] != hash_evento_auditoria(ev):
            raise ValueError(f"cadena de auditoría rota en seq {ev.get('seq')}")
        prev, n = ev["hash"], n + 1
    return n


def exportar(expedientes: dict, ruta_auditoria: Path, destino: Path, expediente_id: Optional[str] = None) -> dict:
    destino.mkdir(parents=True, exist_ok=True)
    eventos = verificar_cadena(ruta_auditoria)
    exp_id = expediente_id or sorted(expedientes)[0]
    exp = expedientes[exp_id]
    if exp["hash"] != hash_expediente(exp):
        raise ValueError(f"hash del expediente {exp_id} no coincide")
    (destino / "expediente-final.json").write_text(json.dumps(exp, indent=2, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
    shutil.copyfile(ruta_auditoria, destino / "auditoria-final.jsonl")
    return {"expediente_id": exp_id, "eventos_auditoria": eventos}


def main() -> None:
    """python -m plataforma.motor.exportar entrega/auditoria-final.jsonl entrega/expediente-final.json"""
    import argparse
    ap = argparse.ArgumentParser(description="Verifica la cadena de la auditoría y el hash de uno o más expedientes")
    ap.add_argument("auditoria", type=Path)
    ap.add_argument("expedientes", type=Path, nargs="*")
    a = ap.parse_args()
    try:
        print(f"auditoría: {verificar_cadena(a.auditoria)} eventos, cadena de hashes íntegra")
    except ValueError as e:
        raise SystemExit(f"{a.auditoria}: {e}")
    for ruta in a.expedientes:
        exp = json.loads(ruta.read_text(encoding="utf-8"))
        if exp["hash"] != hash_expediente(exp):
            raise SystemExit(f"{ruta}: el hash del expediente {exp['expediente_id']} NO coincide")
        print(f"{ruta}: hash del expediente {exp['expediente_id']} íntegro ({exp['hash'][:16]}…)")


if __name__ == "__main__":
    main()
