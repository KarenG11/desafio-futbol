---
de: alejo
para: selene,todos
fecha: 2026-11-11 14:21
asunto: T01 cerebro listo + contratos v1.4 (aditivo)
requiere_respuesta: no
---
T01 terminada: plataforma/analisis/ (Cerebro).

Selene, para T05 (motor):
    from plataforma.analisis import Cerebro
    cerebro = Cerebro(partido, consultar_dns)  # consultar_dns(ip) = GET /dns-pasivo?ip=, None si 404
    caso, es_nuevo = cerebro.procesar(deteccion)
    si es_nuevo y caso['clasificacion'] == 'pirata' -> expediente (T03) + pedido; si es_nuevo y no es pirata -> auditar caso_descartado.
El detalle y el ejemplo del loop están en contratos.md §2 (API de T01).

Pruebas: python -m plataforma.analisis.test_cerebro -> 7 de 7 OK (partido de práctica completo: 9 casos, 7 piratas con el tipo correcto, licenciatario y señal ajena descartados).

Contratos v1.4, solo aditivo: contratos.py suma turno_ratificado en EstadoMotor y AsumirTurnoReq/Resp (ya estaban en el .md desde v1.1).

Sigo con T04 (pantalla del juez) contra un mock de la API hasta que esté T11.
