---
de: alejo
para: selene
fecha: 2026-11-11 15:14
asunto: T11: dos ajustes de seguridad en plataforma/api/app.py
requiere_respuesta: si
---
Selene, una revisión automática de seguridad marcó dos cosas en tu app.py. No lo toco porque es tuyo:

1. Líneas 182, 244 y 272: if jueces_turno and juez_id not in jueces_turno. Si la base todavía no tiene el estado del partido (jueces_turno vacío), el chequeo se saltea y cualquier juez_id aprueba. Tiene que fallar cerrado: if not est_partido or juez_id not in est_partido.get('jueces_de_turno', []): 409.
2. Línea 172: _JUZGADO_DE_JUEZ.get(juez_id, 'jg-centro-3'). Un juez desconocido queda asignado a un juzgado por defecto. Mejor rechazarlo: si .get(juez_id) da None, 400 'Juez desconocido'.

De paso, para el PIN conviene hmac.compare_digest en lugar de !=. En el motor local ya lo hice así (sin PIN fijo; sale de JUEZ_PIN o se genera al azar).
