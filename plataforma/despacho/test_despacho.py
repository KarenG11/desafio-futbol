"""Pruebas del despacho contra el SIMULADOR OFICIAL (se levanta en un subproceso en un puerto libre).

Cubre: firma HMAC aceptada (202), firma inválida (403 -> rechazada), objetivos por capacidad (valle solo dominio),
vencimiento, reintento de cumbre con orden_id nuevo tras `fallida`, levantamiento firmado y control de turno.
"""
import socket
import subprocess
import sys
import time
from pathlib import Path

from plataforma.despacho import Despacho, Firmador, objetivos_por_proveedor, vence_para
from plataforma.motor.motor import MARGEN_TURNO_MIN, Motor
from plataforma.motor.simulador import ClienteSimulador

RAIZ = Path(__file__).resolve().parents[2]


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _simulador(acelerar: float, inicio: float = 0.0):
    puerto = _puerto_libre()
    log = RAIZ / "salida" / f"test_despacho_{puerto}.jsonl"
    log.parent.mkdir(exist_ok=True)
    proc = subprocess.Popen([sys.executable, str(RAIZ / "simulador" / "servidor.py"), "--acelerar", str(acelerar),
                             "--inicio-min", str(inicio), "--puerto", str(puerto), "--log", str(log)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sim = ClienteSimulador(f"http://127.0.0.1:{puerto}")
    for _ in range(50):
        try:
            sim.get_ok("/estado")
            return proc, sim
        except Exception:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("el simulador no arrancó")


def probar_unidad():
    provs = [{"id": "aurora", "capacidades": ["ip", "dominio"]}, {"id": "valle", "capacidades": ["dominio"]}]
    obs = objetivos_por_proveedor("ip", "198.51.100.7", "live.x.test", provs)
    assert obs == [{"proveedor_id": "aurora", "tipo": "ip", "objetivo": "198.51.100.7"},
                   {"proveedor_id": "valle", "tipo": "dominio", "objetivo": "live.x.test"}]
    assert all(o["tipo"] == "dominio" for o in objetivos_por_proveedor("dominio", "1.2.3.4", "h.test", provs))
    assert vence_para(105, 10) == 105 and vence_para(105, 105) is None and vence_para(105, 104.99) == 105
    f = Firmador()
    assert "clave" not in repr(f) and "demo-clave" not in repr(f), "el repr no expone claves"

    m = Motor.__new__(Motor)          # control de turno sin red
    m.firmador, m.simulador_ok, m.juez_ratificado = f, True, "jueza-laura-ficticia"
    m.turnos = [{"juez_id": "jueza-laura-ficticia", "desde_min": -60, "hasta_min": 50},
                {"juez_id": "juez-martin-ejemplo", "desde_min": 50, "hasta_min": 240}]
    m.acelerar, m._t_estado = 0.0, time.monotonic()
    m._min_estado = 40.0
    assert m.firmante() == "jueza-laura-ficticia"
    m._min_estado = 50.0 - MARGEN_TURNO_MIN / 2
    assert m.firmante() is None, "no firma si el turno vence durante el envío"
    m._min_estado = 51.0
    assert m.firmante() is None, "el entrante no firma hasta asumir el turno"
    m.juez_ratificado = "juez-martin-ejemplo"
    assert m.firmante() == "juez-martin-ejemplo"
    m.simulador_ok = False
    assert m.firmante() is None, "sin simulador no se firma (fail-closed)"
    print("test_despacho (unidad): OK")


def probar_integracion():
    proc, sim = _simulador(acelerar=60)
    try:
        auditoria, guardadas = [], []
        d = Despacho(sim, Firmador(), "t", lambda a, ac, da: auditoria.append(ac), guardadas.append)
        provs = sim.get_ok("/proveedores")
        ahora = sim.get_ok("/estado")["minuto_actual"]
        pedido = {"pedido_id": "P-900", "expediente_id": "EXP-T",
                  "objetivos": objetivos_por_proveedor("ip", "198.51.100.200", "live.prueba.test", provs)}
        d.despachar_pedido(pedido, "jueza-laura-ficticia", ahora, 105)
        assert {o["proveedor_id"]: o["tipo"] for o in d.ordenes.values()} == \
            {"aurora": "ip", "andina": "ip", "cumbre": "ip", "valle": "dominio"}
        assert all(o["estado"] == "recibida" for o in d.ordenes.values()), "los 4 proveedores devolvieron 202"

        malo = Firmador()
        malo._claves = {k: "otra-clave" for k in malo._claves}
        d2 = Despacho(sim, malo, "t2", lambda *a: None, lambda o: None)
        d2.despachar_pedido({"pedido_id": "P-901", "expediente_id": "EXP-T",
                             "objetivos": [{"proveedor_id": "aurora", "tipo": "dominio", "objetivo": "x.test"}]},
                            "jueza-laura-ficticia", ahora, 105)
        (rechazada,) = d2.ordenes.values()
        assert rechazada["estado"] == "rechazada" and "Firma" in rechazada["motivo"]

        # cumbre falla ~35 %: seguimos y reintentamos hasta ver un fallo y su reemplazo con otro orden_id
        cumbre = [{"proveedor_id": "cumbre", "tipo": "dominio", "objetivo": f"r{i}.prueba.test"} for i in range(12)]
        d.despachar_pedido({"pedido_id": "P-902", "expediente_id": "EXP-T", "objetivos": cumbre},
                           "jueza-laura-ficticia", sim.get_ok("/estado")["minuto_actual"], 105)
        limite = time.time() + 20
        while time.time() < limite:
            d.seguir(["aurora", "andina", "valle", "cumbre"], "jueza-laura-ficticia",
                     sim.get_ok("/estado")["minuto_actual"], 105)
            reintentos = [o for o in d.ordenes.values() if o["reemplaza_a"]]
            if reintentos and all(d.ordenes[r["reemplaza_a"]]["estado"] == "fallida" for r in reintentos):
                break
            time.sleep(0.2)
        assert reintentos, "con 12 órdenes a cumbre tiene que aparecer al menos una fallida y su reintento"
        r = reintentos[0]
        assert r["orden_id"] != r["reemplaza_a"] and r["intentos"] == d.ordenes[r["reemplaza_a"]]["intentos"] + 1
        assert "orden_reenviada" in auditoria and "orden_fallida" in auditoria

        aurora = next(o for o in d.ordenes.values() if o["proveedor_id"] == "aurora" and o["pedido_id"] == "P-900")
        assert d.levantar(aurora["orden_id"], "jueza-laura-ficticia", "prueba", 0) is None
        vista = sim.get_ok(f"/proveedores/aurora/ordenes/{aurora['orden_id']}")
        assert vista["estado"] == "levantada", "el simulador confirmó el levantamiento"
        assert d.levantar(aurora["orden_id"], "jueza-laura-ficticia", "otra vez", 0) is not None, \
            "una orden ya levantada no se vuelve a levantar"
    finally:
        proc.terminate()
    print("test_despacho (integración con el simulador oficial): OK")


if __name__ == "__main__":
    probar_unidad()
    probar_integracion()
