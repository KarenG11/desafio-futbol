# Decisiones

Se agregan abajo, con fecha y quién decidió. No se borran: si una cambia, se agrega otra que la reemplaza.

## 2026-11-11 — alejo
1. **Repo del equipo:** este fork (`alejogomezmdz14-hash/desafio-futbol`). Lo nuestro vive en `plataforma/` y `entrega/`; lo de la organización no se toca.
2. **Stack: todo Python.** Un solo programa (FastAPI) con el robot y la web del juez. Se corre con un comando. Sin Next.js ni Streamlit.
3. **Juez: aprueba en lote, con un toque.** Un integrante hace de juez desde el celular durante el partido final. La plataforma junta los pedidos pendientes y él aprueba varios a la vez. Hay un modo "juez automático" solo para probar partidos acelerados; en el final va apagado.
4. **Por qué juez sí o sí:** el art. 57 inc. a) de la Ley 27.078 prohíbe bloquear salvo orden judicial. Que el juez confirme cada objetivo nuevo sigue la doctrina de la Corte ("Rodríguez c/ Google": examen previo de la ilicitud de cada contenido concreto). No usamos una "orden marco" que deje a otro sumar objetivos solo.
5. **Coordinación:** buzón en archivos dentro del repo (`coordinacion/`), con un archivo por tarea y uno por mensaje para no chocar en git.
6. **Hallazgos del simulador que condicionan el diseño:**
   - Las detecciones se repiten (43 avisos para 7 streams): hay que agrupar por host e IP.
   - La firma se valida contra el turno **cuando la orden llega al proveedor**. Cerca del cambio de turno hay que firmar con el juez entrante.
   - Una orden `fallida` no se reintenta sola: se reenvía con un `orden_id` nuevo.
   - Una marca de agua de licenciatario **fuera de sus dominios autorizados** es piratería (retransmite su señal).
   - Un proveedor solo acepta bloqueo por dominio: si le mandás IP, rechaza.

## 2026-11-11 — alejo (contratos v1, T00)
7. **Dos registros distintos.** `salida/registro.jsonl` lo escribe el simulador y es lo que mira el verificador; no lo tocamos. Nuestra auditoría interna (cadena de hashes, T03) es otro archivo. No se mezclan formatos.
8. **Vencimiento en el MVP:** `vence_min = int(fin_min)` para IP **y para dominio**. El verificador solo penaliza IP activas después del partido; el bloqueo DNS permanente queda para la propuesta normativa.
9. **Firma por envío:** cada envío a un proveedor, incluido cada reintento, se firma con el juez de turno en el minuto del envío (no necesariamente el que aprobó el pedido). Queda en auditoría.
10. **Reclamos sin `orden_id`:** el feed `/reclamos` no lo trae; se correlaciona por proveedor + dominio + minuto contra nuestras órdenes. Al levantar, se levantan todas las órdenes con ese objetivo en todos los proveedores y, si era IP, se reemplaza por dominio del host pirata.
11. **`orden_id` con prefijo de corrida** (`ord-{corrida}-{pedido_id}-{proveedor_id}-{intento}`) para no chocar con un 409 si se reinicia la plataforma con el simulador andando.
