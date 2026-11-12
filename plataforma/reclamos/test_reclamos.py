"""Pruebas de reclamos (T06) con asserts: correlación, descarte, levantamiento con confirmación y reemplazo."""
from plataforma.reclamos.gestor import GestorReclamos

CASO = {"caso_id": "C-003", "clasificacion": "pirata", "host": "live.pirata.test", "pagina": "pirata.test",
        "motivo_clasificacion": "marca válida en sitio no autorizado"}


def _orden(oid, prov, tipo, objetivo, estado="aplicada", pedido="P-003"):
    return {"orden_id": oid, "pedido_id": pedido, "proveedor_id": prov, "tipo": tipo, "objetivo": objetivo,
            "estado": estado, "aplicada_min": 10.0, "finalizada_min": None, "intentos": 1}


def _gestor():
    ordenes = {o["orden_id"]: o for o in [
        _orden("o-aurora", "aurora", "ip", "198.51.100.7"),
        _orden("o-andina", "andina", "ip", "198.51.100.7"),
        _orden("o-cumbre", "cumbre", "ip", "198.51.100.7", estado="recibida"),
        _orden("o-valle", "valle", "dominio", "live.pirata.test"),
        _orden("o-vieja", "aurora", "ip", "198.51.100.7", estado="fallida", pedido="P-003"),
    ]}
    dns = {"198.51.100.7": ["live.pirata.test", "panaderia.test"]}
    return GestorReclamos(ordenes, lambda: [CASO], lambda ip: dns.get(ip, []), lambda pid: CASO), ordenes


def probar():
    g, ordenes = _gestor()
    r = g.recibir_reclamo({"id": "R-001", "minuto": 14.0, "dominio": "panaderia.test", "proveedor": "aurora",
                           "mensaje": "no anda la tienda"})
    assert r["estado"] == "pendiente" and r["orden_ids"] == ["o-aurora"] and r["caso_id"] == "C-003"

    pirata = g.recibir_reclamo({"id": "R-002", "minuto": 14.0, "dominio": "live.pirata.test", "proveedor": "valle",
                                "mensaje": "me bloquearon"})
    assert pirata["estado"] == "descartado" and "pirata" in pirata["verificacion"]

    sin_orden = g.recibir_reclamo({"id": "R-003", "minuto": 14.0, "dominio": "otro.test", "proveedor": "andina",
                                   "mensaje": "?"})
    assert sin_orden["estado"] == "descartado" and sin_orden["orden_ids"] == []

    a_levantar = {o["orden_id"] for o in g.ordenes_a_levantar(r)}
    assert a_levantar == {"o-aurora", "o-andina", "o-cumbre"}, "todas las órdenes IP activas, ninguna de dominio"

    # un proveedor no confirma: el reclamo NO se marca levantado
    resp = g.resolver_reclamo("R-001", "jueza", True, 15.0,
                              lambda oid: "HTTP 500" if oid == "o-cumbre" else None, lambda rec: "P-009")
    assert resp["estado"] == "pendiente" and len(resp["errores"]) == 1 and resp["pedido_reemplazo_id"] is None
    for oid in ("o-aurora", "o-andina"):
        ordenes[oid]["estado"] = "levantada"

    resp = g.resolver_reclamo("R-001", "jueza", True, 15.5, lambda oid: None, lambda rec: "P-009")
    assert resp["estado"] == "levantado" and resp["errores"] == []
    assert resp["ordenes_levantadas"] == [{"proveedor_id": "cumbre", "orden_id": "o-cumbre"}]
    assert resp["pedido_reemplazo_id"] == "P-009" and g.reclamos["R-001"]["juez_id"] == "jueza"
    assert len(g.reclamos["R-001"]["ordenes_levantadas"]) == 3

    try:
        g.resolver_reclamo("R-002", "jueza", False, 16.0, lambda oid: None, lambda rec: None)
        raise AssertionError("un reclamo descartado no se puede levantar")
    except ValueError:
        pass
    print("test_reclamos: OK")


if __name__ == "__main__":
    probar()
