"""Cliente HTTP del simulador (solo stdlib). Reintenta errores de red y 5xx; los 4xx se devuelven tal cual."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional, Tuple


class ErrorRed(Exception):
    """El simulador no respondió después de los reintentos."""


class ClienteSimulador:
    def __init__(self, base: str, timeout: float = 5.0, reintentos: int = 3, espera: float = 0.3):
        url = urllib.parse.urlsplit(base.rstrip("/"))
        if url.hostname == "localhost":
            # En Windows "localhost" prueba primero ::1 y el simulador escucha solo en IPv4: ~2 s perdidos por pedido.
            url = url._replace(netloc="127.0.0.1" + (f":{url.port}" if url.port else ""))
        self.base = urllib.parse.urlunsplit(url)
        self.timeout = timeout
        self.reintentos = reintentos
        self.espera = espera

    def _pedir(self, metodo: str, ruta: str, cuerpo: Optional[dict] = None) -> Tuple[int, Any]:
        datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
        ultimo: Optional[Exception] = None
        for intento in range(self.reintentos):
            req = urllib.request.Request(self.base + ruta, data=datos, method=metodo,
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return r.status, json.loads(r.read() or b"null")
            except urllib.error.HTTPError as e:
                try:
                    contenido = json.loads(e.read() or b"null")
                except ValueError:
                    contenido = {"error": f"HTTP {e.code}"}
                if e.code < 500:
                    return e.code, contenido
                ultimo = e
            except (urllib.error.URLError, OSError, ValueError) as e:
                ultimo = e
            time.sleep(self.espera * (intento + 1))
        raise ErrorRed(f"{metodo} {ruta}: {ultimo}")

    def get(self, ruta: str) -> Tuple[int, Any]:
        return self._pedir("GET", ruta)

    def post(self, ruta: str, cuerpo: dict) -> Tuple[int, Any]:
        return self._pedir("POST", ruta, cuerpo)

    def get_ok(self, ruta: str) -> Any:
        estado, datos = self.get(ruta)
        if estado != 200:
            raise ErrorRed(f"GET {ruta}: HTTP {estado} {datos}")
        return datos
