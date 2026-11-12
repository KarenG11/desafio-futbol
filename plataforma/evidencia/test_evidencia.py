"""Pruebas de evidencia (T03) con asserts: hash de captura, hash de expediente y cadena de auditoría."""
import json
import os

from plataforma.contratos import EJEMPLO_CASO, EJEMPLO_DETECCION, HASH_INICIAL, hash_expediente, sha256_captura
from plataforma.evidencia.gestor import GestorEvidencia

RUTA = "salida/test_auditoria.jsonl"


def probar():
    os.makedirs("salida", exist_ok=True)
    recibidos = []
    gestor = GestorEvidencia(ruta_auditoria=RUTA, reiniciar=True, al_registrar=recibidos.append)
    exp = gestor.crear_expediente(EJEMPLO_CASO, EJEMPLO_DETECCION, "practica-01", 2.1, vence_propuesto_min=105)
    assert exp["expediente_id"] == "EXP-2026-000001"
    assert exp["vence_propuesto_min"] == 105
    assert exp["capturas"][0]["sha256"] == sha256_captura(EJEMPLO_DETECCION["captura"]["contenido_b64"])
    assert exp["hash"] == hash_expediente(exp), "hash del expediente"
    alterado = dict(exp, caso=dict(exp["caso"], ip="203.0.113.99"))
    assert hash_expediente(alterado) != exp["hash"], "alterar el expediente cambia su hash"
    caso_vivo = dict(EJEMPLO_CASO, deteccion_ids=list(EJEMPLO_CASO["deteccion_ids"]))
    exp2 = gestor.crear_expediente(caso_vivo, EJEMPLO_DETECCION, "practica-01", 2.15)
    caso_vivo["deteccion_ids"].append("D-9999")          # el cerebro sigue sumando detecciones al caso
    assert exp2["hash"] == hash_expediente(exp2), "el expediente es una foto: no cambia si el caso sigue vivo"

    gestor.registrar_evento("motor", "pedido_creado", {"pedido_id": "P-001"}, 2.2)
    assert len(recibidos) == 3 and recibidos[0]["hash_prev"] == HASH_INICIAL
    assert recibidos[2]["hash_prev"] == recibidos[1]["hash"]
    assert gestor.verificar_integridad() is True

    continuador = GestorEvidencia(ruta_auditoria=RUTA)
    assert continuador.seq_actual == 3 and continuador.ultimo_hash == recibidos[2]["hash"], "retoma la cadena"

    with open(RUTA, encoding="utf-8") as f:
        lineas = f.readlines()
    evento = json.loads(lineas[0])
    evento["actor"] = "hacker_infiltrado"
    lineas[0] = json.dumps(evento) + "\n"
    with open(RUTA, "w", encoding="utf-8") as f:
        f.writelines(lineas)
    assert gestor.verificar_integridad() is False, "la alteración tiene que detectarse"

    GestorEvidencia(ruta_auditoria=RUTA, reiniciar=True)
    assert not os.path.exists(RUTA), "reiniciar empieza una cadena nueva"
    print("test_evidencia: OK")


if __name__ == "__main__":
    probar()
