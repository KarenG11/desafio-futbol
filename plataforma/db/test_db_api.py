"""Pruebas unitarias de la capa de datos plataforma/db/ y la API plataforma/api/app.py (T11).

Uso:
    PYTHONUTF8=1 python -m plataforma.db.test_db_api
"""
import os
import tempfile
from pathlib import Path


def correr_pruebas() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ruta_db = Path(tmp) / "test.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{ruta_db}"
        os.environ["JUEZ_PIN"] = "4321"

        from fastapi import HTTPException
        from plataforma import db
        from plataforma.api.app import (
            api_aprobar,
            api_asumir_turno,
            api_auditoria,
            api_auditoria_integridad,
            api_estado,
            api_expediente,
            api_levantar_reclamo,
            api_ordenes,
            api_pedidos,
            api_publico,
            api_reclamos,
            api_rechazar,
            monitoreo,
            partido,
            partidos,
            api_juez_ingresar,
            api_juez_jueces,
            api_juez_yo,
            juez_sesion,
            raiz,
            registro,
        )
        from plataforma.db.semilla import PARTIDO_DEMO, cargar_semilla

        # 1. Semilla y esquema
        cargar_semilla(PARTIDO_DEMO)
        assert db.partido_actual() == PARTIDO_DEMO
        est = db.estado_partido(PARTIDO_DEMO)
        assert est is not None and est["partido_id"] == PARTIDO_DEMO

        # 2. Endpoints de la API
        datos_est = api_estado()
        assert datos_est["partido_id"] == PARTIDO_DEMO
        assert datos_est["contadores"]["pedidos_pendientes"] == 2

        pedidos = api_pedidos(estado="pendiente")["pedidos"]
        assert len(pedidos) == 2
        assert "resumen" in pedidos[0]
        assert pedidos[0]["resumen"]["host"] == "s1.pelotaya.test"

        exp = api_expediente("EXP-2026-000001")
        assert exp["expediente_id"] == "EXP-2026-000001"

        # Ingreso de cada juez con usuario y contraseña (la contraseña de demo sale de JUEZ_PIN y el usuario)
        from plataforma import claves
        LAURA, MARTIN = "jueza-laura-ficticia", "juez-martin-ejemplo"
        assert {j["juez_id"] for j in api_juez_jueces()["jueces"]} >= {LAURA, MARTIN}
        assert claves.clave_de(LAURA) != claves.clave_de(MARTIN)
        for usuario, clave in ((LAURA, "incorrecta"), (LAURA, claves.clave_de(MARTIN)), ("juez-inexistente", "x")):
            try:
                api_juez_ingresar({"juez_id": usuario, "clave": clave})
                raise AssertionError(f"{usuario} no debería ingresar con esa clave")
            except HTTPException as exc:
                assert exc.status_code == 401
        sesion = api_juez_ingresar({"juez_id": LAURA, "clave": claves.clave_de(LAURA)})
        laura = juez_sesion(sesion["token"])
        assert laura == LAURA and api_juez_yo(laura)["de_turno"] is True
        martin = juez_sesion(api_juez_ingresar({"juez_id": MARTIN, "clave": claves.clave_de(MARTIN)})["token"])
        assert api_juez_yo(martin)["de_turno"] is False
        for malo in (None, "basura", sesion["token"][:-4] + "AAAA"):
            try:
                juez_sesion(malo)
                raise AssertionError("token inválido aceptado")
            except HTTPException as exc:
                assert exc.status_code == 401
        assert claves.leer_token(sesion["token"], ahora=__import__("time").time() + claves.DURACION_S + 5) is None
        try:   # nadie firma por otro: la sesión de Laura no puede firmar como Martín
            api_aprobar({"pedido_ids": ["P-001"], "juez_id": MARTIN}, juez=laura)
            raise AssertionError("firmó como otro juez")
        except HTTPException as exc:
            assert exc.status_code == 403

        # Aprobar P-001
        resp_ap = api_aprobar({"pedido_ids": ["P-001"]}, juez=laura)
        assert resp_ap["aprobados"] == ["P-001"]
        assert resp_ap["errores"] == []

        # Verificar atomicidad: volver a aprobar P-001 -> va a errores
        r2 = api_aprobar({"pedido_ids": ["P-001"]}, juez=laura)
        assert r2["aprobados"] == []
        assert len(r2["errores"]) == 1

        # Verificar que el motor lo ve en pedidos_para_despachar y lo marca despachado
        para_desp = db.pedidos_para_despachar(PARTIDO_DEMO)
        assert len(para_desp) == 1 and para_desp[0]["pedido_id"] == "P-001"
        db.marcar_despachado(PARTIDO_DEMO, "P-001")
        assert db.pedidos_para_despachar(PARTIDO_DEMO) == []

        # Rechazar P-002
        r_rec = api_rechazar({"pedido_ids": ["P-002"], "motivo": "Evidencia insuficiente"}, juez=laura)
        assert r_rec["rechazados"] == ["P-002"]

        # Asumir turno y levantar reclamo -> crean solicitudes; sin motor que las resuelva quedan PENDIENTES (202),
        # nunca se informa "levantado" sin confirmación real.
        import sys
        app_mod = sys.modules["plataforma.api.app"]
        app_mod.ESPERA_SOLICITUD_SEG = 0.3
        r_turno = api_asumir_turno({}, juez=laura)
        assert r_turno.status_code == 202

        r_lev = api_levantar_reclamo({"reclamo_id": "R-001", "motivo": "IP compartida", "reemplazar": True}, juez=laura)
        assert r_lev.status_code == 202 and db.obtener("reclamos", PARTIDO_DEMO, "R-001")["estado"] == "pendiente"

        sols = db.solicitudes_pendientes(PARTIDO_DEMO)
        assert len(sols) == 2
        for s in sols:
            db.resolver_solicitud(PARTIDO_DEMO, s["solicitud_id"], {"ok": True})
        assert db.solicitudes_pendientes(PARTIDO_DEMO) == []
        assert db.obtener_solicitud(PARTIDO_DEMO, sols[0]["solicitud_id"])["resultado"] == {"ok": True}

        # Control de turno fail-closed: Martín ingresó bien, pero no está de turno y no puede firmar
        for juez, codigo in ((martin, 409), ("juez-inexistente", 400)):
            try:
                api_aprobar({"pedido_ids": ["P-002"]}, juez=juez)
                raise AssertionError(f"{juez} no debería poder decidir")
            except HTTPException as exc:
                assert exc.status_code == codigo, (juez, exc.status_code)
        try:
            api_aprobar({"pedido_ids": ["P-002"]}, partido_id="sin-motor", juez=laura)
            raise AssertionError("sin estado del motor no se decide")
        except HTTPException as exc:
            assert exc.status_code == 503
        assert api_estado(partido_id="sin-motor")["jueces_de_turno"] == []

        # Ordenes, auditoria, reclamos, publico
        assert len(api_ordenes()["ordenes"]) == 3
        assert len(api_auditoria()["eventos"]) == 4
        assert len(api_reclamos()["reclamos"]) == 1
        assert "entradas" in api_publico()

        # Integridad de la auditoría: íntegra con la semilla, y una alteración se detecta
        integ = api_auditoria_integridad()
        assert integ["integra"] is True and integ["eventos"] == 4, integ
        with db._sesion() as (_, cur, pg):
            cur.execute(db._q("UPDATE auditoria SET datos = ? WHERE partido_id = ? AND seq = 2", pg),
                        (db._json_param(dict(db.auditoria(PARTIDO_DEMO)[1], actor="alterado"), pg), PARTIDO_DEMO))
        integ = api_auditoria_integridad()
        assert integ["integra"] is False and integ["falla_en_seq"] == 2, integ

        # URL del simulador externo (partido final) para la demo en la nube
        from plataforma.nube.rutas import _url_simulador
        assert _url_simulador(None) is None and _url_simulador("  ") is None
        assert _url_simulador("https://sim.final.example/") == "https://sim.final.example"
        for mala in ("ftp://x", "javascript:alert(1)", "sim.example"):
            try:
                _url_simulador(mala)
                raise AssertionError(f"{mala} no debería aceptarse")
            except HTTPException as exc:
                assert exc.status_code == 400

        # Portada, monitoreo y registro público
        for pagina in (raiz(), monitoreo(), registro(), partidos(), partido()):
            assert Path(pagina.path).is_file(), pagina.path

    print("test_db_api: OK")


if __name__ == "__main__":
    correr_pruebas()
