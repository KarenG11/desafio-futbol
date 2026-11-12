"""Ingreso de los jueces: contraseñas de demostración y sesiones firmadas (solo biblioteca estándar).

Cada juez entra con su usuario (su id del simulador, p. ej. jueza-laura-ficticia) y su contraseña. Las contraseñas no
se guardan en ningún lado: se derivan del secreto JUEZ_PIN y del usuario, así funcionan también con los jueces de un
escenario nuevo. La sesión es un token firmado con HMAC que vence a las 12 horas; la API toma de ahí quién firma.

Para ver las contraseñas de los jueces (pide JUEZ_PIN sin mostrarlo si no está en el entorno):

    py -m plataforma.claves                 # jueces de datos/juzgados.json
    py -m plataforma.claves juez-x juez-y   # jueces de otro escenario
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

DURACION_S = 12 * 3600


def _secreto() -> bytes:
    return os.environ.get("JUEZ_PIN", "").encode()


def clave_de(juez_id: str) -> str:
    """Contraseña de demostración del juez: 10 caracteres derivados de JUEZ_PIN y su usuario."""
    crudo = hmac.new(_secreto(), f"clave|{juez_id}".encode(), hashlib.sha256).digest()
    return base64.b32encode(crudo).decode().lower()[:10]


def clave_valida(juez_id: str, clave: str) -> bool:
    return bool(_secreto()) and bool(juez_id) and hmac.compare_digest(clave_de(juez_id).encode(), (clave or "").strip().lower().encode())


def emitir_token(juez_id: str, ahora: Optional[float] = None) -> str:
    vence = int((ahora or time.time()) + DURACION_S)
    cuerpo = f"{juez_id}|{vence}"
    firma = hmac.new(_secreto(), f"token|{cuerpo}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{cuerpo}|{firma}".encode()).decode()


def leer_token(token: Optional[str], ahora: Optional[float] = None) -> Optional[str]:
    """Devuelve el juez del token si la firma es válida y no venció; si no, None."""
    if not token or not _secreto():
        return None
    try:
        juez_id, vence, firma = base64.urlsafe_b64decode(token.encode()).decode().rsplit("|", 2)
    except Exception:
        return None
    esperada = hmac.new(_secreto(), f"token|{juez_id}|{vence}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(esperada, firma) or int(vence) < (ahora or time.time()):
        return None
    return juez_id


def main() -> None:
    if not os.environ.get("JUEZ_PIN"):
        import getpass
        os.environ["JUEZ_PIN"] = getpass.getpass("JUEZ_PIN (el secreto del deploy; con --local es 1234): ")
    ids = sys.argv[1:]
    nombres = {}
    if not ids:
        datos = json.loads((Path(__file__).resolve().parents[1] / "datos" / "juzgados.json").read_text(encoding="utf-8"))
        for jz in datos["juzgados"]:
            for j in jz["jueces"]:
                ids.append(j["id"]); nombres[j["id"]] = j.get("nombre", "")
    for juez_id in ids:
        print(f"{nombres.get(juez_id, juez_id):24s} usuario: {juez_id:24s} contraseña: {clave_de(juez_id)}")


if __name__ == "__main__":
    main()
