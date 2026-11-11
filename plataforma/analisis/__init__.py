"""T01 — Cerebro. Uso desde el motor:

    from plataforma.analisis import Cerebro
    cerebro = Cerebro(partido, consultar_dns)   # consultar_dns(ip) -> DnsPorIp | None (404)
    caso, es_nuevo = cerebro.procesar(deteccion)
    if es_nuevo and caso["clasificacion"] == "pirata": ...   # expediente (T03) + pedido
"""
from plataforma.analisis.cerebro import Cerebro

__all__ = ["Cerebro"]
