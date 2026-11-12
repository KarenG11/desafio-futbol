"""Verificación cruzada de una corrida: registro.jsonl (simulador) vs auditoría (plataforma) vs verificar.json (oficial).

Solo lee archivos y usa la biblioteca estándar; reimplementa el hashing para no depender del código que verifica.
Uso:
  python entrega/evidencias/verificacion/verificar_corrida.py \
      --corrida entrega/evidencias/practica --auditoria entrega/auditoria-final.jsonl \
      --expediente entrega/expediente-final.json [--db entrega/evidencias/practica/plataforma.db]
Sale con código 1 si alguna comprobación falla.
"""
import argparse, hashlib, json, sqlite3, sys
from collections import Counter, defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--corrida", type=Path, required=True)
ap.add_argument("--auditoria", type=Path, required=True)
ap.add_argument("--expediente", type=Path, required=True)
ap.add_argument("--db", type=Path)
ap.add_argument("--proveedores", type=Path, default=Path("datos/proveedores.json"))
a = ap.parse_args()

fallos = []
def ok(cond, texto):
    print(("  OK    " if cond else "  FALLA ") + texto)
    if not cond:
        fallos.append(texto)

canon = lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
sha = lambda b: hashlib.sha256(b).hexdigest()
leer = lambda p: [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

R = leer(a.corrida / "registro.jsonl")
A = leer(a.auditoria)
V = json.loads((a.corrida / "verificar.json").read_text(encoding="utf-8"))
E = json.loads(a.expediente.read_text(encoding="utf-8"))
prov = {p["id"]: p for p in json.loads(a.proveedores.read_text(encoding="utf-8"))["proveedores"]}

reg = defaultdict(dict)                       # orden_id -> evento -> registro
for ev in R:
    if "orden_id" in ev:
        reg[ev["orden_id"]][ev["evento"]] = ev
aud = defaultdict(dict)                       # orden_id -> accion -> evento de auditoría
for ev in A:
    oid = (ev.get("datos") or {}).get("orden_id")
    if oid:
        aud[oid][ev["accion"]] = ev
db = {}
if a.db:
    con = sqlite3.connect(a.db)
    db = {oid: json.loads(d) for oid, d in con.execute("select orden_id, datos from ordenes")}

cuenta = Counter(ev["evento"] for ev in R)
print(f"registro.jsonl: {dict(cuenta)}")

print("\n1. Órdenes fallidas")
fallidas = [oid for oid, e in reg.items() if "orden_fallida" in e]
for oid in fallidas:
    f = reg[oid]["orden_fallida"]
    rec = reg[oid]["orden_recibida"]
    reenv = [ev for ev in A if ev["accion"] == "orden_reenviada" and ev["datos"]["reemplaza_a"] == oid]
    nuevo = reenv[0]["datos"]["orden_id"] if reenv else None
    n = reg.get(nuevo, {})
    print(f"  {oid} ({f['proveedor']}, {rec['tipo']} {rec['objetivo']}): falló min {f['min']} «{f['motivo']}»")
    print(f"     -> reenviada como {nuevo} min {reenv[0]['min'] if reenv else '-'}; recibida {n.get('orden_recibida', {}).get('min')}, "
          f"aplicada {n.get('orden_aplicada', {}).get('min')}, estado final: "
          f"{'vencida min ' + str(n['orden_vencida']['min']) if 'orden_vencida' in n else (db.get(nuevo, {}).get('estado') or '?')}")
    ok("orden_aplicada" not in reg[oid], f"{oid}: el proveedor nunca la aplicó (no hay bloqueo duplicado)")
    ok("nuevo orden_id" in f["motivo"], f"{oid}: el proveedor pidió reenviar con orden_id nuevo")
    ok(f["min"] < rec["vence_min"], f"{oid}: el pedido seguía vigente al fallar (min {f['min']} < vence {rec['vence_min']})")
    ok(rec["tipo"] in prov[f["proveedor"]]["capacidades"], f"{oid}: el proveedor acepta el tipo {rec['tipo']}")
    ok(bool(nuevo) and nuevo != oid, f"{oid}: hubo reenvío con orden_id distinto")
    if nuevo:
        nr = n.get("orden_recibida", {})
        ok(all(nr.get(k) == rec[k] for k in ("tipo", "objetivo", "vence_min", "expediente_id")),
           f"{nuevo}: mismo tipo, objetivo, vencimiento y expediente que la original")
        final, cadena = nuevo, [nuevo]
        while "orden_fallida" in reg.get(final, {}):
            sig = [ev["datos"]["orden_id"] for ev in A if ev["accion"] == "orden_reenviada" and ev["datos"]["reemplaza_a"] == final]
            if not sig:
                break
            final = sig[0]
            cadena.append(final)
        nf = reg.get(final, {})
        ok("orden_aplicada" in nf and "orden_vencida" in nf,
           f"cadena de reintentos {' -> '.join([oid] + cadena)}: la última quedó aplicada (min "
           f"{nf.get('orden_aplicada', {}).get('min')}) y vencida (min {nf.get('orden_vencida', {}).get('min')})")
    if db:
        ok(db[oid]["estado"] == "fallida", f"{oid}: estado en la base = {db[oid]['estado']}")
print(f"  Tasa de falla configurada: " + ", ".join(f"{p} {v['comportamiento']['tasa_falla']}" for p, v in prov.items()))

print("\n2. Órdenes aplicadas")
aplicadas = [oid for oid, e in reg.items() if "orden_aplicada" in e]
for oid in aplicadas:
    e, au = reg[oid], aud[oid]
    rec, apl = e["orden_recibida"], e["orden_aplicada"]
    conds = [
        rec["juez_de_turno"] is True,
        rec["min"] <= apl["min"],
        "orden_aplicada" in au and au["orden_aplicada"]["datos"]["aplicada_min"] == apl["min"],
        ("orden_enviada" in au) != ("orden_reenviada" in au),
        "orden_vencida" in e and e["orden_vencida"]["min"] == rec["vence_min"],
        "orden_vencida" in au,
        not db or (db[oid]["estado"] == "vencida" and db[oid]["aplicada_min"] == apl["min"]),
    ]
    ok(all(conds), f"{oid}: recibida {rec['min']} (juez de turno) -> aplicada {apl['min']} -> vencida {e.get('orden_vencida', {}).get('min')}"
                   + ("" if all(conds) else f" {conds}"))
pares = Counter((reg[o]["orden_recibida"]["expediente_id"], reg[o]["orden_recibida"]["tipo"],
                 reg[o]["orden_recibida"]["objetivo"], reg[o]["orden_recibida"]["proveedor"]) for o in aplicadas)
ok(all(c == 1 for c in pares.values()), f"una sola orden aplicada por objetivo y proveedor ({len(pares)} combinaciones)")

print("\n3. Correspondencia registro / auditoría / verificador")
ids_reg = {o for o, e in reg.items() if "orden_recibida" in e}
ids_aud = {ev["datos"]["orden_id"] for ev in A if ev["accion"] in ("orden_enviada", "orden_reenviada")}
ok(ids_reg == ids_aud, f"órdenes recibidas por el simulador ({len(ids_reg)}) = enviadas/reenviadas en la auditoría ({len(ids_aud)})")
if db:
    ok(ids_reg == set(db), f"= órdenes en la base de la plataforma ({len(db)})")
for ev_r, acc in (("orden_aplicada", "orden_aplicada"), ("orden_fallida", "orden_fallida"), ("orden_vencida", "orden_vencida")):
    ok({o for o, e in reg.items() if ev_r in e} == {o for o, e in aud.items() if acc in e},
       f"{ev_r}: mismas órdenes en registro y auditoría ({cuenta[ev_r]})")
res = V["resumen"]
for k, ev_r in (("ordenes_recibidas", "orden_recibida"), ("ordenes_aplicadas", "orden_aplicada"), ("ordenes_fallidas", "orden_fallida")):
    ok(res[k] == cuenta[ev_r], f"verificador {k} = {res[k]} = registro {cuenta[ev_r]}")
ok(res["ordenes_rechazadas"] == cuenta["orden_rechazada"] == 0, "0 órdenes rechazadas (firma HMAC aceptada en todas)")
ok(res["ordenes_firmadas_fuera_de_turno"] == 0 and all(e["orden_recibida"]["juez_de_turno"] for e in reg.values() if "orden_recibida" in e),
   "0 fuera de turno, y todas las recibidas con juez_de_turno=true")
for f in V["fases"]:
    bloq = sorted({reg[o]["orden_recibida"]["proveedor"] for o in aplicadas
                   if reg[o]["orden_recibida"]["objetivo"] in (f["ip"], f["host"])
                   and f["desde_min"] <= reg[o]["orden_aplicada"]["min"] <= f["hasta_min"]})
    ok(bloq == sorted(f["proveedores_que_bloquearon"]),
       f"fase {f['stream']}-{f['fase']}: primer bloqueo {f['primer_bloqueo_min']} min; proveedores según registro {bloq}")
ips_activas = [o for o in aplicadas if reg[o]["orden_recibida"]["tipo"] == "ip" and "orden_vencida" not in reg[o] and "orden_levantada" not in reg[o]]
ok(not ips_activas and res["bloqueos_ip_activos_post_partido"] == 0, "0 IP activas al cierre (todas vencidas o levantadas)")
exps_reg = {e["orden_recibida"]["expediente_id"] for e in reg.values() if "orden_recibida" in e}
exps_aud = {ev["datos"]["expediente_id"] for ev in A if ev["accion"] == "expediente_creado"}
ok(exps_reg <= exps_aud, f"los {len(exps_reg)} expedientes citados en las órdenes están creados en la auditoría")

print("\n4. Cadena de hashes de la auditoría")
prev, rotos = "0" * 64, []
for i, ev in enumerate(A, 1):
    calc = sha(ev["hash_prev"].encode() + canon({k: v for k, v in ev.items() if k != "hash"}))
    if ev["seq"] != i or ev["hash_prev"] != prev or ev["hash"] != calc:
        rotos.append(ev["seq"])
    prev = ev["hash"]
ok(not rotos, f"{len(A)} eventos, seq 1..{len(A)} contiguo, hash_prev encadenado y hash recalculado (rotos: {rotos})")
print(f"  primer hash_prev 000…0, último hash {A[-1]['hash']}")
if a.db:
    filas = dict(con.execute("select seq, hash from auditoria"))
    ok(filas == {ev["seq"]: ev["hash"] for ev in A}, f"hashes iguales a la tabla auditoria de la base ({len(filas)} filas)")

print("\n5. Expediente")
h = sha(canon({k: v for k, v in E.items() if k != "hash"}))
ok(h == E["hash"], f"{E['expediente_id']}: hash recalculado {h}")
creado = [ev for ev in A if ev["accion"] == "expediente_creado" and ev["datos"]["expediente_id"] == E["expediente_id"]]
ok(bool(creado) and creado[0]["datos"]["expediente_hash"] == E["hash"], f"el mismo hash quedó en la auditoría (seq {creado[0]['seq'] if creado else '-'})")
ok(E["expediente_id"] in exps_reg, "el simulador recibió órdenes que citan este expediente")
ok(E["partido_id"] == R[0]["escenario"] == V["escenario"], f"partido del expediente {E['partido_id']} = escenario del registro {R[0]['escenario']} = del verificador {V['escenario']}")
if a.db:
    fila = con.execute("select hash, datos from expedientes where expediente_id=?", (E["expediente_id"],)).fetchone()
    ok(fila and fila[0] == E["hash"] and json.loads(fila[1]) == E, "idéntico al guardado en la base de la plataforma")

print(f"\n{'TODO OK' if not fallos else str(len(fallos)) + ' FALLAS'}")
sys.exit(1 if fallos else 0)
