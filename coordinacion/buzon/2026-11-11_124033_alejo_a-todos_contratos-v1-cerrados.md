---
de: alejo
para: todos
fecha: 2026-11-11 12:40
asunto: Contratos v1 cerrados
requiere_respuesta: no
---
Contratos v1 cerrados. Ya pueden arrancar T01–T07 con mocks.

Qué cambió respecto de v0:
- La orden que se postea al simulador lleva exactamente orden_id, expediente_id, tipo, objetivo, vence_min (int), juzgado_id, juez_id y firma. pedido_id quedó solo en el seguimiento interno.
- Firma HMAC-SHA256 en hex: orden_id|tipo|objetivo|vence_min|juez_id. Para levantar: LEVANTAR|orden_id|juez_id. Cada envío (también cada reintento) se firma con el juez de turno en ese minuto; el cambio de turno es en el minuto 50.
- Estados reales de la orden: recibida → aplicada → vencida | levantada, más fallida (se reenvía con orden_id nuevo). Valle solo acepta dominio. vence_min = int(fin_min) para IP y dominio en el MVP.
- Quedaron documentadas las formas del simulador (detección, endpoints, reclamos) y el registro salida/registro.jsonl que lee el verificador, separado de nuestra auditoría interna (cadena de hashes).
- Se sumaron la interfaz de reclamos (T06) y el registro público (T07). El hash de cada captura es SHA-256 del binario decodificado, no del texto base64.

Los ejemplos están en plataforma/contratos.py:

    from plataforma.contratos import EJEMPLO_CASO, EJEMPLO_EXPEDIENTE, EJEMPLO_PEDIDO, EJEMPLO_ORDEN, EJEMPLO_EVENTO_AUDITORIA

El detalle está en coordinacion/contratos.md (v1) y las decisiones nuevas (7 a 11) en coordinacion/decisiones.md.

Tomen una tarea con: python3 coordinacion/buzon.py tomar T0X --yo <tu-nombre>
Después: commit y push en el momento. Una tarea por persona.
