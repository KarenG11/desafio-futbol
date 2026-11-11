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

## 2026-11-11 — alejo (diseño aprobado)
12. **Traspaso de turno con ratificación** (complementa la 9). Cuando cambia el juez de turno, el entrante ratifica con un toque las órdenes vigentes (`POST /api/turno/asumir`, contratos v1.1). Hasta entonces, despacho no reenvía órdenes aprobadas por el saliente. Es más prolijo legalmente: nadie firma algo que no decidió.
13. **Diseño aprobado:** `coordinacion/diseno.md`. Las reglas del cerebro (agrupar, marca de agua, IP compartida por `sitio`) dan 9 de 9 contra `evaluacion/verdad_practica.json`: 7 piratas con el tipo correcto, más el licenciatario y la señal ajena descartados.
14. **Lección de coordinación:** dos agentes con el mismo `--yo` no se frenan entre sí (los dos "son" dueños). Si una persona abre más de una sesión de agente, cada una usa un nombre distinto (`alejo`, `alejo-2`, …) en el buzón.

## 2026-11-11 — alejo (escalable y deploy en Vercel)
15. **Deploy público en Vercel.** Reemplaza en parte la decisión 2 y el punto 8 de `diseno.md`. El sistema queda en **dos procesos que comparten una base Postgres**:
    - **Web + API** (FastAPI en Vercel): pantalla del juez, registro público y la API de `contratos.md` §5. No guarda nada en memoria: todo sale de la base. **No tiene las claves de firma.**
    - **Motor** (proceso Python que corre siempre): loop, cerebro, evidencia, despacho y reclamos. Es el único que habla con el simulador y el único que firma. Corre donde llegue al simulador: en el evento, la notebook.
16. **Por qué el motor no va en Vercel.** Una función de Vercel dura como máximo 5 minutos en el plan Hobby y no guarda estado entre pedidos. El partido dura de 17 a 105 minutos y el loop consulta cada ~1 s. Además, el simulador del final está en la dirección que asigne la organización, que probablemente es de la red del evento.
17. **Base: Postgres administrado** (Neon, desde el Marketplace de Vercel: las variables se cargan solas en Vercel y en local con `vercel env pull`). Hay una tabla por contrato (`casos`, `expedientes`, `pedidos`, `ordenes`, `reclamos`, `auditoria`), con el contrato completo en una columna JSONB y unas pocas columnas para filtrar (`partido_id`, `estado`, ids). Los contratos no cambian de forma.
18. **Escala.** Todas las tablas llevan `partido_id`. Varios partidos y juzgados pueden correr en paralelo, con un motor por partido y una sola web federal. El juez aprueba desde cualquier lugar con internet, no solo desde el wifi del evento: eso es lo "federal" del pitch.
19. **Auditoría con un solo escritor.** Solo el motor escribe en `auditoria`, así la cadena de hashes no tiene carreras. La web registra la decisión del juez en `pedidos` (con `decidido_min`), y el motor la audita al tomarla.
20. **Plan B para el partido final.** La capa de datos funciona con Postgres (`DATABASE_URL=postgres://...`) o con SQLite (`sqlite:///salida/plataforma.db`). Si se cae internet, la web y el motor corren juntos en la notebook con SQLite, como en el diseño original: `python -m plataforma.main --sim ... --local`. Primero tiene que andar la demo.
21. **Acceso del juez:** como la web es pública, aprobar y rechazar piden un PIN de demo (`JUEZ_PIN`, variable de entorno, nunca en el repo). No es login: alcanza para que un tercero no apruebe órdenes. El registro público no pide nada.

## 2026-11-11 — alejo (todo online en Vercel)
22. **El motor también corre en Vercel, en un Vercel Sandbox** (una máquina virtual que Vercel prende a pedido). Reemplaza lo de "motor en la notebook" de las decisiones 15 y 16. En una función de Vercel no entra, porque dura como máximo 5 minutos; en un Sandbox sí: la sesión dura hasta 45 minutos en Hobby y 24 horas en Pro. Un partido con `--acelerar 6` dura 17,5 minutos, más 5 de gracia, y entra en Hobby. Con `--acelerar 1` (110 minutos) hace falta Pro, o reanudar el Sandbox: el estado está en la base y el motor retoma.
23. **Partido de demo online para el jurado.** La web tiene un botón "Correr partido de práctica". Prende un Sandbox que clona el repo, levanta el simulador de la organización con el escenario de práctica y nuestro motor apuntando a él, y al terminar corre `evaluacion/verificar.py`. Cualquiera con el link ve el circuito completo en vivo: detección, juez, proveedores, confirmación, vencimiento y la salida del verificador.
24. **Partido final:** el motor corre en un Sandbox apuntando a la dirección del simulador que asigne la organización, **si esa dirección se puede alcanzar desde internet**. Si es de la red local del evento, el mismo motor corre en la notebook. Es el mismo código y la misma base, y la web sigue en Vercel. **Hay que preguntarle a la organización el día 1.**
