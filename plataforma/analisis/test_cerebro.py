"""Pruebas del cerebro (T01). Correr desde la raíz del repo:

    python -m plataforma.analisis.test_cerebro
"""
import copy
import json
import sys
from pathlib import Path

from plataforma.analisis import Cerebro

RAIZ = Path(__file__).resolve().parents[2]


def cargar(ruta: str) -> dict:
    return json.loads((RAIZ / ruta).read_text(encoding="utf-8"))


def dns_desde_escenario(escenario: dict):
    """Imita GET /dns-pasivo?ip= del simulador (None = 404)."""
    llamadas = []

    def consultar(ip: str):
        llamadas.append(ip)
        if ip not in escenario["dns_pasivo"]:
            return None
        asn = escenario["ip_asn"].get(ip)
        return {"ip": ip, "asn": asn, "organizacion": escenario["asn"].get(str(asn)),
                "dominios": escenario["dns_pasivo"][ip]}

    consultar.llamadas = llamadas
    return consultar


def det(id_, host, ip, marca, minuto=1.0):
    return {"id": id_, "minuto": minuto, "pagina": f"https://{host}/", "stream_url": f"https://{host}/x.m3u8",
            "host_stream": host, "ip_servidor": ip, "asn": 64600, "marca_de_agua_extraida": marca,
            "captura": {"capturada_min": minuto, "formato": "mpegts", "duracion_seg": 6, "contenido_b64": ""},
            "promocion": []}


# --- pruebas ------------------------------------------------------------------------------

def prueba_partido_de_practica():
    escenario = cargar("datos/escenario_practica.json")
    verdad = cargar("evaluacion/verdad_practica.json")
    cerebro = Cerebro(escenario["partido"], dns_desde_escenario(escenario))
    nuevos = 0
    for d in sorted(escenario["detecciones"], key=lambda x: x["minuto"]):
        _, es_nuevo = cerebro.procesar(d)
        nuevos += es_nuevo
    esperado = {(f["host"], f["ip"]): (s["clase"], f["bloqueo_recomendado"], f["detecciones"])
                for s in verdad["streams"] for f in s["fases"]}
    casos = {(c["host"], c["ip"]): c for c in cerebro.casos()}
    assert nuevos == len(casos) == len(esperado) == 9, f"casos: {len(casos)}, esperados {len(esperado)}"
    piratas = 0
    for clave, (clase, recomendado, ids) in esperado.items():
        caso = casos[clave]
        assert sorted(caso["deteccion_ids"]) == sorted(ids), f"{clave}: detecciones mal agrupadas"
        if clase == "pirata":
            piratas += 1
            assert caso["clasificacion"] == "pirata", f"{clave}: {caso['clasificacion']}"
            assert caso["tipo_recomendado"] == recomendado, f"{clave}: {caso['tipo_recomendado']} != {recomendado}"
        else:
            assert caso["clasificacion"] != "pirata", f"{clave}: falso positivo ({clase})"
    assert piratas == 7
    assert casos[("envivo.canalnorte.test", "192.0.2.10")]["clasificacion"] == "licenciatario_legal"
    assert casos[("vod.resumenes-deportivos.test", "198.51.100.90")]["clasificacion"] == "otra_senal"


def prueba_campos_del_contrato():
    escenario = cargar("datos/escenario_practica.json")
    cerebro = Cerebro(escenario["partido"], dns_desde_escenario(escenario))
    caso, _ = cerebro.procesar(escenario["detecciones"][0])
    claves = {"caso_id", "host", "ip", "asn", "organizacion", "sitio", "pagina", "deteccion_ids", "primer_minuto",
              "marca", "marca_origen", "clasificacion", "motivo_clasificacion", "dominios_en_ip", "ip_compartida",
              "tipo_recomendado", "motivo_tipo"}
    assert set(caso) == claves, f"sobran {set(caso) - claves}, faltan {claves - set(caso)}"
    assert caso["caso_id"] == "C-001" and caso["sitio"] == "pelotaya.test"
    assert caso["organizacion"] == "Bruma Hosting Dedicado (ficticio)"
    json.dumps(caso)  # serializable para la base


def prueba_licenciatario_fuera_de_su_dominio_es_pirata():
    escenario = cargar("datos/escenario_practica.json")
    cerebro = Cerebro(escenario["partido"], lambda ip: None)
    caso, _ = cerebro.procesar(det("D-1", "copia.trucha.test", "203.0.113.99", "LP26-PRA-LIC-NORTE"))
    assert caso["clasificacion"] == "pirata", caso["clasificacion"]
    assert "Canal Norte" in caso["motivo_clasificacion"]


def prueba_subdominio_del_licenciatario_es_legal():
    escenario = cargar("datos/escenario_practica.json")
    cerebro = Cerebro(escenario["partido"], lambda ip: None)
    caso, _ = cerebro.procesar(det("D-1", "hd.envivo.canalnorte.test", "192.0.2.10", "LP26-PRA-LIC-NORTE"))
    assert caso["clasificacion"] == "licenciatario_legal"


def prueba_dns_sin_datos_va_por_dominio():
    escenario = cargar("datos/escenario_practica.json")
    cerebro = Cerebro(escenario["partido"], lambda ip: None)
    caso, _ = cerebro.procesar(det("D-1", "nuevo.pirata.test", "203.0.113.200", "LP26-PRA-OFI-S1"))
    assert caso["ip_compartida"] is True and caso["tipo_recomendado"] == "dominio"
    assert caso["dominios_en_ip"] == [] and caso["organizacion"] is None


def prueba_repeticion_y_mudanza():
    escenario = cargar("datos/escenario_practica.json")
    dns = dns_desde_escenario(escenario)
    cerebro = Cerebro(escenario["partido"], dns)
    a, nuevo_a = cerebro.procesar(det("D-1", "s1.pelotaya.test", "203.0.113.10", "LP26-PRA-OFI-S1", 2))
    b, nuevo_b = cerebro.procesar(det("D-2", "s1.pelotaya.test", "203.0.113.10", "LP26-PRA-OFI-S1", 12))
    c, nuevo_c = cerebro.procesar(det("D-3", "s2.pelotaya.test", "203.0.113.11", "LP26-PRA-OFI-S1", 37))
    assert nuevo_a and not nuevo_b and nuevo_c
    assert a is b and a["deteccion_ids"] == ["D-1", "D-2"]
    assert c["caso_id"] == "C-002"
    assert dns.llamadas == ["203.0.113.10", "203.0.113.11"], "el DNS se tiene que cachear por IP"


def prueba_sin_marca_y_prefijo_mas_largo():
    partido = copy.deepcopy(cargar("datos/escenario_practica.json")["partido"])
    partido["marcas_de_agua_validas"].append({"prefijo": "LP26", "origen": "Prefijo corto de prueba"})
    cerebro = Cerebro(partido, lambda ip: None)
    sin, _ = cerebro.procesar(det("D-1", "a.test", "192.0.2.1", None))
    vacia, _ = cerebro.procesar(det("D-2", "b.test", "192.0.2.2", ""))
    lic, _ = cerebro.procesar(det("D-3", "envivo.canalnorte.test", "192.0.2.10", "LP26-PRA-LIC-NORTE"))
    pegada, _ = cerebro.procesar(det("D-4", "c.test", "192.0.2.3", "LP26-PRA-OFIX"))
    assert sin["clasificacion"] == vacia["clasificacion"] == "sin_marca"
    assert lic["clasificacion"] == "licenciatario_legal", "tiene que ganar el prefijo más largo"
    assert pegada["marca_origen"] == "Prefijo corto de prueba", "'OFIX' no es el prefijo 'OFI'"


def prueba_marca_oficial_en_dominio_del_licenciatario_no_se_bloquea():
    escenario = cargar("datos/escenario_practica.json")
    cerebro = Cerebro(escenario["partido"], lambda ip: None)
    caso, _ = cerebro.procesar(det("D-1", "canalnorte.test", "192.0.2.10", "LP26-PRA-OFI-S1"))
    assert caso["clasificacion"] == "licenciatario_legal", "nunca bloquear un dominio autorizado del licenciatario"
    assert "no es la suya" in caso["motivo_clasificacion"]


def prueba_mayusculas_y_espacios():
    escenario = cargar("datos/escenario_practica.json")
    cerebro = Cerebro(escenario["partido"], dns_desde_escenario(escenario))
    caso, _ = cerebro.procesar(det("D-1", "S1.PelotaYa.test.", "203.0.113.10", " lp26-pra-ofi-s048211 "))
    assert caso["clasificacion"] == "pirata" and caso["tipo_recomendado"] == "ip", caso


def prueba_sitio_con_sufijos_publicos():
    from plataforma.contratos import sitio_de
    assert sitio_de("s1.pelotaya.test") == "pelotaya.test"
    assert sitio_de("www.diario.com.ar") == "diario.com.ar"
    assert sitio_de("pirata.com.ar") == "pirata.com.ar"
    assert sitio_de("tienda.vercel.app") == "tienda.vercel.app"
    assert sitio_de("com.ar") == "com.ar"


def prueba_hosting_compartido_real_va_por_dominio():
    """En el mundo real: un pirata .com.ar en un hosting con otros .com.ar no es 'el mismo sitio'."""
    escenario = cargar("datos/escenario_practica.json")
    dns = {"ip": "200.1.1.1", "asn": 1, "organizacion": "Hosting Compartido SA",
           "dominios": ["vivo.futbolgratis.com.ar", "panaderia.com.ar", "municipio.gob.ar"]}
    cerebro = Cerebro(escenario["partido"], lambda ip: dns)
    caso, _ = cerebro.procesar(det("D-1", "vivo.futbolgratis.com.ar", "200.1.1.1", "LP26-PRA-OFI-S9"))
    assert caso["ip_compartida"] and caso["tipo_recomendado"] == "dominio", caso["motivo_tipo"]
    dns2 = {"ip": "200.1.1.2", "asn": 1, "organizacion": "x", "dominios": ["a.vercel.app", "b.vercel.app"]}
    cerebro2 = Cerebro(escenario["partido"], lambda ip: dns2)
    caso2, _ = cerebro2.procesar(det("D-2", "a.vercel.app", "200.1.1.2", "LP26-PRA-OFI-S9"))
    assert caso2["tipo_recomendado"] == "dominio", "clientes distintos de una plataforma no son el mismo sitio"


def prueba_dns_caido_no_frena_el_circuito():
    escenario = cargar("datos/escenario_practica.json")

    def dns_roto(ip):
        raise TimeoutError("DNS pasivo no responde")

    cerebro = Cerebro(escenario["partido"], dns_roto)
    caso, nuevo = cerebro.procesar(det("D-1", "s1.pelotaya.test", "203.0.113.10", "LP26-PRA-OFI-S1"))
    assert nuevo and caso["clasificacion"] == "pirata" and caso["tipo_recomendado"] == "dominio"
    vacio = Cerebro(escenario["partido"], lambda ip: {"ip": ip, "asn": None, "organizacion": None, "dominios": []})
    caso2, _ = vacio.procesar(det("D-2", "x.pirata.test", "203.0.113.5", "LP26-PRA-OFI-S1"))
    assert caso2["tipo_recomendado"] == "dominio", "sin dominios conocidos no hay forma de medir el colateral"


def prueba_escenario_final_simulado():
    """Un partido 'que nadie vio': otros nombres, varios licenciatarios y todas las trampas del enunciado."""
    partido = {"id": "final-x", "nombre": "Final", "titular_derechos": "Liga", "inicio_iso": "", "fin_min": 105,
               "marcas_de_agua_validas": [{"prefijo": "LF26-FIN-OFI", "origen": "oficial"},
                                          {"prefijo": "LF26-FIN-LIC-SUR", "origen": "Canal Sur"},
                                          {"prefijo": "LF26-FIN-LIC-OESTE", "origen": "Oeste TV"}],
               "licenciatarios": [
                   {"nombre": "Canal Sur", "prefijo_marca": "LF26-FIN-LIC-SUR", "dominios_autorizados": ["canalsur.test"]},
                   {"nombre": "Oeste TV", "prefijo_marca": "LF26-FIN-LIC-OESTE", "dominios_autorizados": ["oestetv.example"]}]}
    dns = {
        "198.51.100.1": ["live.rojo.test", "rojo.test"],                                   # exclusiva
        "198.51.100.2": ["cdn.verde.test", "almacen.test", "colegio.example"],              # CDN
        "198.51.100.3": ["live2.rojo.test"],                                                 # exclusiva
        "198.51.100.4": ["vivo.canalsur.test", "canalsur.test"],                             # licenciatario
        "198.51.100.5": ["espejo.gris.test", "gris.test", "radio.example"],                  # compartida
    }
    consultar = lambda ip: ({"ip": ip, "asn": 1, "organizacion": "x", "dominios": dns[ip]} if ip in dns else None)
    detecciones = [
        det("F1", "live.rojo.test", "198.51.100.1", "LF26-FIN-OFI-A1", 1),
        det("F2", "cdn.verde.test", "198.51.100.2", "LF26-FIN-OFI-A2", 2),
        det("F3", "vivo.canalsur.test", "198.51.100.4", "LF26-FIN-LIC-SUR", 3),     # legal
        det("F4", "espejo.gris.test", "198.51.100.5", "LF26-FIN-LIC-OESTE", 4),     # señal de Oeste robada
        det("F5", "vod.otro.test", "198.51.100.9", "LF25-X-OFI-1", 5),              # otro partido
        det("F6", "x.sinmarca.test", "198.51.100.8", None, 6),                      # sin marca
        det("F7", "live.rojo.test", "198.51.100.1", "LF26-FIN-OFI-A1", 11),         # repetición
        det("F8", "live2.rojo.test", "198.51.100.3", "LF26-FIN-OFI-A1", 40),        # mudanza a IP exclusiva
        det("F9", "nuevo.rojo.test", "203.0.113.77", "LF26-FIN-OFI-A1", 70),        # mudanza a IP sin DNS
    ]
    cerebro = Cerebro(partido, consultar)
    nuevos = [c for c, n in (cerebro.procesar(d) for d in detecciones) if n]
    clas = {c["host"]: (c["clasificacion"], c["tipo_recomendado"]) for c in nuevos}
    assert len(nuevos) == 8, len(nuevos)
    assert clas["live.rojo.test"] == ("pirata", "ip")
    assert clas["cdn.verde.test"] == ("pirata", "dominio")
    assert clas["vivo.canalsur.test"][0] == "licenciatario_legal"
    assert clas["espejo.gris.test"] == ("pirata", "dominio")
    assert clas["vod.otro.test"][0] == "otra_senal"
    assert clas["x.sinmarca.test"][0] == "sin_marca"
    assert clas["live2.rojo.test"] == ("pirata", "ip")
    assert clas["nuevo.rojo.test"] == ("pirata", "dominio")


def main() -> int:
    pruebas = [v for k, v in globals().items() if k.startswith("prueba_")]
    fallas = 0
    for prueba in pruebas:
        try:
            prueba()
            print(f"OK    {prueba.__name__}")
        except AssertionError as e:
            fallas += 1
            print(f"FALLA {prueba.__name__}: {e}")
    print(f"\n{len(pruebas) - fallas} de {len(pruebas)} pruebas OK")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
