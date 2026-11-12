"""Verificación de solo lectura de la demo manual. Uso, desde la raíz del repo:
python entrega/evidencias/demo-manual/verificar_demo.py
Revisa la cadena de la auditoría, la base contra la auditoría, los hashes de los expedientes, la API contra el registro
del simulador, vuelve a correr el verificador oficial y el cruce de la firma en lote. No escribe ningún archivo."""
import json, sqlite3, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from plataforma.motor.exportar import hash_expediente, verificar_cadena  # noqa: E402

D = Path(__file__).resolve().parent
errores = 0


def ok(cond, txt):
    global errores
    print(("OK    " if cond else "ERROR ") + txt)
    errores += not cond


def jsonl(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def revisar_plataforma(nombre, carpeta):
    aud_p = carpeta / "auditoria_interna.jsonl"
    try:
        n = verificar_cadena(aud_p)
        ok(True, f"{nombre}: auditoría con {n} eventos, cadena de hashes íntegra")
    except ValueError as e:
        ok(False, f"{nombre}: {e}")
    aud = jsonl(aud_p)
    db = sqlite3.connect(f"file:{carpeta / 'plataforma.db'}?mode=ro", uri=True)
    ok([r[0] for r in db.execute("select hash from auditoria order by seq")] == [e["hash"] for e in aud],
       f"{nombre}: la tabla auditoria de la base es idéntica a auditoria_interna.jsonl")
    creados = {e["datos"]["expediente_id"]: e["datos"]["expediente_hash"] for e in aud if e["accion"] == "expediente_creado"}
    exps = [json.loads(r[0]) for r in db.execute("select datos from expedientes order by expediente_id")]
    ok(all(e["hash"] == hash_expediente(e) == creados.get(e["expediente_id"]) for e in exps) and len(exps) == len(creados),
       f"{nombre}: {len(exps)} expedientes con hash recalculado igual al guardado y al de la auditoría")
    return aud, db


print("== Partido completo (demo-manual/) ==")
reg = jsonl(D / "registro.jsonl")
ok(reg[-1]["evento"] == "ventana_cerrada" and reg[-1]["min"] == 110.0, "el registro del simulador llega al minuto 110 (ventana cerrada)")
aud, db = revisar_plataforma("plataforma", D / "plataforma")
final = json.loads((D / "final.json").read_text(encoding="utf-8"))
recibidas = {e["orden_id"]: e for e in reg if e["evento"] == "orden_recibida"}
ultimo = {}
for e in reg:
    if e["evento"] in ("orden_aplicada", "orden_fallida", "orden_vencida"):
        ultimo[e["orden_id"]] = e["evento"].replace("orden_", "")
api = {o["orden_id"]: o for o in final["ordenes"]}
enviadas = {e["datos"]["orden_id"] for e in aud if e["accion"] in ("orden_enviada", "orden_reenviada")}
ok(set(api) == set(recibidas) == enviadas, f"{len(api)} órdenes: las mismas en la API, la auditoría y el registro del simulador")
ok(all(ultimo[k] == o["estado"] and recibidas[k]["objetivo"] == o["objetivo"] and recibidas[k]["juez_id"] == o["juez_id"]
       and recibidas[k]["juez_de_turno"] is True for k, o in api.items()),
   "cada orden tiene el mismo objetivo, juez y estado final en la API y en el registro; todas con juez de turno")
activas = {}
for k, o in api.items():
    if o["estado"] != "fallida":
        activas.setdefault((o["pedido_id"], o["proveedor_id"]), []).append(k)
ok(all(len(v) == 1 for v in activas.values()), f"una sola orden no fallida por pedido y proveedor ({len(activas)} combinaciones): los reintentos no duplicaron bloqueos")
log = (D / "recorrido.log").read_text(encoding="utf-8")
ok("FIRMA JUEZA SALIENTE -> (409" in log and "ASUMIR TURNO (UI)" in log and "FIRMA EN LOTE" not in log and "juez automático" not in log.lower(),
   "recorrido.log: la jueza saliente recibió 409, el juez entrante asumió desde la pantalla y todas las firmas fueron individuales")
salida = subprocess.run([sys.executable, str(RAIZ / "evaluacion" / "verificar.py"), "--log", str(D / "registro.jsonl")],
                        capture_output=True, text=True, cwd=RAIZ, env={"PYTHONUTF8": "1", "PATH": ""}).stdout
ok(salida == (D / "verificar.txt").read_text(encoding="utf-8"), "el verificador oficial, corrido de nuevo, da exactamente verificar.txt")

print("\n== Firma en lote (demo-manual/lote/) ==")
revisar_plataforma("lote", D / "lote")
r = subprocess.run([sys.executable, str(D / "lote" / "cruce.py")], capture_output=True, text=True)
ok(r.returncode == 0 and r.stdout == (D / "lote" / "cruce.txt").read_text(encoding="utf-8"),
   "lote/cruce.py da TODO OK y la misma salida que lote/cruce.txt")

print("\nTODO OK" if not errores else f"\n{errores} ERRORES")
sys.exit(1 if errores else 0)
