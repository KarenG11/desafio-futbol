"""T01 — Cerebro: agrupa detecciones en casos, las clasifica y recomienda IP o dominio.

Reglas (contratos.md §2 y diseno.md §2):
1. Un caso es el par (host_stream, ip_servidor). Una repetición se suma al caso; una mudanza es un caso nuevo.
2. Marca de agua contra GET /partido: sin_marca | otra_senal | licenciatario_legal | pirata.
   Una marca de licenciatario fuera de sus dominios autorizados es pirata (retransmite su señal).
3. Se bloquea la IP solo con evidencia positiva de que es exclusiva del sitio pirata; ante cualquier duda, dominio.
   El sufijo común de los dominios es necesario pero no alcanza (un hosting puede dar subdominios propios a sus
   clientes: panaderia.hostcomun.test y pirata.hostcomun.test). Ver `_riesgo_colateral`.

El cerebro no habla con la red: el motor le pasa `consultar_dns(ip)` (GET /dns-pasivo?ip=, None si 404).
"""
from typing import Callable, Dict, List, Optional, Tuple

from plataforma.contratos import Caso, Deteccion, DnsPorIp, Partido, sitio_de

ConsultarDns = Callable[[str], Optional[DnsPorIp]]


def _host_autorizado(host: str, dominios: List[str]) -> bool:
    host = host.lower().rstrip(".")
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in dominios)


# Palabras del nombre del ASN que indican infraestructura compartida entre clientes (hosting compartido, CDN, nube,
# revendedores): ahí una IP casi nunca es de un solo titular.
INDICIOS_INFRA_COMPARTIDA = ("compartid", "shared", "cdn", "nube", "cloud", "revend", "reseller", "virtual",
                             "multi", "colocation", "proxy")


def _infra_compartida(organizacion: str) -> Optional[str]:
    nombre = organizacion.lower()
    return next((i for i in INDICIOS_INFRA_COMPARTIDA if i in nombre), None)


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
        self._ips_compartidas: Dict[str, str] = {}   # ip -> motivo (p. ej. un reclamo verificado)

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

    def marcar_ip_compartida(self, ip: str, motivo: str) -> None:
        """Después de un reclamo verificado la IP no vuelve a recomendarse para bloqueo, en ningún caso."""
        self._ips_compartidas[ip] = motivo
        for c in self._casos.values():
            if c["ip"] == ip and c["tipo_recomendado"] == "ip":
                c.update(ip_compartida=True, tipo_recomendado="dominio", motivo_tipo=motivo)

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

    def _riesgo_colateral(self, host: str, ip: str, asn_deteccion: Optional[int] = None
                          ) -> Tuple[Optional[DnsPorIp], bool, str, str]:
        """(dns, ip_compartida, tipo_recomendado, motivo_tipo).

        La IP se recomienda solo si TODAS las señales indican un único titular; si una falla o falta, dominio:
        1. hay DNS pasivo con dominios;  2. todos son del mismo sitio que el host (dominio registrable);
        3. el ASN tiene titular conocido y no es hosting compartido/CDN/nube;  4. el ASN de la detección coincide
        con el del DNS;  5. ningún dominio de la IP es de un licenciatario o de un caso no pirata;
        6. la IP no tuvo reclamos verificados.
        """
        try:
            dns = self._dns_de(ip)
        except Exception:  # el DNS pasivo caído no puede frenar el circuito: se va a lo seguro
            self._dns.pop(ip, None)
            dns = None
        if dns is None or not dns.get("dominios"):
            return (None, True, "dominio",
                    f"No hay datos de DNS pasivo para {ip}: por precaución se bloquea solo {host}")
        dominios = sorted({d.lower().rstrip(".") for d in dns["dominios"]})
        sitio = sitio_de(host)
        ajenos = [d for d in dominios if sitio_de(d) != sitio]
        if ajenos:
            muestra = ", ".join(ajenos[:3]) + (f" y {len(ajenos) - 3} más" if len(ajenos) > 3 else "")
            return (dns, True, "dominio",
                    f"La IP {ip} aloja {len(ajenos)} sitio(s) de terceros ({muestra}): se bloquea solo {host}")
        if ip in self._ips_compartidas:
            return dns, True, "dominio", self._ips_compartidas[ip]
        org = (dns.get("organizacion") or "").strip()
        if not org:
            return (dns, True, "dominio",
                    f"No se conoce el titular del ASN de {ip}: no se puede descartar que la IP sea compartida; "
                    f"se bloquea solo {host}")
        indicio = _infra_compartida(org)
        if indicio:
            return (dns, True, "dominio",
                    f"La IP {ip} es de {org} (infraestructura compartida: '{indicio}'). Los {len(dominios)} dominios "
                    f"comparten el sufijo {sitio}, pero eso no prueba un único titular: se bloquea solo {host}")
        if asn_deteccion is not None and dns.get("asn") is not None and asn_deteccion != dns["asn"]:
            return (dns, True, "dominio",
                    f"El ASN de la detección ({asn_deteccion}) no coincide con el del DNS pasivo ({dns['asn']}): "
                    f"datos inconsistentes, se bloquea solo {host}")
        legitimos = [d for d in dominios if self._licenciatario_del_dominio(d) is not None
                     or any(c["host"] == d and c["clasificacion"] != "pirata" for c in self._casos.values())]
        if legitimos:
            return (dns, True, "dominio",
                    f"La IP {ip} aloja dominios que no son piratas ({', '.join(legitimos[:3])}): se bloquea solo {host}")
        return (dns, False, "ip",
                f"Todos los dominios de la IP {ip} son de {sitio} y el ASN es de {org} (hosting no compartido): "
                "se bloquea la IP")

    def _nuevo_caso(self, d: Deteccion) -> Caso:
        host = d["host_stream"].lower()
        ip = d["ip_servidor"]
        marca = d.get("marca_de_agua_extraida") or None
        clasificacion, marca_origen, motivo_clas = self._clasificar(marca, host)
        dns, compartida, tipo, motivo_tipo = self._riesgo_colateral(host, ip, d.get("asn"))
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
