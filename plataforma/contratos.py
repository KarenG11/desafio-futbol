"""Contratos v1 entre las piezas de la plataforma (tarea T00).

Es la versión en código de `coordinacion/contratos.md`: las formas de los datos (TypedDict),
las constantes compartidas, unas funciones de referencia para hashes y textos de firma, y
datos de ejemplo coherentes entre sí para que cada pieza (T01–T07) arranque con mocks sin
esperar a las demás.

- Solo stdlib, Python 3.9+. Importarlo no hace I/O, no lee archivos ni claves.
- Los TypedDict documentan y sirven para chequeo estático; en ejecución los datos son `dict` comunes.
- Los ejemplos son mocks: dominios .test/.example, IPs de documentación, jueces ficticios.
  Las firmas de los ejemplos son de mentira ("ab" * 32). Las claves de demo viven solo en
  `datos/juzgados.json` y no se copian acá.
- `python -m plataforma.contratos` recalcula los hashes de los ejemplos y verifica que cierren.
- Los ejemplos comparten objetos anidados (el expediente contiene EJEMPLO_CASO tal cual).
  Si los vas a modificar en un test, copialos antes: `copy.deepcopy(EJEMPLO_PEDIDO)`.

Uso típico:
    from plataforma.contratos import EJEMPLO_CASO, EJEMPLO_EXPEDIENTE, EJEMPLO_PEDIDO
"""
import base64
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional, TypedDict

VERSION_CONTRATOS = "v1.5"

# =====================================================================================
# Constantes
# =====================================================================================

GRACIA_MIN = 5
"""Minutos después de fin_min en los que el simulador cierra la ventana (evento ventana_cerrada)."""

TIPOS_BLOQUEO = ("ip", "dominio")
TipoBloqueo = Literal["ip", "dominio"]

CLASIFICACIONES = ("pirata", "licenciatario_legal", "otra_senal", "sin_marca")
"""Clasificación de un Caso (T01). Solo `pirata` va al juez."""
Clasificacion = Literal["pirata", "licenciatario_legal", "otra_senal", "sin_marca"]

ESTADOS_PEDIDO = ("pendiente", "aprobado", "rechazado")
EstadoPedido = Literal["pendiente", "aprobado", "rechazado"]

ESTADOS_ORDEN_SIM = ("recibida", "aplicada", "vencida", "levantada", "fallida")
"""Estados que devuelve el simulador para una orden guardada."""
ESTADOS_ORDEN = ESTADOS_ORDEN_SIM + ("rechazada",)
"""Estados de nuestro seguimiento: los del simulador + `rechazada` (el POST volvió 4xx y no quedó guardada)."""
ESTADOS_ORDEN_ACTIVA = ("recibida", "aplicada")
"""Únicos estados en los que el simulador acepta levantar (si no, 409)."""
ESTADOS_ORDEN_FINAL = ("vencida", "levantada", "fallida", "rechazada")
ESTADOS_ORDEN_REENVIAR = ("fallida", "rechazada")
"""Hay que reenviar con orden_id NUEVO (en `rechazada`, solo si el motivo se puede corregir)."""
EstadoOrden = Literal["recibida", "aplicada", "vencida", "levantada", "fallida", "rechazada"]

ESTADOS_RECLAMO = ("pendiente", "descartado", "levantado")
"""pendiente = verificado, espera al juez · descartado = no corresponde · levantado = el juez levantó."""
EstadoReclamo = Literal["pendiente", "descartado", "levantado"]

ESTADOS_PUBLICOS = ("en_curso", "vigente", "vencido", "levantado")
"""Estado de una entrada del registro público (T07). Ver contratos.md §9."""
EstadoPublico = Literal["en_curso", "vigente", "vencido", "levantado"]

EVENTOS_REGISTRO = (
    "simulacion_iniciada", "orden_recibida", "orden_aplicada", "orden_fallida", "orden_vencida",
    "orden_levantada", "orden_rechazada", "reclamo_emitido", "partido_finalizado", "ventana_cerrada",
)
"""Eventos que el SIMULADOR escribe en salida/registro.jsonl (lo lee evaluacion/verificar.py)."""

ACCIONES_AUDITORIA = (
    # análisis (T01)
    "caso_creado", "caso_descartado",
    # evidencia (T03)
    "expediente_creado",
    # motor / juez (T05, T04)
    "pedido_creado", "pedido_aprobado", "pedido_rechazado",
    # despacho (T02)
    "orden_enviada", "orden_rechazada", "orden_aplicada", "orden_fallida", "orden_reenviada",
    "orden_vencida", "orden_levantada",
    # reclamos (T06)
    "reclamo_recibido", "reclamo_descartado", "reclamo_levantado",
    # motor
    "motor_iniciado", "partido_finalizado",
    # agregadas al implementar motor y despacho
    "deteccion_repetida", "cambio_de_turno", "turno_asumido", "orden_recibida", "orden_en_espera",
    "orden_no_enviada", "orden_abandonada", "orden_error_red",
)
"""Acciones de la auditoría INTERNA (T03). Se pueden agregar más; avisar en el buzón."""

ACTORES_AUDITORIA = ("motor", "analisis", "evidencia", "despacho", "reclamos", "juez:<juez_id>", "proveedor:<id>")

CAMPOS_ORDEN = ("orden_id", "expediente_id", "tipo", "objetivo", "vence_min", "juzgado_id", "juez_id", "firma")
"""Campos obligatorios del POST /proveedores/<id>/ordenes (igual que simulador/servidor.py)."""
CAMPOS_LEVANTAR = ("juez_id", "firma", "motivo")
"""Cuerpo del POST /proveedores/<id>/ordenes/<orden_id>/levantar."""

MENSAJE_FIRMA_ORDEN = "{orden_id}|{tipo}|{objetivo}|{vence_min}|{juez_id}"
"""Texto que se firma con HMAC-SHA256 (hex) y la clave_firma_demo del juez. Uso: .format(**payload)."""
MENSAJE_FIRMA_LEVANTAR = "LEVANTAR|{orden_id}|{juez_id}"
"""Texto que se firma para levantar una orden."""

ORDEN_ID_FORMATO = "ord-{corrida}-{pedido_id}-{proveedor_id}-{intento}"
"""`corrida` = 4 hex al azar al arrancar el motor, para no chocar (409) si se reinicia la plataforma."""

HASH_INICIAL = "0" * 64
"""hash_prev del primer evento de la auditoría interna."""


# =====================================================================================
# Funciones de referencia (puras, sin I/O). T03 y T02 pueden usarlas tal cual.
# =====================================================================================

def json_canonico(obj: Any) -> bytes:
    """JSON canónico para hashear: claves ordenadas, sin espacios, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def sha256_captura(contenido_b64: str) -> str:
    """SHA-256 del binario DECODIFICADO de captura.contenido_b64 (no del texto base64)."""
    return sha256_hex(base64.b64decode(contenido_b64))


def hash_expediente(expediente: Dict[str, Any]) -> str:
    """sha256 del JSON canónico del expediente sin el campo "hash"."""
    return sha256_hex(json_canonico({k: v for k, v in expediente.items() if k != "hash"}))


def hash_evento_auditoria(evento: Dict[str, Any]) -> str:
    """sha256(hash_prev + JSON canónico del evento sin "hash"). El evento incluye su hash_prev."""
    sin_hash = {k: v for k, v in evento.items() if k != "hash"}
    return sha256_hex(evento["hash_prev"].encode("utf-8") + json_canonico(sin_hash))


def mensaje_firma_orden(payload: Dict[str, Any]) -> str:
    return MENSAJE_FIRMA_ORDEN.format(**payload)


def mensaje_firma_levantar(orden_id: str, juez_id: str) -> str:
    return MENSAJE_FIRMA_LEVANTAR.format(orden_id=orden_id, juez_id=juez_id)


def vence_min_para(fin_min: float) -> int:
    """Vencimiento del MVP para IP y dominio: el fin del partido, entero (el simulador exige int)."""
    return int(fin_min)


# Sufijos donde cada subdominio es de un dueño distinto (subconjunto de la Public Suffix List).
# Sin esto, "panaderia.com.ar" y "pirata.com.ar" serían el "mismo sitio" (com.ar), y dos clientes de
# una plataforma de hosting (a.vercel.app, b.vercel.app) también: se bloquearía una IP compartida.
SUFIJOS_PUBLICOS = frozenset({
    # Argentina y región
    "com.ar", "gob.ar", "gov.ar", "org.ar", "net.ar", "edu.ar", "int.ar", "mil.ar", "tur.ar", "musica.ar",
    "com.br", "net.br", "org.br", "gov.br", "com.mx", "gob.mx", "org.mx", "net.mx", "com.co", "gov.co",
    "com.pe", "gob.pe", "com.uy", "gub.uy", "com.py", "gov.py", "com.bo", "gob.bo", "com.ec", "gob.ec",
    "com.ve", "gob.ve", "co.uk", "org.uk", "com.es", "com.au",
    # plataformas de hosting/CDN donde cada subdominio es un cliente distinto
    "github.io", "gitlab.io", "vercel.app", "netlify.app", "pages.dev", "workers.dev", "web.app",
    "firebaseapp.com", "appspot.com", "herokuapp.com", "azurewebsites.net", "cloudfront.net",
    "blogspot.com", "wordpress.com", "onrender.com", "fly.dev", "glitch.me", "repl.co", "ngrok.io",
    "ngrok-free.app", "trycloudflare.com", "duckdns.org", "no-ip.org", "ddns.net",
})


def sitio_de(host: str) -> str:
    """Sitio = dominio registrable del host: s1.pelotaya.test -> pelotaya.test, www.diario.com.ar -> diario.com.ar,
    tienda.vercel.app -> tienda.vercel.app. Usa SUFIJOS_PUBLICOS (subconjunto de la Public Suffix List)."""
    etiquetas = host.lower().strip().rstrip(".").split(".")
    if len(etiquetas) >= 3 and ".".join(etiquetas[-2:]) in SUFIJOS_PUBLICOS:
        return ".".join(etiquetas[-3:])
    return ".".join(etiquetas[-2:])


# =====================================================================================
# 1. Formas del simulador (API de afuera). Nombres de campos EXACTOS del simulador.
# =====================================================================================

class Captura(TypedDict):
    capturada_min: float
    formato: str                      # p. ej. "mpegts"
    duracion_seg: int
    contenido_b64: str


class Promocion(TypedDict):
    red: str                          # "x" | "discord" | "telegram" | ...
    url: str
    minuto: float


class Deteccion(TypedDict):
    id: str                           # "D-0001"
    minuto: float
    pagina: str
    stream_url: str
    host_stream: str
    ip_servidor: str
    asn: int
    marca_de_agua_extraida: Optional[str]   # puede venir vacía/None -> sin_marca
    captura: Captura
    promocion: List[Promocion]


class RespuestaDetecciones(TypedDict):
    minuto_actual: float              # redondeado a 3; usarlo como próximo ?desde=
    detecciones: List[Deteccion]


class EstadoSim(TypedDict):
    partido: str                      # id del partido
    minuto_actual: float              # redondeado a 2
    fin_min: float
    finalizado: bool
    acelerar: float
    jueces_de_turno: List[str]        # juez_id


class MarcaValida(TypedDict):
    prefijo: str
    origen: str


class Licenciatario(TypedDict):
    nombre: str
    prefijo_marca: str
    dominios_autorizados: List[str]


class Partido(TypedDict):
    id: str
    nombre: str
    titular_derechos: str
    inicio_iso: str
    fin_min: int
    marcas_de_agua_validas: List[MarcaValida]
    licenciatarios: List[Licenciatario]


class DnsPorIp(TypedDict):            # GET /dns-pasivo?ip=  (404 si no hay registros)
    ip: str
    asn: Optional[int]
    organizacion: Optional[str]
    dominios: List[str]


class IpDeDominio(TypedDict):
    ip: str
    asn: Optional[int]
    organizacion: Optional[str]


class DnsPorDominio(TypedDict):       # GET /dns-pasivo?dominio=  (404 si no hay registros)
    dominio: str
    ips: List[IpDeDominio]


class ProveedorSim(TypedDict):        # elemento de GET /proveedores (lista, sin "comportamiento")
    id: str
    nombre: str
    tamano: str                       # grande | mediano | chico
    clientes: int
    capacidades: List[str]            # subconjunto de TIPOS_BLOQUEO
    ordenes: str                      # ruta: "/proveedores/<id>/ordenes"


class JuezSim(TypedDict):
    id: str
    nombre: str


class JuzgadoSim(TypedDict):
    id: str
    nombre: str
    jurisdiccion: str
    jueces: List[JuezSim]             # SIN claves


class Turno(TypedDict):
    juez_id: str
    desde_min: float                  # inclusive
    hasta_min: float                  # exclusive


class JuzgadosSim(TypedDict):         # GET /juzgados
    juzgados: List[JuzgadoSim]
    turnos: List[Turno]
    de_turno_ahora: List[str]


class ReclamoSim(TypedDict):          # elemento de GET /reclamos -> "reclamos"
    id: str                           # "R-001"
    minuto: float
    dominio: str                      # el sitio legítimo que reclama
    proveedor: str                    # id del proveedor donde está bloqueado
    mensaje: str
    # OJO: NO trae orden_id. Hay que correlacionar (contratos.md §8).


class RespuestaReclamos(TypedDict):
    minuto_actual: float
    reclamos: List[ReclamoSim]


class OrdenPayload(TypedDict):        # POST /proveedores/<id>/ordenes
    orden_id: str                     # único POR proveedor
    expediente_id: str
    tipo: TipoBloqueo
    objetivo: str                     # IP, o host_stream si tipo == "dominio"
    vence_min: int                    # int (no float, no bool), > minuto actual
    juzgado_id: str
    juez_id: str
    firma: str                        # HMAC-SHA256 hex de MENSAJE_FIRMA_ORDEN


class RespuestaOrden(TypedDict):      # 202
    orden_id: str
    estado: str                       # "recibida"
    consultar: str                    # "/proveedores/<id>/ordenes/<orden_id>"


class _VistaOrdenBase(TypedDict):
    orden_id: str
    expediente_id: str
    tipo: TipoBloqueo
    objetivo: str
    vence_min: int
    juzgado_id: str
    juez_id: str
    estado: str                       # ESTADOS_ORDEN_SIM
    recibida_min: float


class VistaOrdenSim(_VistaOrdenBase, total=False):
    """GET /proveedores/<id>/ordenes/<orden_id> (y respuesta 200 de levantar). Sin firma."""
    aplicada_min: float               # si llegó a aplicarse
    motivo: str                       # si quedó fallida
    finalizada_min: float             # si venció o se levantó


class LevantarReq(TypedDict):         # POST /proveedores/<id>/ordenes/<orden_id>/levantar
    juez_id: str
    firma: str                        # HMAC-SHA256 hex de MENSAJE_FIRMA_LEVANTAR
    motivo: str


class ErrorSim(TypedDict):            # 400/403/404/409/422
    error: str


class _EventoRegistroBase(TypedDict):
    min: float                        # 3 decimales
    evento: str                       # EVENTOS_REGISTRO


class EventoRegistro(_EventoRegistroBase, total=False):
    """Una línea de salida/registro.jsonl (lo escribe el SIMULADOR, no nosotros).
    Qué campos trae cada evento: ver contratos.md §1.11."""
    escenario: str
    acelerar: float
    fin_min: float
    proveedor: str
    orden_id: Optional[str]
    expediente_id: str
    tipo: TipoBloqueo
    objetivo: str
    vence_min: int
    juzgado_id: str
    juez_id: str
    juez_de_turno: bool
    motivo: Optional[str]
    id: str
    dominio: str
    mensaje: str
    ordenes_activas: List[Dict[str, str]]   # [{proveedor, orden_id, tipo, objetivo}]


# =====================================================================================
# 2–9. Contratos internos (los nuestros). Todas las claves están siempre; si no aplica, None.
# =====================================================================================

class Caso(TypedDict):                # T01
    caso_id: str                      # "C-001"
    host: str                         # <- deteccion.host_stream (lo que se bloquea por dominio)
    ip: str                           # <- deteccion.ip_servidor
    asn: int                          # <- deteccion.asn
    organizacion: Optional[str]       # <- dns-pasivo?ip= .organizacion
    sitio: str                        # sitio_de(host): agrupa mudanzas del mismo sitio
    pagina: str
    deteccion_ids: List[str]          # <- deteccion.id (todas las del mismo host + IP)
    primer_minuto: float
    marca: Optional[str]              # <- deteccion.marca_de_agua_extraida
    marca_origen: Optional[str]       # origen del prefijo válido que coincidió (de GET /partido)
    clasificacion: Clasificacion
    motivo_clasificacion: str
    dominios_en_ip: List[str]         # <- dns-pasivo?ip= .dominios ([] si 404)
    ip_compartida: bool
    tipo_recomendado: TipoBloqueo
    motivo_tipo: str


class CapturaExpediente(TypedDict):   # T03
    deteccion_id: str
    capturada_min: float
    formato: str
    duracion_seg: int
    bytes: int                        # largo del binario decodificado
    sha256: str                       # sha256_captura(contenido_b64)


class Expediente(TypedDict):          # T03
    expediente_id: str                # "EXP-2026-000001"
    partido_id: str
    caso: Caso
    capturas: List[CapturaExpediente]
    promocion: List[Promocion]        # extra; [] si no hay
    vence_propuesto_min: int
    creado_min: float
    creado_ts: str                    # ISO 8601 con zona, reloj de la máquina
    hash: str                         # hash_expediente(expediente)


class ObjetivoPedido(TypedDict):
    proveedor_id: str
    tipo: TipoBloqueo                 # el que ESE proveedor acepta
    objetivo: str


class Pedido(TypedDict):              # T05 crea, T04 aprueba
    pedido_id: str                    # "P-001"
    expediente_id: str
    origen: str                       # "deteccion" | "reclamo:<reclamo_id>" (reemplazo)
    objetivos: List[ObjetivoPedido]   # uno por proveedor
    vence_min: int
    creado_min: float
    estado: EstadoPedido
    juez_id: Optional[str]            # se llenan al decidir
    juzgado_id: Optional[str]
    decidido_min: Optional[float]
    motivo_rechazo: Optional[str]


class Orden(TypedDict):               # T02: seguimiento interno de una orden enviada
    orden_id: str
    pedido_id: str
    expediente_id: str
    proveedor_id: str
    tipo: TipoBloqueo
    objetivo: str
    vence_min: int
    juzgado_id: str
    juez_id: str                      # quien FIRMÓ este envío (de turno al enviar)
    estado: EstadoOrden
    intentos: int                     # nº de intento para (pedido, proveedor); 1 = primer envío
    reemplaza_a: Optional[str]        # orden_id del intento anterior (reintento)
    enviada_min: float
    recibida_min: Optional[float]
    aplicada_min: Optional[float]
    finalizada_min: Optional[float]   # vencida o levantada
    motivo: Optional[str]             # error del simulador (fallida/rechazada) o motivo de levantamiento
    consultar: Optional[str]          # ruta que devolvió el 202


class EventoAuditoria(TypedDict):     # T03: auditoría INTERNA (no es salida/registro.jsonl)
    seq: int
    min: float
    ts: str
    actor: str                        # ACTORES_AUDITORIA
    accion: str                       # ACCIONES_AUDITORIA
    datos: Dict[str, Any]
    hash_prev: str
    hash: str


class Reclamo(TypedDict):             # T06: gestión interna de un reclamo del feed
    reclamo_id: str                   # <- ReclamoSim.id
    minuto: float
    dominio: str
    proveedor_id: str                 # <- ReclamoSim.proveedor
    mensaje: str
    estado: EstadoReclamo
    verificacion: str                 # por qué es (o no) procedente, en lenguaje claro
    orden_ids: List[str]              # órdenes nuestras correlacionadas (en ese proveedor)
    caso_id: Optional[str]
    juez_id: Optional[str]
    decidido_min: Optional[float]
    ordenes_levantadas: List[Dict[str, str]]   # [{proveedor_id, orden_id}] en TODOS los proveedores
    pedido_reemplazo_id: Optional[str]


class EstadoProveedorPublico(TypedDict):
    proveedor_id: str
    estado: EstadoOrden
    aplicada_min: Optional[float]
    finalizada_min: Optional[float]


class EntradaPublica(TypedDict):      # T07: una por (pedido, tipo, objetivo)
    entrada_id: str                   # "<pedido_id>/<tipo>/<objetivo>"
    pedido_id: str
    expediente_id: str
    partido_id: str
    tipo: TipoBloqueo
    objetivo: str
    motivo: str
    juez_id: str
    juez_nombre: str
    juzgado_id: str
    juzgado_nombre: str
    ordenado_min: float               # Pedido.decidido_min
    vence_min: int
    estado: EstadoPublico
    finalizado_min: Optional[float]
    motivo_fin: Optional[str]         # p. ej. motivo del levantamiento
    proveedores: List[EstadoProveedorPublico]


# --- API del motor (T05 sirve, T04/T06/T07 consumen) ---------------------------------

class ContadoresMotor(TypedDict):
    casos_piratas: int
    casos_descartados: int
    pedidos_pendientes: int
    pedidos_aprobados: int
    pedidos_rechazados: int
    ordenes_activas: int
    ordenes_fallidas: int
    reclamos_pendientes: int


class EstadoMotor(TypedDict):         # GET /api/estado
    partido_id: str
    minuto_actual: float
    fin_min: float
    finalizado: bool
    jueces_de_turno: List[str]
    proximo_cambio_turno_min: Optional[float]
    simulador_ok: bool
    turno_ratificado: bool            # v1.1: False desde un cambio de turno hasta POST /api/turno/asumir
    contadores: ContadoresMotor


class AsumirTurnoReq(TypedDict):      # POST /api/turno/asumir (v1.1)
    juez_id: str


class AsumirTurnoResp(TypedDict):
    juez_id: str
    ratificadas: List[str]            # orden_id de las órdenes vigentes que el entrante ratificó
    decidido_min: float


class ResumenExpediente(TypedDict):   # lo que la pantalla del juez muestra por pedido
    caso_id: str
    host: str
    ip: str
    organizacion: Optional[str]
    marca: Optional[str]
    motivo_clasificacion: str
    ip_compartida: bool
    dominios_en_ip: List[str]
    tipo_recomendado: TipoBloqueo
    motivo_tipo: str
    primer_minuto: float


class PedidoConResumen(Pedido):
    resumen: ResumenExpediente


class ListaPedidos(TypedDict):        # GET /api/pedidos?estado=pendiente
    pedidos: List[PedidoConResumen]


class ErrorPedido(TypedDict):
    pedido_id: str
    error: str


class AprobarPedidosReq(TypedDict):   # POST /api/pedidos/aprobar
    pedido_ids: List[str]
    juez_id: str


class AprobarPedidosResp(TypedDict):
    aprobados: List[str]
    errores: List[ErrorPedido]
    decidido_min: float


class RechazarPedidosReq(TypedDict):  # POST /api/pedidos/rechazar
    pedido_ids: List[str]
    juez_id: str
    motivo: str


class RechazarPedidosResp(TypedDict):
    rechazados: List[str]
    errores: List[ErrorPedido]
    decidido_min: float


class LevantarReclamoReq(TypedDict):  # POST /api/reclamos/levantar
    reclamo_id: str
    juez_id: str
    motivo: str
    reemplazar: bool                  # True = reemplazar por bloqueo por dominio del host pirata


class LevantarReclamoResp(TypedDict):
    reclamo_id: str
    estado: EstadoReclamo
    ordenes_levantadas: List[Dict[str, str]]
    errores: List[Dict[str, str]]     # [{proveedor_id, orden_id, error}]
    pedido_reemplazo_id: Optional[str]


# =====================================================================================
# Ejemplos (mocks). Historia común: caso C-001 = s1.pelotaya.test en 203.0.113.10,
# detectado en el minuto 2.0, aprobado por la jueza de turno en el 2.6, orden a aurora
# aplicada en el 3.2. Los ejemplos de reclamo son un escenario hipotético aparte (C-003).
# =====================================================================================

_JUEZA = "jueza-laura-ficticia"       # de turno del minuto -60 al 50 (exclusive)
_JUZGADO = "jg-centro-3"
_CORRIDA = "c0a1"

EJEMPLO_DETECCION: Deteccion = {
    "id": "D-0001",
    "minuto": 2.0,
    "pagina": "https://pelotaya.test/en-vivo",
    "stream_url": "https://s1.pelotaya.test/hls/en-vivo/index.m3u8",
    "host_stream": "s1.pelotaya.test",
    "ip_servidor": "203.0.113.10",
    "asn": 64600,
    "marca_de_agua_extraida": "LP26-PRA-OFI-S048211",
    "captura": {
        "capturada_min": 2.0,
        "formato": "mpegts",
        "duracion_seg": 6,
        "contenido_b64": "R78wa6jDSwxuvnrbaeujx9QA6W2SWznDA23chX6X64YQcfhYYZSMMZwcKXGjb2FxD+oQxdoJxuAnpRn0QxEQ0Q==",
    },
    "promocion": [{"red": "x", "url": "https://x.example/futbolya_ok/status/1001", "minuto": 1.0}],
}

EJEMPLO_SIM_DETECCIONES: RespuestaDetecciones = {"minuto_actual": 2.013, "detecciones": [EJEMPLO_DETECCION]}

EJEMPLO_SIM_ESTADO: EstadoSim = {
    "partido": "practica-01", "minuto_actual": 2.6, "fin_min": 105.0, "finalizado": False,
    "acelerar": 6.0, "jueces_de_turno": [_JUEZA],
}

EJEMPLO_SIM_PARTIDO: Partido = {
    "id": "practica-01",
    "nombre": "Partido de práctica — Club Ficticio del Norte vs. Deportivo Ejemplo",
    "titular_derechos": "Liga Profesional Ficticia",
    "inicio_iso": "2026-11-11T18:00:00-03:00",
    "fin_min": 105,
    "marcas_de_agua_validas": [
        {"prefijo": "LP26-PRA-OFI", "origen": "Señal oficial del titular (plataforma propia)"},
        {"prefijo": "LP26-PRA-LIC-NORTE", "origen": "Licenciatario autorizado: Canal Norte TV (ficticio)"},
    ],
    "licenciatarios": [{
        "nombre": "Canal Norte TV (ficticio)",
        "prefijo_marca": "LP26-PRA-LIC-NORTE",
        "dominios_autorizados": ["canalnorte.test", "envivo.canalnorte.test"],
    }],
}

EJEMPLO_SIM_DNS_IP: DnsPorIp = {
    "ip": "203.0.113.10", "asn": 64600, "organizacion": "Bruma Hosting Dedicado (ficticio)",
    "dominios": ["s1.pelotaya.test", "s1-respaldo.pelotaya.test"],
}

EJEMPLO_SIM_DNS_DOMINIO: DnsPorDominio = {
    "dominio": "s1.pelotaya.test",
    "ips": [{"ip": "203.0.113.10", "asn": 64600, "organizacion": "Bruma Hosting Dedicado (ficticio)"}],
}

EJEMPLO_SIM_PROVEEDORES: List[ProveedorSim] = [
    {"id": "aurora", "nombre": "Conectividad Aurora (ficticio)", "tamano": "grande", "clientes": 3800000,
     "capacidades": ["ip", "dominio"], "ordenes": "/proveedores/aurora/ordenes"},
    {"id": "andina", "nombre": "Red Andina Telecom (ficticio)", "tamano": "mediano", "clientes": 1200000,
     "capacidades": ["ip", "dominio"], "ordenes": "/proveedores/andina/ordenes"},
    {"id": "valle", "nombre": "FibraValle (ficticio)", "tamano": "chico", "clientes": 140000,
     "capacidades": ["dominio"], "ordenes": "/proveedores/valle/ordenes"},
    {"id": "cumbre", "nombre": "Cooperativa Cumbre Conecta (ficticio)", "tamano": "chico", "clientes": 60000,
     "capacidades": ["ip", "dominio"], "ordenes": "/proveedores/cumbre/ordenes"},
]

EJEMPLO_SIM_JUZGADOS: JuzgadosSim = {
    "juzgados": [
        {"id": "jg-centro-3", "nombre": "Juzgado de Garantías N.º 3 (ficticio) — Distrito Judicial Centro",
         "jurisdiccion": "Provincia Ficticia del Norte",
         "jueces": [{"id": "jueza-laura-ficticia", "nombre": "Dra. Laura Ficticia"}]},
        {"id": "jg-norte-1", "nombre": "Juzgado de Garantías N.º 1 (ficticio) — Distrito Judicial Norte",
         "jurisdiccion": "Provincia Ficticia del Norte",
         "jueces": [{"id": "juez-martin-ejemplo", "nombre": "Dr. Martín Ejemplo"}]},
    ],
    "turnos": [
        {"juez_id": "jueza-laura-ficticia", "desde_min": -60, "hasta_min": 50},
        {"juez_id": "juez-martin-ejemplo", "desde_min": 50, "hasta_min": 240},
    ],
    "de_turno_ahora": [_JUEZA],
}

EJEMPLO_CASO: Caso = {
    "caso_id": "C-001",
    "host": "s1.pelotaya.test",
    "ip": "203.0.113.10",
    "asn": 64600,
    "organizacion": "Bruma Hosting Dedicado (ficticio)",
    "sitio": "pelotaya.test",
    "pagina": "https://pelotaya.test/en-vivo",
    "deteccion_ids": ["D-0001"],
    "primer_minuto": 2.0,
    "marca": "LP26-PRA-OFI-S048211",
    "marca_origen": "Señal oficial del titular (plataforma propia)",
    "clasificacion": "pirata",
    "motivo_clasificacion": "Marca de agua de la señal oficial del partido (LP26-PRA-OFI) en un dominio no autorizado",
    "dominios_en_ip": ["s1.pelotaya.test", "s1-respaldo.pelotaya.test"],
    "ip_compartida": False,
    "tipo_recomendado": "ip",
    "motivo_tipo": "La IP solo aloja dominios del mismo sitio pirata (pelotaya.test)",
}

EJEMPLO_EXPEDIENTE: Expediente = {
    "expediente_id": "EXP-2026-000001",
    "partido_id": "practica-01",
    "caso": EJEMPLO_CASO,
    "capturas": [{
        "deteccion_id": "D-0001",
        "capturada_min": 2.0,
        "formato": "mpegts",
        "duracion_seg": 6,
        "bytes": 64,
        "sha256": "77b14ea8874ef8bbbf99cc292fd820a9e8df09fa4d4c00ebaeb9003e6b9bfbe1",
    }],
    "promocion": [{"red": "x", "url": "https://x.example/futbolya_ok/status/1001", "minuto": 1.0}],
    "vence_propuesto_min": 105,
    "creado_min": 2.1,
    "creado_ts": "2026-11-11T18:02:06-03:00",
    "hash": "5332df39e30d98c8cb4a6403e382dee9eced62ec89d50e58639eedf49f63cb31",
}

_OBJETIVOS_C001: List[ObjetivoPedido] = [
    {"proveedor_id": "aurora", "tipo": "ip", "objetivo": "203.0.113.10"},
    {"proveedor_id": "andina", "tipo": "ip", "objetivo": "203.0.113.10"},
    {"proveedor_id": "valle", "tipo": "dominio", "objetivo": "s1.pelotaya.test"},   # valle: solo dominio
    {"proveedor_id": "cumbre", "tipo": "ip", "objetivo": "203.0.113.10"},
]

EJEMPLO_PEDIDO_PENDIENTE: Pedido = {
    "pedido_id": "P-001",
    "expediente_id": "EXP-2026-000001",
    "origen": "deteccion",
    "objetivos": _OBJETIVOS_C001,
    "vence_min": 105,
    "creado_min": 2.1,
    "estado": "pendiente",
    "juez_id": None,
    "juzgado_id": None,
    "decidido_min": None,
    "motivo_rechazo": None,
}

EJEMPLO_PEDIDO: Pedido = dict(  # type: ignore[assignment]
    EJEMPLO_PEDIDO_PENDIENTE, estado="aprobado", juez_id=_JUEZA, juzgado_id=_JUZGADO, decidido_min=2.6,
)

EJEMPLO_ORDEN_PAYLOAD: OrdenPayload = {
    "orden_id": f"ord-{_CORRIDA}-P-001-aurora-1",
    "expediente_id": "EXP-2026-000001",
    "tipo": "ip",
    "objetivo": "203.0.113.10",
    "vence_min": 105,
    "juzgado_id": _JUZGADO,
    "juez_id": _JUEZA,
    "firma": "ab" * 32,   # de mentira: la real es HMAC(clave_firma_demo, mensaje_firma_orden(payload))
}
# mensaje_firma_orden(EJEMPLO_ORDEN_PAYLOAD) == "ord-c0a1-P-001-aurora-1|ip|203.0.113.10|105|jueza-laura-ficticia"

EJEMPLO_SIM_RESPUESTA_ORDEN: RespuestaOrden = {
    "orden_id": "ord-c0a1-P-001-aurora-1",
    "estado": "recibida",
    "consultar": "/proveedores/aurora/ordenes/ord-c0a1-P-001-aurora-1",
}

EJEMPLO_SIM_VISTA_ORDEN: VistaOrdenSim = {
    "orden_id": "ord-c0a1-P-001-aurora-1",
    "expediente_id": "EXP-2026-000001",
    "tipo": "ip",
    "objetivo": "203.0.113.10",
    "vence_min": 105,
    "juzgado_id": _JUZGADO,
    "juez_id": _JUEZA,
    "estado": "aplicada",
    "recibida_min": 2.7,
    "aplicada_min": 3.2,
}

EJEMPLO_ORDEN: Orden = {
    "orden_id": "ord-c0a1-P-001-aurora-1",
    "pedido_id": "P-001",
    "expediente_id": "EXP-2026-000001",
    "proveedor_id": "aurora",
    "tipo": "ip",
    "objetivo": "203.0.113.10",
    "vence_min": 105,
    "juzgado_id": _JUZGADO,
    "juez_id": _JUEZA,
    "estado": "aplicada",
    "intentos": 1,
    "reemplaza_a": None,
    "enviada_min": 2.7,
    "recibida_min": 2.7,
    "aplicada_min": 3.2,
    "finalizada_min": None,
    "motivo": None,
    "consultar": "/proveedores/aurora/ordenes/ord-c0a1-P-001-aurora-1",
}

EJEMPLO_ORDEN_FALLIDA: Orden = dict(  # type: ignore[assignment]
    EJEMPLO_ORDEN,
    orden_id="ord-c0a1-P-001-cumbre-1", proveedor_id="cumbre", estado="fallida",
    aplicada_min=None, motivo="Error interno del proveedor. Reenviar la orden con un nuevo orden_id.",
    consultar="/proveedores/cumbre/ordenes/ord-c0a1-P-001-cumbre-1",
)

EJEMPLO_ORDEN_REINTENTO: Orden = dict(  # type: ignore[assignment]
    EJEMPLO_ORDEN,
    orden_id="ord-c0a1-P-001-cumbre-2", proveedor_id="cumbre", estado="recibida", intentos=2,
    reemplaza_a="ord-c0a1-P-001-cumbre-1", enviada_min=6.0, recibida_min=6.0, aplicada_min=None,
    consultar="/proveedores/cumbre/ordenes/ord-c0a1-P-001-cumbre-2",
)

EJEMPLO_LEVANTAR_REQ: LevantarReq = {
    # Cuerpo del POST al SIMULADOR /proveedores/andina/ordenes/ord-c0a1-P-003-andina-1/levantar
    "juez_id": _JUEZA,
    "firma": "cd" * 32,   # de mentira: HMAC(clave, "LEVANTAR|ord-c0a1-P-003-andina-1|jueza-laura-ficticia")
    "motivo": "Reclamo R-001 verificado: la IP 192.0.2.50 es compartida con sitios legítimos",
}

# --- Auditoría interna: cadena de 4 eventos (hashes reales) ---------------------------

EJEMPLO_AUDITORIA: List[EventoAuditoria] = [
    {"seq": 1, "min": 2.05, "ts": "2026-11-11T18:02:03-03:00", "actor": "analisis", "accion": "caso_creado",
     "datos": {"caso_id": "C-001", "clasificacion": "pirata", "host": "s1.pelotaya.test", "ip": "203.0.113.10",
               "deteccion_ids": ["D-0001"]},
     "hash_prev": HASH_INICIAL, "hash": "93bdb468fa9a9e14a5f2a4d9508d8223663fbe538b5831c9d0a1ff50c59253ce"},
    {"seq": 2, "min": 2.1, "ts": "2026-11-11T18:02:06-03:00", "actor": "evidencia", "accion": "expediente_creado",
     "datos": {"expediente_id": "EXP-2026-000001", "caso_id": "C-001", "expediente_hash": "5332df39e30d98c8cb4a6403e382dee9eced62ec89d50e58639eedf49f63cb31"},
     "hash_prev": "93bdb468fa9a9e14a5f2a4d9508d8223663fbe538b5831c9d0a1ff50c59253ce", "hash": "f16dd4b5c1dc188c62bdffa7f0a999b6c358f1aaa521f7fbe484bb55b24ed281"},
    {"seq": 3, "min": 2.6, "ts": "2026-11-11T18:02:36-03:00", "actor": "juez:jueza-laura-ficticia",
     "accion": "pedido_aprobado",
     "datos": {"pedido_id": "P-001", "expediente_id": "EXP-2026-000001", "juzgado_id": "jg-centro-3"},
     "hash_prev": "f16dd4b5c1dc188c62bdffa7f0a999b6c358f1aaa521f7fbe484bb55b24ed281", "hash": "e9810d6649f17471c2f004708d82e43cebc2ec5a19b4ffa4bbefa354e109618c"},
    {"seq": 4, "min": 3.2, "ts": "2026-11-11T18:03:12-03:00", "actor": "despacho", "accion": "orden_aplicada",
     "datos": {"orden_id": "ord-c0a1-P-001-aurora-1", "proveedor_id": "aurora", "tipo": "ip",
               "objetivo": "203.0.113.10"},
     "hash_prev": "e9810d6649f17471c2f004708d82e43cebc2ec5a19b4ffa4bbefa354e109618c", "hash": "316ab2d9a407e4a4253557f41c91271d9a031966ad7d0db6bbdbd3f54ce48a65"},
]

EJEMPLO_EVENTO_AUDITORIA: EventoAuditoria = EJEMPLO_AUDITORIA[2]

# --- Registro del simulador (salida/registro.jsonl) ----------------------------------

EJEMPLO_REGISTRO: List[EventoRegistro] = [
    {"min": 2.7, "evento": "orden_recibida", "proveedor": "aurora", "juez_de_turno": True,
     "orden_id": "ord-c0a1-P-001-aurora-1", "expediente_id": "EXP-2026-000001", "tipo": "ip",
     "objetivo": "203.0.113.10", "vence_min": 105, "juzgado_id": "jg-centro-3", "juez_id": _JUEZA},
    {"min": 3.2, "evento": "orden_aplicada", "proveedor": "aurora", "orden_id": "ord-c0a1-P-001-aurora-1",
     "tipo": "ip", "objetivo": "203.0.113.10"},
    {"min": 105.0, "evento": "orden_vencida", "proveedor": "aurora", "orden_id": "ord-c0a1-P-001-aurora-1"},
]

EJEMPLO_EVENTO_REGISTRO: EventoRegistro = EJEMPLO_REGISTRO[1]

# --- Reclamos (escenario HIPOTÉTICO aparte: C-003 / P-003 se bloqueó por IP una IP compartida) ---

EJEMPLO_RECLAMO: ReclamoSim = {
    "id": "R-001",
    "minuto": 16.0,
    "dominio": "panaderia-la-espiga.test",
    "proveedor": "andina",
    "mensaje": "Panadería La Espiga: nuestros clientes no pueden entrar a la tienda online desde hace unos minutos.",
}

EJEMPLO_SIM_RECLAMOS: RespuestaReclamos = {"minuto_actual": 16.02, "reclamos": [EJEMPLO_RECLAMO]}

EJEMPLO_RECLAMO_GESTION: Reclamo = {
    "reclamo_id": "R-001",
    "minuto": 16.0,
    "dominio": "panaderia-la-espiga.test",
    "proveedor_id": "andina",
    "mensaje": EJEMPLO_RECLAMO["mensaje"],
    "estado": "pendiente",
    "verificacion": ("panaderia-la-espiga.test no es un sitio pirata y comparte la IP 192.0.2.50 con "
                     "tv.verpartido-hd.test, bloqueada por IP en andina por la orden ord-c0a1-P-003-andina-1"),
    "orden_ids": ["ord-c0a1-P-003-andina-1"],
    "caso_id": "C-003",
    "juez_id": None,
    "decidido_min": None,
    "ordenes_levantadas": [],
    "pedido_reemplazo_id": None,
}

# --- Registro público (T07) -----------------------------------------------------------

EJEMPLO_ENTRADA_PUBLICA: EntradaPublica = {
    "entrada_id": "P-001/ip/203.0.113.10",
    "pedido_id": "P-001",
    "expediente_id": "EXP-2026-000001",
    "partido_id": "practica-01",
    "tipo": "ip",
    "objetivo": "203.0.113.10",
    "motivo": "Retransmisión no autorizada del partido (marca de agua oficial en un sitio no autorizado)",
    "juez_id": _JUEZA,
    "juez_nombre": "Dra. Laura Ficticia",
    "juzgado_id": _JUZGADO,
    "juzgado_nombre": "Juzgado de Garantías N.º 3 (ficticio) — Distrito Judicial Centro",
    "ordenado_min": 2.6,
    "vence_min": 105,
    "estado": "vigente",
    "finalizado_min": None,
    "motivo_fin": None,
    "proveedores": [
        {"proveedor_id": "aurora", "estado": "aplicada", "aplicada_min": 3.2, "finalizada_min": None},
        {"proveedor_id": "andina", "estado": "recibida", "aplicada_min": None, "finalizada_min": None},
        {"proveedor_id": "cumbre", "estado": "recibida", "aplicada_min": None, "finalizada_min": None},
    ],
}

# --- API del motor -------------------------------------------------------------------

EJEMPLO_API_ESTADO: EstadoMotor = {
    "partido_id": "practica-01",
    "minuto_actual": 3.3,
    "fin_min": 105.0,
    "finalizado": False,
    "jueces_de_turno": [_JUEZA],
    "proximo_cambio_turno_min": 50.0,
    "simulador_ok": True,
    "turno_ratificado": True,
    "contadores": {
        "casos_piratas": 1, "casos_descartados": 0, "pedidos_pendientes": 0, "pedidos_aprobados": 1,
        "pedidos_rechazados": 0, "ordenes_activas": 4, "ordenes_fallidas": 0, "reclamos_pendientes": 0,
    },
}

_RESUMEN_C001: ResumenExpediente = {
    "caso_id": "C-001",
    "host": EJEMPLO_CASO["host"],
    "ip": EJEMPLO_CASO["ip"],
    "organizacion": EJEMPLO_CASO["organizacion"],
    "marca": EJEMPLO_CASO["marca"],
    "motivo_clasificacion": EJEMPLO_CASO["motivo_clasificacion"],
    "ip_compartida": EJEMPLO_CASO["ip_compartida"],
    "dominios_en_ip": EJEMPLO_CASO["dominios_en_ip"],
    "tipo_recomendado": EJEMPLO_CASO["tipo_recomendado"],
    "motivo_tipo": EJEMPLO_CASO["motivo_tipo"],
    "primer_minuto": EJEMPLO_CASO["primer_minuto"],
}

EJEMPLO_API_PEDIDOS: ListaPedidos = {
    "pedidos": [dict(EJEMPLO_PEDIDO_PENDIENTE, resumen=_RESUMEN_C001)],  # type: ignore[list-item]
}

EJEMPLO_API_APROBAR_REQ: AprobarPedidosReq = {"pedido_ids": ["P-001"], "juez_id": _JUEZA}

EJEMPLO_API_APROBAR_RESP: AprobarPedidosResp = {"aprobados": ["P-001"], "errores": [], "decidido_min": 2.6}

EJEMPLO_API_RECHAZAR_REQ: RechazarPedidosReq = {
    "pedido_ids": ["P-002"], "juez_id": _JUEZA,
    "motivo": "La evidencia no alcanza para identificar el servidor que entrega el video",
}

EJEMPLO_API_RECHAZAR_RESP: RechazarPedidosResp = {"rechazados": ["P-002"], "errores": [], "decidido_min": 8.4}

EJEMPLO_API_ORDENES: Dict[str, List[Orden]] = {"ordenes": [EJEMPLO_ORDEN, EJEMPLO_ORDEN_FALLIDA, EJEMPLO_ORDEN_REINTENTO]}

EJEMPLO_API_AUDITORIA: Dict[str, List[EventoAuditoria]] = {"eventos": EJEMPLO_AUDITORIA}

EJEMPLO_API_RECLAMOS: Dict[str, List[Reclamo]] = {"reclamos": [EJEMPLO_RECLAMO_GESTION]}

EJEMPLO_API_LEVANTAR_REQ: LevantarReclamoReq = {
    "reclamo_id": "R-001",
    "juez_id": _JUEZA,
    "motivo": "La IP 192.0.2.50 es compartida con sitios legítimos; se reemplaza por bloqueo por dominio",
    "reemplazar": True,
}

EJEMPLO_API_LEVANTAR_RESP: LevantarReclamoResp = {
    "reclamo_id": "R-001",
    "estado": "levantado",
    "ordenes_levantadas": [
        {"proveedor_id": "aurora", "orden_id": "ord-c0a1-P-003-aurora-1"},
        {"proveedor_id": "andina", "orden_id": "ord-c0a1-P-003-andina-1"},
        {"proveedor_id": "cumbre", "orden_id": "ord-c0a1-P-003-cumbre-1"},
    ],
    "errores": [],
    "pedido_reemplazo_id": "P-004",
}

EJEMPLO_API_PUBLICO: Dict[str, List[EntradaPublica]] = {"entradas": [EJEMPLO_ENTRADA_PUBLICA]}

EJEMPLO_API_ASUMIR_TURNO_REQ: AsumirTurnoReq = {"juez_id": "juez-martin-ejemplo"}

EJEMPLO_API_ASUMIR_TURNO_RESP: AsumirTurnoResp = {
    "juez_id": "juez-martin-ejemplo",
    "ratificadas": ["ord-c0a1-P-001-aurora-1", "ord-c0a1-P-001-andina-1"],
    "decidido_min": 50.4,
}


# =====================================================================================
# Autoverificación: python -m plataforma.contratos
# =====================================================================================

def _verificar_ejemplos() -> None:
    errores: List[str] = []

    def chequear(cond: bool, texto: str) -> None:
        if not cond:
            errores.append(texto)

    cap = EJEMPLO_EXPEDIENTE["capturas"][0]
    binario = base64.b64decode(EJEMPLO_DETECCION["captura"]["contenido_b64"])
    chequear(cap["sha256"] == sha256_captura(EJEMPLO_DETECCION["captura"]["contenido_b64"]), "sha256 de captura")
    chequear(cap["bytes"] == len(binario), "bytes de captura")
    chequear(EJEMPLO_EXPEDIENTE["hash"] == hash_expediente(EJEMPLO_EXPEDIENTE), "hash del expediente")
    chequear(EJEMPLO_AUDITORIA[1]["datos"]["expediente_hash"] == EJEMPLO_EXPEDIENTE["hash"], "expediente_hash en auditoría")
    prev = HASH_INICIAL
    for ev in EJEMPLO_AUDITORIA:
        chequear(ev["hash_prev"] == prev, f"hash_prev del seq {ev['seq']}")
        chequear(ev["hash"] == hash_evento_auditoria(ev), f"hash del seq {ev['seq']}")
        prev = ev["hash"]
    chequear(set(EJEMPLO_ORDEN_PAYLOAD) == set(CAMPOS_ORDEN), "campos del payload")
    chequear(isinstance(EJEMPLO_ORDEN_PAYLOAD["vence_min"], int), "vence_min entero")
    chequear(mensaje_firma_orden(EJEMPLO_ORDEN_PAYLOAD)
             == "ord-c0a1-P-001-aurora-1|ip|203.0.113.10|105|jueza-laura-ficticia", "mensaje de firma")
    for p in (EJEMPLO_ORDEN, EJEMPLO_SIM_VISTA_ORDEN, EJEMPLO_SIM_RESPUESTA_ORDEN, EJEMPLO_EVENTO_REGISTRO):
        chequear(p["orden_id"] == EJEMPLO_ORDEN_PAYLOAD["orden_id"], "orden_id coherente")
    chequear(EJEMPLO_CASO["host"] == EJEMPLO_DETECCION["host_stream"], "host del caso")
    chequear(EJEMPLO_CASO["ip"] == EJEMPLO_DETECCION["ip_servidor"], "ip del caso")
    chequear(EJEMPLO_CASO["sitio"] == sitio_de(EJEMPLO_CASO["host"]), "sitio del caso")
    chequear(EJEMPLO_PEDIDO["vence_min"] == vence_min_para(EJEMPLO_SIM_PARTIDO["fin_min"]), "vence_min del pedido")
    if errores:
        raise SystemExit("Ejemplos incoherentes: " + "; ".join(errores))
    print(f"contratos {VERSION_CONTRATOS}: ejemplos coherentes")
    print(f"  sha256 captura D-0001 : {cap['sha256']}")
    print(f"  hash EXP-2026-000001  : {EJEMPLO_EXPEDIENTE['hash']}")
    for ev in EJEMPLO_AUDITORIA:
        print(f"  auditoría seq {ev['seq']}       : {ev['hash']}")


if __name__ == "__main__":
    _verificar_ejemplos()
