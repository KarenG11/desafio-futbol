import base64
import copy
import json
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from plataforma.contratos import (
    Caso, Deteccion, Expediente, EventoAuditoria,
    sha256_captura, hash_expediente, hash_evento_auditoria, HASH_INICIAL
)

class GestorEvidencia:
    def __init__(self, ruta_auditoria: str = "salida/auditoria_interna.jsonl", reiniciar: bool = False,
                 al_registrar: Optional[Callable[[Dict[str, Any]], None]] = None):
        """reiniciar=True empieza una cadena nueva (una por corrida); al_registrar recibe cada evento (p. ej. la base)."""
        self.ruta_auditoria = ruta_auditoria
        self.contador_expedientes = 1
        self.ultimo_hash = HASH_INICIAL
        self.seq_actual = 0
        self.al_registrar = al_registrar
        if reiniciar and os.path.exists(self.ruta_auditoria):
            os.remove(self.ruta_auditoria)
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

    def crear_expediente(self, caso: Caso, deteccion: Deteccion, partido_id: str, minuto_actual: float,
                         vence_propuesto_min: int = 105) -> Expediente:
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
            "caso": copy.deepcopy(caso),   # foto del caso al firmar: el cerebro lo sigue actualizando
            "capturas": [captura_exp],
            "promocion": deteccion.get("promocion", []),
            "vence_propuesto_min": int(vence_propuesto_min),
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
        os.makedirs(os.path.dirname(self.ruta_auditoria) or ".", exist_ok=True)
        with open(self.ruta_auditoria, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
        if self.al_registrar is not None:
            self.al_registrar(evento)

        return evento

    def verificar_integridad(self) -> bool:
        """Revisa que la cadena de auditoría no haya sido alterada."""
        if not os.path.exists(self.ruta_auditoria):
            print("No hay archivo de auditoría para verificar.")
            return True

        prev_hash_esperado = HASH_INICIAL
        
        with open(self.ruta_auditoria, "r", encoding="utf-8") as f:
            for num_linea, linea in enumerate(f, 1):
                if not linea.strip():
                    continue
                
                evento = json.loads(linea)
                
                # 1. Verificar que el enlace (hash_prev) apunte al evento anterior
                if evento["hash_prev"] != prev_hash_esperado:
                    print(f"❌ ALERTA: Cadena rota en la línea {num_linea} (seq {evento['seq']}). Alguien alteró el pasado.")
                    return False
                
                # 2. Re-calcular el hash del evento para ver si sus datos fueron cambiados
                hash_calculado = hash_evento_auditoria(evento)
                if evento["hash"] != hash_calculado:
                    print(f"❌ ALERTA: Datos alterados en la línea {num_linea} (seq {evento['seq']}).")
                    return False
                
                prev_hash_esperado = evento["hash"]
                
        print("✅ Integridad verificada: la cadena de auditoría es válida y no fue alterada.")
        return True