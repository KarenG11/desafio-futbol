# Plataforma federal de órdenes de bloqueo en vivo

**Equipo Desafío Fútbol, Hackatón Argentina Space 2026 (track Datos y Streaming, QualyData).**

Mientras se juega el partido, la plataforma detecta un stream pirata y arma el expediente con evidencia verificable. Después se lo muestra al **juez de turno en el celular**, que firma con un toque, y manda la orden a **todos los proveedores de internet**, cada uno en el tipo de bloqueo que acepta. Sigue cada orden hasta que confirma, reintenta las que fallan, levanta sola los bloqueos por IP al terminar el partido y deja todo en una auditoría que no se puede alterar sin que se note.

> Todo es ficticio: proveedores, juzgados, dominios `.test` e IPs de documentación. Solo trabajamos contra el simulador de la organización. No se bloquea nada real.

## Por qué un juez, y por qué en Argentina
El art. 57 inc. a) de la **Ley 27.078 (Argentina Digital)** prohíbe a los proveedores bloquear contenidos "salvo orden judicial". Por eso el modelo italiano, donde el regulador bloquea sin juez, acá no tiene base legal. Además, la Corte Suprema ("Rodríguez c/ Google") exige examinar cada contenido concreto antes de bloquearlo. La plataforma resuelve eso: **cada objetivo nuevo pasa por el juez de turno**, en segundos, con la evidencia a la vista. La propuesta normativa está en [`propuesta-normativa.md`](propuesta-normativa.md). Los escenarios, la comparación con Italia y el modelo de negocio están en [`escenarios-y-modelo.md`](escenarios-y-modelo.md).

## Cómo funciona
```
simulador ──detecciones──► CEREBRO ──caso pirata──► EVIDENCIA ──expediente──► PEDIDO
                           (analisis/)               (evidencia/)                 │
                                                                                  ▼
proveedores ◄──órdenes firmadas── DESPACHO ◄──aprobado── JUEZ EN EL CELULAR (web/)
   │                              (despacho/)
   └──confirmación, reintentos, vencimiento──► AUDITORÍA encadenada + REGISTRO PÚBLICO
```
| Pieza | Qué decide | Dónde |
|---|---|---|
| Cerebro | Agrupa avisos repetidos. Verifica la marca de agua contra el partido (oficial, licenciatario en su dominio, otra señal o sin marca). Si la IP es compartida con sitios legítimos, recomienda bloquear el **nombre** y no la IP. | `plataforma/analisis/` |
| Evidencia | Expediente con SHA-256 de cada captura (sobre el binario), servidor, ASN, sitios en la misma IP, promoción del enlace y hash del expediente. La auditoría está encadenada con hashes. | `plataforma/evidencia/` |
| Juez | Pantalla para celular: lee el pedido en lenguaje claro y firma en lote. Rechazar exige un motivo. En el cambio de turno, el juez entrante ratifica las órdenes vigentes. | `plataforma/web/` |
| Despacho | Firma con el juez de turno en el minuto del envío. Manda IP o nombre según lo que acepta cada proveedor, reintenta las fallidas y vence en el fin del partido. | `plataforma/despacho/` |
| Motor y API | El loop que une todo, y la API que usa la web. | `plataforma/motor/`, `plataforma/api/` |

Las reglas y el porqué de cada decisión están en [`coordinacion/diseno.md`](../coordinacion/diseno.md). Las formas de datos entre piezas están en [`coordinacion/contratos.md`](../coordinacion/contratos.md).

## Cómo correrlo
Requisitos: Python 3.10 o superior.
```bash
pip install fastapi uvicorn
```
En Windows, anteponé `PYTHONUTF8=1` a cada comando, porque el simulador imprime caracteres que la consola no muestra.

**1. El cerebro contra el partido de práctica** (no necesita red):
```bash
python -m plataforma.analisis.test_cerebro
```
Resultado esperado: `13 de 13 pruebas OK`. Incluye:
- el partido de práctica completo (9 casos, igual que `evaluacion/verdad_practica.json`);
- un "partido final" simulado con otros nombres y varios licenciatarios;
- hosting real (`.com.ar`, `vercel.app`);
- DNS caído;
- mayúsculas y espacios.

Para ensayarlo **en vivo contra el simulador**, solo leyendo, sin mandar órdenes:
```bash
python simulador/servidor.py --acelerar 30
python -m plataforma.analisis.ensayo_en_vivo --sim http://localhost:8080 --verdad evaluacion/verdad_practica.json
```
El segundo comando va en otra terminal. Resultado: 9 de 9.

**2. La evidencia y la auditoría** (detecta alteraciones):
```bash
python -m plataforma.evidencia.test_evidencia
```

**3. La pantalla del juez con datos simulados** (sin base ni motor):
```bash
uvicorn plataforma.web.mock_api:app --port 8000
```
Abrir http://localhost:8000/juez/ con el PIN `1234`, idealmente en tamaño celular. El mock corre el partido de práctica a x10 con el cerebro real. Para ver el cambio de turno del minuto 50, arrancalo con `MOCK_INICIO_MIN=46`.

**4. El circuito completo contra el simulador** (necesita que estén T02 y T05; ver "Estado"):
```bash
python simulador/servidor.py --acelerar 6
python -m plataforma.main --sim http://localhost:8080 --local
python evaluacion/verificar.py --log salida/registro.jsonl
```
El segundo comando va en otra terminal. Sin `--juez-automatico`, aprobás desde http://localhost:8000/juez/. El tercero se corre cuando termina el partido.

**En línea:** la web del juez y el registro público se publican en Vercel. La dirección se completa acá cuando esté el deploy (tarea T11).

## Estado (se actualiza durante el evento)
| Tarea | Estado |
|---|---|
| T01 Cerebro | ✅ Hecho y probado (13 de 13, más 9 de 9 en vivo contra el simulador) |
| T03 Evidencia y auditoría | ✅ Hecho y probado |
| T04 Pantalla del juez | ✅ Funciona contra el mock. Falta probarla con la URL pública |
| T08 Propuesta normativa | ✅ Hecho (Rocío) |
| T02 Despacho, T05 Motor, T11 Base y Vercel | En curso |
| T07 Registro público | En curso (Rocío) |
| T06 Reclamos, T12 Sandbox | Extras |

## Supuestos
- **La firma del juez es un HMAC** con la clave de demostración del simulador, porque es lo que acepta. **Legalmente no alcanza:**
  - la clave es compartida, así que cualquiera que la tenga puede firmar;
  - no se puede verificar sin tenerla;
  - el art. 288 del Código Civil y Comercial exige **firma digital** en documentos electrónicos.

  En producción, la plataforma arma cada orden como documento PDF con su expediente y sus hashes. **El juez la firma con su propio certificado** de firma digital (Ley 25.506), desde el celular, con la [Plataforma de Firma Digital Remota](https://www.argentina.gob.ar/jefatura/innovacion-ciencia-y-tecnologia/innovacion/firma-digital/pfdr), que funciona sin token y con un código de un solo uso. **La plataforma nunca tiene la clave del juez.** Cada proveedor verifica la firma con el certificado público antes de bloquear. "Firmar en lote" son varias firmas, una por orden y cada una con su fundamento; no una sola firma que cubra todo.
- **El acceso del juez es un PIN de demo.** En producción, la identidad la da la propia firma digital.
- **"Sitio" son las dos últimas etiquetas del dominio** (`s1.pelotaya.test` → `pelotaya.test`). Alcanza para los dominios `.test` del simulador; en producción haría falta la Public Suffix List.
- **Si el DNS pasivo no tiene datos de una IP, la tratamos como compartida** y bloqueamos solo el nombre: preferimos no bloquear de más.
- **Todas las órdenes vencen en el minuto en que termina el partido**, también las de nombre. Extenderlas requiere una orden nueva, por proporcionalidad.
- **Un único juzgado de turno por momento**, como en el simulador. La competencia territorial real es parte de la propuesta normativa.

## Qué existía antes del evento y qué es nuestro
- **De la organización (QualyData), sin cambios:** `simulador/`, `evaluacion/`, `ejemplos/` y `datos/`. Repo original: [qualydata-org/desafio-futbol](https://github.com/qualydata-org/desafio-futbol).
- **Hecho por el equipo durante la hackatón (11 al 13 de noviembre de 2026):** `plataforma/`, `entrega/` y `coordinacion/`. `coordinacion/` es el tablero, el buzón y los contratos con los que se coordinaron los agentes de los 5 integrantes.
- **Librerías públicas:**
  - FastAPI y Uvicorn, para la API y para servir la web;
  - psycopg, para Postgres en el deploy;
  - del navegador, solo las fuentes Public Sans y Barlow Condensed de Google Fonts.

  El resto es la biblioteca estándar de Python y JavaScript sin dependencias.

## Entregables (`entrega/`)
- `README.md`: este archivo.
- [`escenarios-y-modelo.md`](escenarios-y-modelo.md): cada escenario (del partido y del mundo real), cómo lo resuelve la plataforma, quién paga y el camino a producción.
- [`pitch.md`](pitch.md): guion del pitch y del video de 3 minutos.
- `propuesta-normativa.md`: 1 página (T08).
- `expediente-final.json` y `auditoria-final.jsonl`: exportados del partido final (T03).

## Equipo
Alejo, Selene, Luciano, Rocío y Nahuel. Quién hizo qué está en [`coordinacion/equipo.md`](../coordinacion/equipo.md) y en el historial de `coordinacion/tareas/`.
