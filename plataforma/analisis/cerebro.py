"""T01 — Cerebro: agrupa detecciones en casos, las clasifica y recomienda IP o dominio.

Reglas (contratos.md §2 y diseno.md §2):
1. Un caso es el par (host_stream, ip_servidor). Una repetición se suma al caso; una mudanza es un caso nuevo.
2. Marca de agua contra GET /partido: sin_marca | otra_senal | licenciatario_legal | pirata.
   Una marca de licenciatario fuera de sus dominios autorizados es pirata (retransmite su señal).
3. IP compartida si algún dominio de la IP es de otro sitio, o si el DNS pasivo no tiene datos -> dominio.

El cerebro no habla con la red: el motor le pasa `consultar_dns(ip)` (GET /dns-pasivo?ip=, None si 404).
"""
from typing import Callable, Dict, List, Optional, Tuple

from plataforma.contratos import Caso, Deteccion, DnsPorIp, Partido, sitio_de

ConsultarDns = Callable[[str], Optional[DnsPorIp]]


def _host_autorizado(host: str, dominios: List[str]) -> bool:
    host = host.lower().rstrip(".")
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in dominios)


def _prefijo_que_coincide(marca: str, prefijos: List[str]) -> Optional[str]:
    """El prefijo más largo tal que marca == prefijo o marca empieza con 'prefijo-'."""
    for prefijo in sorted(prefijos, key=len, reverse=True):
        if marca == prefijo or marca.startswith(prefijo + "-"):
            return prefijo
    return None


class Cerebro:
    def __init__(self, partido: Partido, consultar_dns: ConsultarDns):
        self.partido = partido
        self.consultar_dns = consultar_dns
        self._origen = {m["prefijo"].strip().upper(): m["origen"] for m in partido.get("marcas_de_agua_validas", [])}
        self._licenciatarios = {l["prefijo_marca"].strip().upper(): l for l in partido.get("licenciatarios", [])}
        self._casos: Dict[Tuple[str, str], Caso] = {}
        self._dns: Dict[str, Optional[DnsPorIp]] = {}

    # --- API para el motor ----------------------------------------------------------------

    def procesar(self, deteccion: Deteccion) -> Tuple[Caso, bool]:
        """Devuelve (caso, es_nuevo). Si es_nuevo y el caso es pirata, el motor arma expediente y pedido."""
        clave = (deteccion["host_stream"].lower(), deteccion["ip_servidor"])
        caso = self._casos.get(clave)
        if caso is not None:
            if deteccion["id"] not in caso["deteccion_ids"]:
                caso["deteccion_ids"].append(deteccion["id"])
            return caso, False
        caso = self._nuevo_caso(deteccion)
        self._casos[clave] = caso
        return caso, True

    def casos(self) -> List[Caso]:
        return list(self._casos.values())

    # --- internos -------------------------------------------------------------------------

    def _dns_de(self, ip: str) -> Optional[DnsPorIp]:
        if ip not in self._dns:
            self._dns[ip] = self.consultar_dns(ip)
        return self._dns[ip]

    def _licenciatario_del_dominio(self, host: str) -> Optional[dict]:
        for lic in self._licenciatarios.values():
            if _host_autorizado(host, lic["dominios_autorizados"]):
                return lic
        return None

    def _clasificar(self, marca: Optional[str], host: str) -> Tuple[str, Optional[str], str]:
        """(clasificacion, marca_origen, motivo)."""
        marca = (marca or "").strip().upper()
        if not marca:
            return ("sin_marca", None,
                    "El video no trae marca de agua: no se puede probar que sea la señal del partido. Queda registrado")
        prefijo = _prefijo_que_coincide(marca, list(self._origen))
        if prefijo is None:
            return "otra_senal", None, f"La marca {marca} no corresponde a este partido"
        origen = self._origen[prefijo]
        dueno_del_dominio = self._licenciatario_del_dominio(host)
        if dueno_del_dominio is not None:
            # Un dominio autorizado de un licenciatario nunca se bloquea desde acá, aunque la marca sea otra:
            # bloquear al licenciatario es un falso positivo grave y una disputa de contrato, no piratería.
            if self._licenciatarios.get(prefijo) is dueno_del_dominio:
                return ("licenciatario_legal", origen,
                        f"{dueno_del_dominio['nombre']} retransmite con autorización en su propio dominio")
            return ("licenciatario_legal", origen,
                    f"Dominio autorizado de {dueno_del_dominio['nombre']} con una marca que no es la suya: "
                    "no se bloquea; se informa al titular de derechos")
        licenciatario = self._licenciatarios.get(prefijo)
        if licenciatario is not None:
            return ("pirata", origen,
                    f"Señal de {licenciatario['nombre']} retransmitida en un dominio que no es suyo")
        return "pirata", origen, "Lleva la marca de la señal oficial del partido y este dominio no está autorizado a transmitirla"

    def _riesgo_colateral(self, host: str, ip: str) -> Tuple[Optional[DnsPorIp], bool, str, str]:
        """(dns, ip_compartida, tipo_recomendado, motivo_tipo)."""
        try:
            dns = self._dns_de(ip)
        except Exception:  # el DNS pasivo caído no puede frenar el circuito: se va a lo seguro
            self._dns.pop(ip, None)
            dns = None
        sitio = sitio_de(host)
        if dns is None or not dns.get("dominios"):
            return (None, True, "dominio",
                    f"No hay datos de DNS pasivo para {ip}: por precaución se bloquea solo {host}")
        ajenos = sorted({d.lower() for d in dns["dominios"] if sitio_de(d) != sitio})
        if ajenos:
            muestra = ", ".join(ajenos[:3]) + (f" y {len(ajenos) - 3} más" if len(ajenos) > 3 else "")
            return (dns, True, "dominio",
                    f"La IP {ip} aloja {len(ajenos)} sitio(s) de terceros ({muestra}): se bloquea solo {host}")
        return dns, False, "ip", f"Todos los dominios de la IP {ip} son de {sitio}: se bloquea la IP"

    def _nuevo_caso(self, d: Deteccion) -> Caso:
        host = d["host_stream"].lower()
        ip = d["ip_servidor"]
        marca = d.get("marca_de_agua_extraida") or None
        clasificacion, marca_origen, motivo_clas = self._clasificar(marca, host)
        dns, compartida, tipo, motivo_tipo = self._riesgo_colateral(host, ip)
        return {
            "caso_id": f"C-{len(self._casos) + 1:03d}",
            "host": host,
            "ip": ip,
            "asn": d.get("asn") if d.get("asn") is not None else (dns or {}).get("asn"),
            "organizacion": (dns or {}).get("organizacion"),
            "sitio": sitio_de(host),
            "pagina": d.get("pagina", ""),
            "deteccion_ids": [d["id"]],
            "primer_minuto": d["minuto"],
            "marca": marca,
            "marca_origen": marca_origen,
            "clasificacion": clasificacion,
            "motivo_clasificacion": motivo_clas,
            "dominios_en_ip": list(dns["dominios"]) if dns else [],
            "ip_compartida": compartida,
            "tipo_recomendado": tipo,
            "motivo_tipo": motivo_tipo,
        }
