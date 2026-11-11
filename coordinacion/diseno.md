# Diseño — Plataforma federal de órdenes de bloqueo en vivo

Aprobado por Alejo el 2026-11-11 (T00). Los contratos de datos son los de `contratos.md` (v1) y `plataforma/contratos.py`. **Si este documento y los contratos difieren en un nombre o formato, mandan los contratos.** Este documento explica el *porqué* y las reglas de decisión.

## 1. Qué es
Un solo programa Python (FastAPI) que se conecta al simulador y hace el circuito completo durante el partido:

```
SIMULADOR ──detecciones, DNS pasivo, reclamos──► MOTOR (loop)
   ▲                                              │
   │ órdenes firmadas                             ├─► CEREBRO      clasifica y arma casos
   │                                              ├─► EVIDENCIA    expediente + auditoría encadenada
   └──────────── DESPACHO ◄── pedido aprobado ────┤
                                                  └─► API ◄──► WEB DEL JUEZ (celular, aprueba en lote)
                                                             └► REGISTRO PÚBLICO (/api/publico)
```

Se corre con `python -m plataforma.main --sim http://localhost:8080`. El flag `--juez-automatico` sirve solo para probar partidos acelerados. En el partido final aprueba una persona desde el celular.

## 2. Cerebro (`plataforma/analisis/`)
Probado contra `evaluacion/verdad_practica.json`: 9 de 9 casos correctos.

1. **Agrupar.** Un caso es el par (`host_stream`, `ip_servidor`). Un aviso repetido se suma a su caso y no genera otro pedido. Si el sitio se muda (otro host o IP), es un caso nuevo.
2. **Clasificar por marca de agua** contra `GET /partido`:
   - Sin marca → `sin_marca` (descartado).
   - La marca no empieza con ningún prefijo de `marcas_de_agua_validas` → `otra_senal` (descartado).
   - La marca es de un licenciatario y el `host_stream` es uno de sus `dominios_autorizados` (o un subdominio de uno) → `licenciatario_legal` (descartado).
   - Cualquier otro caso con marca válida → `pirata`. Esto incluye la marca de un licenciatario fuera de sus dominios.
3. **Riesgo colateral** con `GET /dns-pasivo?ip=`:
   - Todos los dominios de la IP tienen la misma raíz que el host (las dos últimas etiquetas, como `pelotaya.test`) → IP exclusiva → `tipo_recomendado = "ip"`.
   - Si hay un dominio con otra raíz, o el DNS pasivo no tiene datos de la IP → `tipo_recomendado = "dominio"`, y el objetivo es el `host_stream` exacto.
4. **Promoción:** se copian las URLs de `promocion` del aviso (X, Discord, Telegram) al caso.

Los casos descartados se registran en la auditoría con su motivo. Solo los `pirata` generan un pedido al juez.

## 3. Juez (`plataforma/web/` + API del motor)
- **Un pedido por caso pirata**, que espera en la cola del juez de turno.
- **Aprobación en lote:** "Aprobar todos" o de a uno. Rechazar requiere un motivo.
- **La firma la pone el juez de turno al momento de enviar.** El turno se consulta en `GET /estado` justo antes de firmar, porque el simulador valida el turno cuando recibe la orden.
- **Traspaso de turno:** cuando cambia el juez de turno, la web le muestra al entrante "Asumir turno y ratificar N órdenes vigentes" (un toque, `POST /api/turno/asumir`). Hasta que ratifique, los reintentos de órdenes aprobadas por el juez saliente quedan en espera. Los pedidos nuevos siempre los aprueba el juez de turno. Esto es un agregado a la decisión 9: el reintento se sigue firmando con el juez de turno en el minuto del envío, pero solo después de que ratificó.
- **Juez automático (solo pruebas):** aprueba cada pedido al instante y ratifica solo en el traspaso.

## 4. Despacho (`plataforma/despacho/`)
- **Objetivos por proveedor** (de `GET /proveedores`, campo `capacidades`):
  - Caso `ip`: los proveedores que aceptan `ip` reciben la IP. Los que solo aceptan `dominio` reciben el `host_stream`.
  - Caso `dominio`: todos reciben el `host_stream`.
- **Vencimiento:** `vence_min = int(fin_min)` para todas las órdenes. En IP es obligatorio. En dominio se hace por proporcionalidad: extenderlo requiere una orden nueva.
- **Firma:** `HMAC-SHA256(clave_firma_demo, "orden_id|tipo|objetivo|vence_min|juez_id")`. Las claves salen de `datos/juzgados.json` y nunca se muestran en la web.
- **`orden_id`:** `ord-{corrida}-{pedido_id}-{proveedor_id}-{intento}` (`ORDEN_ID_FORMATO` en contratos). Es único por proveedor y no choca si se reinicia la plataforma.
- **Seguimiento:** cada orden se consulta cada ~1 s real. Si queda `fallida`, se reenvía en el acto con el intento siguiente (Cumbre falla el 35 % de las veces). Si el envío es rechazado, se registra y no se reintenta igual: es un error nuestro.
- **Levantar (reclamos):** se firma `LEVANTAR|orden_id|juez_id` con el juez de turno, previa aprobación en la web.

## 5. Evidencia y auditoría (`plataforma/evidencia/`)
- **Expediente por caso:** clasificación y motivo, marca verificada contra el prefijo, servidor (host, IP, ASN y organización), dominios en la IP, `sha256` de cada captura (sobre los bytes de `contenido_b64` decodificado), minutos de captura, promoción y hash del expediente completo.
- **Auditoría:** JSONL append-only con cadena de hashes (`contratos.md` punto 6). Registra cada aviso recibido, caso creado o descartado, pedido, aprobación o rechazo, orden enviada, aplicada, fallida o rechazada, reintento, ratificación de turno, reclamo y levantamiento.
- **Verificador de integridad:** recorre la cadena y dice en qué línea se rompió. También verifica el hash de un expediente.
- **Exportación a `entrega/`:** un expediente y la auditoría completa del partido final.

## 6. Reclamos (extra, `plataforma/reclamos/`)
`GET /reclamos` → se verifica que el dominio reclamante no esté entre los objetivos piratas y que esté detrás de una orden nuestra → pedido de levantamiento al juez → al aprobarse, se levanta esa orden y se reemplaza por bloqueo de dominio del `host_stream`. Con las reglas de la sección 2 no deberían aparecer reclamos, pero el escenario final puede tener un DNS pasivo incompleto.

## 7. Qué medimos
`evaluacion/verificar.py`: 7 de 7 fases bloqueadas, visibilidad residual mínima, 0 colateral, 0 falsos positivos, 0 rechazos, 0 firmas fuera de turno y 0 IP activas después del partido. Línea base (cliente de ejemplo): 1 de 7 y 92,4 %.

## 8. Fuera de alcance
Login y usuarios reales, base de datos (alcanza con memoria + JSONL), firma digital real (se explica en el pitch y en la propuesta normativa) y deploy en la nube del motor (corre en la notebook, conectado al simulador que asigne la organización).
