import base64
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

# Importamos las herramientas que hizo Alejo en contratos.py
from plataforma.contratos import (
    Caso, Deteccion, Expediente, EventoAuditoria,
    sha256_captura, hash_expediente, hash_evento_auditoria, HASH_INICIAL
)

class GestorEvidencia:
    def __init__(self, ruta_auditoria: str = "salida/auditoria_interna.jsonl"):
        self.ruta_auditoria = ruta_auditoria
        self.contador_expedientes = 1
        self.ultimo_hash = HASH_INICIAL
        self.seq_actual = 0
        self._cargar_estado_auditoria()

    def _cargar_estado_auditoria(self):
        """Si el archivo ya existe, recupera el último hash para seguir la cadena."""
        if os.path.exists(self.ruta_auditoria):
            with open(self.ruta_auditoria, "r", encoding="utf-8") as f:
                for linea in f:
                    if linea.strip():
                        evento = json.loads(linea)
                        self.ultimo_hash = evento["hash"]
                        self.seq_actual = evento["seq"]

    def crear_expediente(self, caso: Caso, deteccion: Deteccion, partido_id: str, minuto_actual: float) -> Expediente:
        """Arma el expediente legal con las capturas y calcula su hash de integridad."""
        
        # Procesamos la captura (base64 a binario y sacamos su hash)
        b64 = deteccion["captura"]["contenido_b64"]
        binario = base64.b64decode(b64)
        
        captura_exp = {
            "deteccion_id": deteccion["id"],
            "capturada_min": deteccion["captura"]["capturada_min"],
            "formato": deteccion["captura"]["formato"],
            "duracion_seg": deteccion["captura"]["duracion_seg"],
            "bytes": len(binario),
            "sha256": sha256_captura(b64)
        }

        # Armamos el expediente (sin el hash todavía)
        exp = {
            "expediente_id": f"EXP-2026-{self.contador_expedientes:06d}",
            "partido_id": partido_id,
            "caso": caso,
            "capturas": [captura_exp],
            "promocion": deteccion.get("promocion", []),
            "vence_propuesto_min": 105, # Según el MVP de Alejo
            "creado_min": minuto_actual,
            "creado_ts": datetime.now(timezone.utc).isoformat(),
        }
        
        # Calculamos el hash del expediente
        exp["hash"] = hash_expediente(exp)
        
        self.contador_expedientes += 1
        
        # Registramos en la auditoría
        self.registrar_evento(
            actor="evidencia", 
            accion="expediente_creado", 
            datos={"expediente_id": exp["expediente_id"], "caso_id": caso["caso_id"], "expediente_hash": exp["hash"]},
            minuto=minuto_actual
        )
        
        return exp # type: ignore

    def registrar_evento(self, actor: str, accion: str, datos: Dict[str, Any], minuto: float):
        """Agrega un evento a la cadena inalterable de auditoría."""
        self.seq_actual += 1
        evento = {
            "seq": self.seq_actual,
            "min": minuto,
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "accion": accion,
            "datos": datos,
            "hash_prev": self.ultimo_hash,
        }
        
        # Calculamos el hash de ESTE evento usando el hash del anterior
        evento["hash"] = hash_evento_auditoria(evento)
        self.ultimo_hash = evento["hash"]
        
        # Guardamos en el archivo JSONL
        os.makedirs(os.path.dirname(self.ruta_auditoria), exist_ok=True)
        with open(self.ruta_auditoria, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento) + "\n")
            
        return evento