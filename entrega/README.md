# Plataforma federal de órdenes de bloqueo en vivo

**Equipo Desafío Fútbol, Hackatón Argentina Space 2026 (track Datos y Streaming, QualyData).**

Mientras se juega el partido, la plataforma detecta un stream pirata y arma el expediente con evidencia verificable. Después se lo muestra al **juez de turno en el celular**, que firma con un toque, y manda la orden a **todos los proveedores de internet**, cada uno en el tipo de bloqueo que acepta. Sigue cada orden hasta que confirma, reintenta las que fallan, levanta sola los bloqueos por IP al terminar el partido y deja todo en una auditoría que no se puede alterar sin que se note.

> Todo es ficticio: proveedores, juzgados, dominios `.test` e IPs de documentación. Solo trabajamos contra el simulador de la organización. No se bloquea nada real.

## Por qué un juez, y por qué en Argentina
El art. 57 inc. a) de la **Ley 27.078 (Argentina Digital)** prohíbe a los proveedores bloquear contenidos "salvo orden judicial". Por eso el modelo italiano, donde el regulador bloquea sin juez, acá no tiene base legal. Además, la Corte Suprema ("Rodríguez c/ Google") exige examinar cada contenido concreto antes de bloquearlo. La plataforma resuelve eso: **cada objetivo nuevo pasa por el juez de turno**, en segundos, con la evidencia a la vista. La propuesta normativa está en [`propuesta_normativa.md`](propuesta_normativa.md). Los escenarios, la comparación con Italia y el modelo de negocio están en [`escenarios-y-modelo.md`](escenarios-y-modelo.md).

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

## Reproducir los resultados (resumen)
Requisitos: Python 3.10 o superior. Todo se probó con Python 3.10.12 en Linux, en una copia limpia del repo y un entorno virtual nuevo.
```bash
# 1. Instalar dependencias
python -m venv .venv && . .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Pruebas con asserts (6 módulos; incluye una prueba contra el simulador oficial)
python -m plataforma.pruebas.unitarias

# 3. Partido completo: levanta el simulador oficial, corre la plataforma, corre evaluacion/verificar.py
#    (sin modificar) y falla si no se cumplen los criterios. Unos 6 minutos cada uno, se pueden correr en paralelo.
python -m plataforma.pruebas.partido_completo --salida salida/practica
python -m plataforma.pruebas.partido_completo --inicio-min 40 --salida salida/turno
python -m plataforma.pruebas.partido_completo --escenario reclamos --salida salida/reclamos
python -m plataforma.pruebas.partido_completo --escenario reclamos --falla dns-desactualizado --salida salida/reclamo-forzado

# 4. Verificar la integridad de lo entregado (cadena de la auditoría y hash del expediente)
python -m plataforma.motor.exportar entrega/auditoria-final.jsonl entrega/expediente-final.json
```
Cada corrida empieza de cero: base SQLite y auditoría nuevas dentro de `--salida`, y el simulador escribe su propio `registro.jsonl`. No usa resultados anteriores. La salida del verificador queda en `--salida/verificar.txt`. Los resultados de referencia están en [`evidencias/RESULTADOS.md`](evidencias/RESULTADOS.md).

A mano, con el juez en la web (dos terminales):
```bash
python simulador/servidor.py --acelerar 6                       # simulador oficial en http://localhost:8080
python -m plataforma.main --sim http://localhost:8080 --local   # motor + API + web en http://localhost:8000/juez/
python evaluacion/verificar.py --log salida/registro.jsonl      # verificador oficial, después del minuto 110
```

## Cómo correrlo (detalle)
```bash
pip install -r requirements.txt
```
El simulador y el verificador oficiales no necesitan dependencias. Todo se probó con Python 3.10.12.
En Windows, anteponé `PYTHONUTF8=1` a cada comando, porque el simulador imprime caracteres que la consola no muestra.

**1. El cerebro contra el partido de práctica** (no necesita red):
```bash
python -m plataforma.analisis.test_cerebro
```
Resultado esperado: `17 de 17 pruebas OK`. Incluye:
- el partido de práctica completo (9 casos, igual que `evaluacion/verdad_practica.json`);
- un "partido final" simulado con otros nombres y varios licenciatarios;
- hosting real (`.com.ar`, `vercel.app`) e IP compartida con sufijo común (ASN de hosting compartido, ASN inconsistente, reclamo previo);
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

**4. Todas las pruebas con asserts** (terminan con código 1 si algo falla):
```bash
python -m plataforma.pruebas.unitarias
```
Corre cerebro, evidencia, reclamos, registro público, base + API (incluye control de turno *fail-closed* y que un levantamiento sin confirmar responde `202`, nunca "levantado") y despacho. La prueba de despacho levanta el **simulador oficial** en un puerto libre y comprueba firma aceptada, firma inválida rechazada (403), IP o nombre según el proveedor, reintento de Cumbre con `orden_id` nuevo y levantamiento confirmado.

**5. El circuito completo contra el simulador, con el juez en la web:**
```bash
python simulador/servidor.py --acelerar 6
python -m plataforma.main --sim http://localhost:8080 --local
```
El segundo comando va en otra terminal. Abrí http://localhost:8000/juez/ con el PIN de `JUEZ_PIN` (con `--local`, `1234` si no está definida). Firmás los pedidos, asumís el turno en el minuto 50 y resolvés los reclamos desde la pantalla. El registro público queda en http://localhost:8000/api/publico. Para la presentación usamos `--acelerar 3` (unos 35 minutos reales). Un recorrido completo así, firmado a mano, está en [`evidencias/demo-manual/`](evidencias/demo-manual/README.md). Cuando el simulador pasa el minuto 110 (el verificador lo necesita para evaluar las IP activas después del partido):
```bash
python evaluacion/verificar.py --log salida/registro.jsonl
```

**6. Partido completo automático + verificador oficial + chequeos** (lo que usamos para las evidencias):
```bash
python -m plataforma.pruebas.partido_completo --salida salida/e2e-practica                  # partido de práctica
python -m plataforma.pruebas.partido_completo --inicio-min 40 --salida salida/e2e-turno     # cambio de turno del minuto 50
python -m plataforma.pruebas.partido_completo --escenario reclamos --salida salida/e2e-reclamos  # hosting compartido
python -m plataforma.pruebas.partido_completo --escenario reclamos --falla dns-desactualizado \
    --salida salida/e2e-reclamo-forzado                                                       # circuito de reclamos
```
Cada uno arranca el simulador oficial (x20, unos 6 minutos), corre el motor con `--juez-automatico` (**solo para pruebas**: el juez de turno aprueba, ratifica y resuelve reclamos solo), corre `evaluacion/verificar.py` al terminar y falla si no se cumple: registro hasta el minuto 110, todas las fases en juego bloqueadas, 0 órdenes fuera de turno, 0 IP activas post partido, 0 falsos positivos, 0 rechazadas, reclamos resueltos, fallidas reenviadas, turno ratificado y cadena de auditoría íntegra. Deja `registro.jsonl` (del simulador), `verificar.txt`/`verificar.json` (salida real del verificador), `auditoria.jsonl`, `publico.json`, `resumen.json` y `export/` con el expediente y la auditoría.

El escenario de reclamos (`plataforma/pruebas/escenarios/`, generado con `generar_reclamos.py` a partir del de práctica, sin tocar `datos/`) pone el stream de verpartido en un hosting compartido. Ahí sus dominios y los de dos sitios legítimos comparten el sufijo `hostcomun.test`, así que solo con el sufijo parecen un mismo sitio. La plataforma tiene que bloquear solo el dominio: se exige 0 daño colateral.

Con `--falla dns-desactualizado` (`plataforma/pruebas/motor_con_falla.py`, **solo pruebas**) el DNS pasivo que ve el cerebro miente para esa IP: lista solo el dominio pirata y un ASN dedicado. Así la plataforma bloquea la IP por error, el simulador emite los reclamos reales y se prueba el resto del circuito: verificación con DNS fresco, levantamiento firmado en todos los proveedores, reemplazo por dominio y la IP marcada como compartida para siempre. El daño colateral de esa corrida es deliberado y el verificador lo informa tal cual; no es una corrida de aceptación.

Resultados reales de las corridas: [`evidencias/RESULTADOS.md`](evidencias/RESULTADOS.md).

**En línea:** la web del juez y el registro público se publican en Vercel. La dirección se completa acá cuando esté el deploy (tarea T11).

## Estado (se actualiza durante el evento)
| Tarea | Estado |
|---|---|
| T01 Cerebro | ✅ Hecho y probado (17 de 17, más 9 de 9 en vivo contra el simulador) |
| T02 Despacho | ✅ Firma HMAC, IP o nombre según proveedor, seguimiento, reintentos con `orden_id` nuevo, levantamiento confirmado. Probado contra el simulador oficial |
| T03 Evidencia y auditoría | ✅ Hecho y probado. El expediente guarda una foto del caso, así su hash no cambia |
| T04 Pantalla del juez | ✅ Contra la API real, con reclamos. PIN en `sessionStorage`. Probada en navegador con un partido completo firmado a mano ([`evidencias/demo-manual/`](evidencias/demo-manual/README.md)). Falta probarla con la URL pública |
| T05 Motor y API | ✅ Loop completo, turno *fail-closed*, solicitudes con resultado real. Probado con el verificador oficial |
| T06 Reclamos | ✅ Correlación real con órdenes activas, levantamiento en todos los proveedores y reemplazo por dominio |
| T07 Registro público | ✅ Desde la base: una entrada por objetivo, estado real por proveedor (`/api/publico`) |
| T08 Propuesta normativa | ✅ [`propuesta_normativa.md`](propuesta_normativa.md), de una página, basada en la versión de Rocío |
| T11 Vercel | ❌ No hay deploy público verificado |
| Video y pitch | Guion listo en [`pitch.md`](pitch.md). El video todavía no está grabado |
| T12 Sandbox | Extra, no hecho |

## Supuestos
- **La firma del juez es un HMAC** con la clave de demostración del simulador, porque es lo que acepta. **Legalmente no alcanza:**
  - la clave es compartida, así que cualquiera que la tenga puede firmar;
  - no se puede verificar sin tenerla;
  - el art. 288 del Código Civil y Comercial exige **firma digital** en documentos electrónicos.

  En producción, la plataforma arma cada orden como documento PDF con su expediente y sus hashes. **El juez la firma con su propio certificado** de firma digital (Ley 25.506), desde el celular, con la [Plataforma de Firma Digital Remota](https://www.argentina.gob.ar/jefatura/innovacion-ciencia-y-tecnologia/innovacion/firma-digital/pfdr), que funciona sin token y con un código de un solo uso. **La plataforma nunca tiene la clave del juez.** Cada proveedor verifica la firma con el certificado público antes de bloquear. "Firmar en lote" son varias firmas, una por orden y cada una con su fundamento; no una sola firma que cubra todo.
- **El acceso del juez es un PIN de demo.** En producción, la identidad la da la propia firma digital.
- **Bloqueo por IP solo con evidencia de un único titular.** Tienen que cumplirse todas estas condiciones (`Cerebro._riesgo_colateral`); si una falla o falta el dato, se bloquea el nombre:
  - el DNS pasivo tiene datos de la IP;
  - todos sus dominios son del mismo sitio. "Sitio" es el dominio registrable: las dos últimas etiquetas más un subconjunto de la Public Suffix List;
  - el titular del ASN es conocido y no es hosting compartido, CDN ni nube;
  - el ASN de la detección coincide con el del DNS;
  - ningún dominio de la IP es de un licenciatario ni de un caso no pirata;
  - la IP no tuvo reclamos verificados.

  El sufijo común solo no alcanza. Límite: si un hosting compartido tiene un nombre de ASN neutro y da subdominios propios a sus clientes, la IP se bloquearía. Ahí entra el reclamo: se levanta y la IP queda marcada. En producción haría falta que el hosting informe a sus clientes (propuesta normativa, punto 4).
- **Si el DNS pasivo no tiene datos de una IP, la tratamos como compartida** y bloqueamos solo el nombre: preferimos no bloquear de más.
- **Todas las órdenes vencen en el minuto en que termina el partido**, también las de nombre. Extenderlas requiere una orden nueva, por proporcionalidad.
- **Un único juzgado de turno por momento**, como en el simulador. La competencia territorial real es parte de la propuesta normativa.

## Seguridad (revisado)
- **Sin claves ni secretos reales.** Las únicas claves son las `clave_firma_demo` de `datos/juzgados.json`, que son de la organización y están marcadas como ficticias en su campo `aviso`. La plataforma las lee del archivo y no las copia a la base, la auditoría, los expedientes, la API ni los logs (`test_despacho` comprueba que el `repr` del firmador no las expone). `.env` y `.vercel/` están en `.gitignore`.
- **PIN del juez.** Sale de la variable `JUEZ_PIN`. Si no está definida, la API rechaza todo. `1234` existe solo con `--local`. La web lo guarda en `sessionStorage` y después de 5 intentos fallidos por minuto responde 429.
- **Solo entorno de prueba.** La plataforma habla únicamente con la URL de `--sim`, que es el simulador. No hay otra salida de red: los "proveedores" son endpoints del simulador y **no se bloquea nada real**. Todos los dominios son `.test`/`.example` y las IP, de documentación (RFC 5737). `simulador/servidor.py` (de la organización, sin cambios) escucha en `0.0.0.0`: corranlo en una máquina local o en una red de confianza.
- **API pública** (`/api/publico`): objetivo, tipo, motivo, juez y juzgado (ficticios y públicos por diseño), minutos y estado por proveedor. No incluye firmas, claves, PIN, capturas ni datos de usuarios. El expediente guarda los hashes de las capturas, no el video.
- **`--juez-automatico` y `--falla`** son solo para pruebas: el primero aprueba sin humano, el segundo inyecta un DNS falso. Ninguno se activa por defecto.

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
- [`propuesta_normativa.md`](propuesta_normativa.md): propuesta normativa de una página (T08), la versión de entrega. [`propuesta-normativa.md`](propuesta-normativa.md) es la versión original de Rocío, conservada como referencia.
- `expediente-final.json` y `auditoria-final.jsonl`: exportados de la corrida definitiva sobre el **partido de práctica** (T03). La auditoría es interna y está encadenada con hashes. Si se corre el partido final, regenerarlos con `--exportar entrega`.
- `registro.jsonl`: registro **oficial del simulador** de esa misma corrida, el que lee `evaluacion/verificar.py`. La plataforma no lo escribe.
- [`evidencias/`](evidencias/RESULTADOS.md): salida del verificador, registro y chequeos de cada corrida definitiva, más la base y el log del motor de la práctica. La corrida v2 anterior está en `evidencias/v2/` y la v1 (anterior al fix de IP compartida) en `evidencias/v1/`.
- [`evidencias/verificacion/`](evidencias/verificacion/practica.txt): verificación cruzada orden por orden de la práctica (registro, auditoría, base y verificador) y el script que la genera.
- [`evidencias/demo-manual/`](evidencias/demo-manual/README.md): partido completo firmado a mano desde la pantalla del juez (sin juez automático), con registro, base, auditoría, verificador, capturas y scripts. Incluye la prueba de firma en lote con su cruce contra el registro del simulador.

## Equipo
Alejo, Selene, Luciano, Rocío y Nahuel. Quién hizo qué está en [`coordinacion/equipo.md`](../coordinacion/equipo.md) y en el historial de `coordinacion/tareas/`.
