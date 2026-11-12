"""Corre un partido completo: simulador oficial + motor (--juez-automatico) + evaluacion/verificar.py, con asserts.

    python -m plataforma.pruebas.partido_completo --salida salida/e2e-practica
    python -m plataforma.pruebas.partido_completo --inicio-min 40 --salida salida/e2e-turno
    python -m plataforma.pruebas.partido_completo --escenario reclamos --salida salida/e2e-reclamos
    python -m plataforma.pruebas.partido_completo --escenario reclamos --falla dns-desactualizado \
        --salida salida/e2e-reclamo-forzado

Deja en --salida: registro.jsonl (oficial, del simulador), auditoria.jsonl (interna), publico.json,
verificar.txt y verificar.json (salida real del verificador) y resumen.json con los chequeos.
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESC = Path(__file__).resolve().parent / "escenarios"
ESCENARIOS = {
    "practica": (RAIZ / "datos" / "escenario_practica.json", RAIZ / "evaluacion" / "verdad_practica.json"),
    "reclamos": (ESC / "escenario_reclamos.json", ESC / "verdad_reclamos.json"),
}


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# Falla inyectada (solo pruebas): DNS pasivo desactualizado para la IP compartida del escenario de reclamos.
FALLAS = {
    "dns-desactualizado": ["-m", "plataforma.pruebas.motor_con_falla", "--ip-desactualizada", "192.0.2.50",
                           "--dominios", "tv.verpartido.hostcomun.test", "--"],
}


def correr(escenario: str, acelerar: float, inicio: float, salida: Path, falla: str = None) -> dict:
    esc, verdad = ESCENARIOS[escenario]
    salida.mkdir(parents=True, exist_ok=True)
    puerto = _puerto_libre()
    sim = subprocess.Popen([sys.executable, str(RAIZ / "simulador" / "servidor.py"), "--escenario", str(esc),
                            "--acelerar", str(acelerar), "--inicio-min", str(inicio), "--puerto", str(puerto),
                            "--log", str(salida / "registro.jsonl")],
                           stdout=open(salida / "simulador.log", "w"), stderr=subprocess.STDOUT)
    time.sleep(1.0)
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{salida / 'plataforma.db'}", PYTHONUNBUFFERED="1")
    try:
        modulo = FALLAS[falla] if falla else ["-m", "plataforma.motor"]
        motor = subprocess.run([sys.executable, *modulo, "--sim", f"http://127.0.0.1:{puerto}",
                                "--juez-automatico", "--auditoria", str(salida / "auditoria.jsonl"),
                                "--publico", str(salida / "publico.json"), "--exportar", str(salida / "export")],
                               cwd=RAIZ, env=env, stdout=open(salida / "motor.log", "w"), stderr=subprocess.STDOUT,
                               timeout=110 * 60 / acelerar + 120)
    finally:
        sim.terminate()
    assert motor.returncode == 0, f"el motor terminó con código {motor.returncode} (ver {salida / 'motor.log'})"
    args = [sys.executable, str(RAIZ / "evaluacion" / "verificar.py"), "--log", str(salida / "registro.jsonl"),
            "--escenario", str(esc), "--verdad", str(verdad)]
    texto = subprocess.run(args, capture_output=True, text=True, check=True).stdout
    (salida / "verificar.txt").write_text(texto, encoding="utf-8")
    r = json.loads(subprocess.run(args + ["--json"], capture_output=True, text=True, check=True).stdout)
    (salida / "verificar.json").write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return r


def chequear(r: dict, escenario: str, inicio: float, salida: Path, falla: str = None) -> dict:
    res = r["resumen"]
    bloqueadas, total = (int(x) for x in res["fases_piratas_bloqueadas"].split(" de "))
    fases_en_ventana = [f for f in r["fases"] if f["hasta_min"] > inicio]
    chequeos = {
        "registro_completo_hasta_110": r["log_hasta_min"] >= 110,
        "todas_las_fases_en_juego_bloqueadas": all(f["primer_bloqueo_min"] is not None for f in fases_en_ventana),
        "sin_ordenes_fuera_de_turno": res["ordenes_firmadas_fuera_de_turno"] == 0,
        "sin_bloqueos_ip_post_partido": res["bloqueos_ip_activos_post_partido"] == 0,
        "sin_falsos_positivos": res["bloqueos_falsos_positivos"] == 0,
        "sin_ordenes_rechazadas": res["ordenes_rechazadas"] == 0,
        "reclamos_resueltos": res["reclamos_resueltos_por_levantamiento"] == res["reclamos"],
    }
    if falla is None:
        chequeos["sin_dano_colateral"] = res["bloqueos_con_dano_colateral"] == 0
        chequeos["sin_dominios_legitimos_afectados"] = res["dominios_legitimos_afectados"] == 0
    else:
        # Con la falla inyectada el colateral es deliberado: se exige que haya reclamos, que se resuelvan y que
        # cada orden IP con colateral quede levantada (el verificador informa cuántos minutos estuvo activa).
        chequeos["hubo_reclamos"] = res["reclamos"] > 0
        chequeos["colateral_levantado"] = all(c["minutos_activo"] < 105 - inicio for c in r["dano_colateral"])
    aud = [json.loads(l) for l in (salida / "auditoria.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    acciones = {e["accion"] for e in aud}
    if res["ordenes_fallidas"]:
        chequeos["fallidas_reintentadas"] = "orden_reenviada" in acciones
    if inicio < 50 < 105:
        chequeos["cambio_de_turno_ratificado"] = {"cambio_de_turno", "turno_asumido"} <= acciones
    from plataforma.motor.exportar import verificar_cadena
    chequeos["auditoria_interna_integra"] = verificar_cadena(salida / "auditoria.jsonl") == len(aud)
    resumen = {"escenario": escenario, "falla_inyectada": falla, "inicio_min": inicio, "fases": f"{bloqueadas} de {total}",
               "resumen_verificador": res, "chequeos": chequeos}
    (salida / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return resumen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--escenario", choices=sorted(ESCENARIOS), default="practica")
    ap.add_argument("--acelerar", type=float, default=20.0)
    ap.add_argument("--inicio-min", type=float, default=0.0)
    ap.add_argument("--salida", type=Path, default=Path("salida/e2e"))
    ap.add_argument("--falla", choices=sorted(FALLAS), default=None, help="SOLO PRUEBAS: falla inyectada")
    a = ap.parse_args()
    r = correr(a.escenario, a.acelerar, a.inicio_min, a.salida, a.falla)
    resumen = chequear(r, a.escenario, a.inicio_min, a.salida, a.falla)
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    fallidos = [k for k, ok in resumen["chequeos"].items() if not ok]
    assert not fallidos, f"chequeos fallidos: {fallidos}"
    print("partido_completo: OK")


if __name__ == "__main__":
    main()
