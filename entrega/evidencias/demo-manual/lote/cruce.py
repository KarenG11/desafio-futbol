"""Cruza lo que informó la API al firmar en lote (lote.json) con la base de la plataforma, la auditoría interna y el registro oficial del simulador."""
import json, sqlite3, sys
from pathlib import Path

d = Path(__file__).parent
lote = json.loads((d / "lote.json").read_text(encoding="utf-8"))
reg = [json.loads(l) for l in (d / "registro.jsonl").read_text(encoding="utf-8").splitlines()]
aud = [json.loads(l) for l in (d / "auditoria_interna.jsonl").read_text(encoding="utf-8").splitlines()]
db = sqlite3.connect(d / "plataforma.db")
recibidas = {e["orden_id"]: e for e in reg if e["evento"] == "orden_recibida"}
aplicadas = {e["orden_id"]: e["min"] for e in reg if e["evento"] == "orden_aplicada"}
enviadas = {e["datos"]["orden_id"]: e for e in aud if e["accion"] == "orden_enviada"}
errores = 0


def ok(cond, txt):
    global errores
    print(("OK    " if cond else "ERROR ") + txt)
    errores += not cond


aprob = [p for p in lote["pedidos"] if p["estado"] == "aprobado"]
ok(len(aprob) == 2 and len({p["decidido_min"] for p in aprob}) == 1,
   f"API: 2 pedidos aprobados en el mismo minuto {[(p['pedido_id'], p['juez_id'], p['decidido_min']) for p in aprob]}")
base = db.execute("select pedido_id, estado, juez_id, decidido_min from pedidos where estado = 'aprobado' order by pedido_id").fetchall()
ok([(p["pedido_id"], p["juez_id"], p["decidido_min"]) for p in aprob] == [(b[0], b[2], b[3]) for b in base],
   f"base: {base}")
for o in sorted(lote["ordenes"], key=lambda o: o["orden_id"]):
    r, a = recibidas.get(o["orden_id"]), enviadas.get(o["orden_id"])
    ok(a is not None and r is not None and r["proveedor"] == o["proveedor_id"] and r["tipo"] == o["tipo"]
       and r["objetivo"] == o["objetivo"] and r["juez_id"] == o["juez_id"] and r["juez_de_turno"] is True,
       f"{o['orden_id']}: {o['proveedor_id']} {o['tipo']} {o['objetivo']} | auditoría seq {a and a['seq']}"
       f" | simulador: recibida min {r and r['min']}, aplicada min {aplicadas.get(o['orden_id'])}")
ok(set(recibidas) == {o["orden_id"] for o in lote["ordenes"]} == set(enviadas),
   f"simulador recibió {len(recibidas)}, auditoría registra {len(enviadas)} envíos, API informó {len(lote['ordenes'])}")
print("TODO OK" if not errores else f"{errores} ERRORES")
sys.exit(1 if errores else 0)
