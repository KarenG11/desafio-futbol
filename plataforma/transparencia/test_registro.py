"""Pruebas del registro público (T07) con asserts: una entrada por objetivo y estado real de proveedores."""
import json

from plataforma.contratos import EJEMPLO_EXPEDIENTE, EJEMPLO_PEDIDO
from plataforma.transparencia import RegistroPublico, armar_entradas, estado_publico


def _o(oid, prov, tipo, objetivo, estado, intentos=1, fin=None, motivo=None):
    return {"orden_id": oid, "pedido_id": EJEMPLO_PEDIDO["pedido_id"], "proveedor_id": prov, "tipo": tipo,
            "objetivo": objetivo, "estado": estado, "intentos": intentos, "vence_min": 105,
            "aplicada_min": 3.0 if estado != "recibida" else None, "finalizada_min": fin, "motivo": motivo}


def probar():
    ordenes = [
        _o("a1", "aurora", "ip", "198.51.100.7", "aplicada"),
        _o("c1", "cumbre", "ip", "198.51.100.7", "fallida"),
        _o("c2", "cumbre", "ip", "198.51.100.7", "aplicada", intentos=2),
        _o("v1", "valle", "dominio", "live.pirata.test", "recibida"),
    ]
    nombres = {EJEMPLO_PEDIDO["juez_id"]: "Dra. Laura Ficticia", EJEMPLO_PEDIDO["juzgado_id"]: "Juzgado 3"}
    entradas = armar_entradas([EJEMPLO_PEDIDO], {EJEMPLO_EXPEDIENTE["expediente_id"]: EJEMPLO_EXPEDIENTE},
                              ordenes, nombres)
    assert [e["tipo"] for e in entradas] == ["dominio", "ip"], "una entrada por (tipo, objetivo)"
    ip = entradas[1]
    assert ip["estado"] == "vigente" and ip["juez_nombre"] == "Dra. Laura Ficticia"
    assert {p["proveedor_id"]: p["estado"] for p in ip["proveedores"]} == {"aurora": "aplicada", "cumbre": "aplicada"}
    assert entradas[0]["estado"] == "en_curso"

    assert estado_publico([_o("x", "aurora", "ip", "i", "vencida", fin=105.0)])[0] == "vencido"
    lev = estado_publico([_o("x", "aurora", "ip", "i", "levantada", fin=20.0, motivo="Reclamo R-001")])
    assert lev == ("levantado", 20.0, "Reclamo R-001")

    pendiente = dict(EJEMPLO_PEDIDO, estado="pendiente")
    assert armar_entradas([pendiente], {EJEMPLO_EXPEDIENTE["expediente_id"]: EJEMPLO_EXPEDIENTE}, ordenes, {}) == []

    reg = RegistroPublico(ruta_salida="salida/test_registro_publico.json")
    reg.publicar(entradas)
    with open(reg.ruta_salida, encoding="utf-8") as f:
        assert len(json.load(f)["entradas"]) == 2
    print("test_registro: OK")


if __name__ == "__main__":
    probar()
