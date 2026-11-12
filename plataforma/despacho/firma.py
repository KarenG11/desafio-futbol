"""Firma de demostración (HMAC-SHA256 hex) con la clave_firma_demo del juez.

Las claves se leen SOLO de datos/juzgados.json (claves ficticias que provee la organización) y nunca
se guardan en la base, en la auditoría ni se muestran en la web. En producción esto sería un servicio
de firma digital del juez (ver entrega/propuesta_normativa.md).
"""
import hashlib
import hmac
import json
from pathlib import Path
from typing import Dict

from plataforma.contratos import mensaje_firma_levantar, mensaje_firma_orden

RAIZ = Path(__file__).resolve().parents[2]
RUTA_JUZGADOS = RAIZ / "datos" / "juzgados.json"


class Firmador:
    def __init__(self, ruta_juzgados: Path = RUTA_JUZGADOS):
        datos = json.loads(Path(ruta_juzgados).read_text(encoding="utf-8"))
        self._claves: Dict[str, str] = {}
        self.juzgado_de: Dict[str, str] = {}
        for juzgado in datos["juzgados"]:
            for juez in juzgado["jueces"]:
                self._claves[juez["id"]] = juez["clave_firma_demo"]
                self.juzgado_de[juez["id"]] = juzgado["id"]

    def conoce(self, juez_id: str) -> bool:
        return juez_id in self._claves

    def _hmac(self, juez_id: str, mensaje: str) -> str:
        return hmac.new(self._claves[juez_id].encode("utf-8"), mensaje.encode("utf-8"), hashlib.sha256).hexdigest()

    def firmar_orden(self, payload: dict) -> str:
        return self._hmac(payload["juez_id"], mensaje_firma_orden(payload))

    def firmar_levantar(self, orden_id: str, juez_id: str) -> str:
        return self._hmac(juez_id, mensaje_firma_levantar(orden_id, juez_id))

    def __repr__(self) -> str:  # nunca imprimir claves
        return f"Firmador(jueces={sorted(self._claves)})"
