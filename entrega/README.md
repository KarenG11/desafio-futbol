# Plataforma federal de órdenes de bloqueo en vivo

**Entrega individual de Karen Gutierrez ([KarenG11](https://github.com/KarenG11)), Hackatón Argentina Space 2026 (track Datos y Streaming, QualyData).** Parte del trabajo del equipo Desafío Fútbol; qué hice yo y qué es del equipo está en [Autoría](#autoría).

Mientras se juega el partido, la plataforma detecta un stream pirata y arma el expediente con evidencia verificable. Después se lo muestra al **juez de turno en el celular**, que firma con un toque, y manda la orden a **todos los proveedores de internet**, cada uno en el tipo de bloqueo que acepta. Sigue cada orden hasta que confirma, reintenta las que fallan, levanta sola los bloqueos por IP al terminar el partido y deja todo en una auditoría que no se puede alterar sin que se note.

**En línea:** https://desafio-futbol-karen.vercel.app (portada, `/partidos`, `/monitoreo`, `/registro` y la pantalla del juez en `/juez/`). Corre sobre una base Postgres en Neon; un partido 100 % online dio 7 de 7 con el verificador oficial ([evidencias](evidencias/RESULTADOS.md)). La URL del equipo, https://desafio-futbol-iota.vercel.app, corre la versión del repo del equipo con el motor anterior, no la de este fork. La forma de verificar esta entrega es correrla en local: está probada de punta a punta contra el simulador y el verificador oficiales.

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
| Sitio del producto | **Tarjeta Roja**: portada (`/`) con el problema, cómo funciona, resultados y modelo de negocio; **monitoreo en vivo** (`/monitoreo`) para el titular de derechos, con streams, órdenes por proveedor, tiempos de bloqueo, reclamos, actividad y la cadena de auditoría verificada en el servidor (`/api/auditoria/integridad`); **registro público** (`/registro`) con buscador y filtros; **centro de partidos** (`/partidos` y `/partido`) con selecciones, banderas y alineaciones de demostración (nombres inventados) sobre la protección real del simulador: cada stream bloqueado aparece como una tarjeta roja al pirata. Solo lectura, sin build. | `plataforma/sitio/` |

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
Abrir http://localhost:8000/juez/ con cualquier juez y la contraseña `1234` (solo en el mock), idealmente en tamaño celular. El mock corre el partido de práctica a x10 con el cerebro real. Para ver el cambio de turno del minuto 50, arrancalo con `MOCK_INICIO_MIN=46`.

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
El segundo comando va en otra terminal. En http://localhost:8000/ está la portada, en http://localhost:8000/monitoreo el tablero en vivo y en http://localhost:8000/registro el registro público. Abrí http://localhost:8000/juez/ y **ingresá con tu usuario de juez y tu contraseña**: con `--local`, `main.py` imprime al arrancar las de cada juez (también `py -m plataforma.claves`). Solo podés firmar mientras estás de turno. Firmás los pedidos, asumís el turno en el minuto 50 y resolvés los reclamos desde la pantalla. El registro público queda en http://localhost:8000/api/publico. Para la presentación usamos `--acelerar 3` (unos 35 minutos reales). Un recorrido completo así, firmado a mano, está en [`evidencias/demo-manual/`](evidencias/demo-manual/README.md). Por defecto la API escucha solo en esta máquina (`127.0.0.1`). Para entrar desde el celular por wifi agregá `--red` (escucha en `0.0.0.0`): exige un secreto `JUEZ_PIN` de al menos 8 caracteres (de él salen las contraseñas de los jueces) y no acepta el `1234` de demo; usalo solo en una red confiable. Cuando el simulador pasa el minuto 110 (el verificador lo necesita para evaluar las IP activas después del partido):
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

**5. Con la base y la web de Vercel** (modo del partido final). La web de T11 corre en Vercel y lee y decide sobre la base. El motor corre donde llegue al simulador y sincroniza con esa misma base:
```bash
DATABASE_URL=postgres://...  python -m plataforma.main --sim URL_DEL_SIMULADOR --base --sin-web --exportar-entrega
```
Para probarlo todo en local, con SQLite: `DATABASE_URL=sqlite:///salida/plataforma.db JUEZ_PIN=<pin> uvicorn plataforma.api.app:app --port 8020` en una terminal, el motor con `--base --sin-web` en otra, y la pantalla del juez en http://localhost:8020/juez/. Así se hizo la corrida `practica-juez-humano/`.

**6. Partido de práctica online (T12), sin ninguna notebook.** En `/juez/demo.html` del deploy se ingresa como juez (usuario y contraseña) y se aprieta "Correr partido de práctica". Opcional: la URL del simulador de la final. La web prende un Vercel Sandbox que clona el repo de `DEMO_REPO` (por defecto, este fork) y levanta el simulador de la organización y el motor apuntando a la base. El juez firma desde `/juez/` en el celular y, al terminar, la página muestra la salida de `evaluacion/verificar.py`. Hay un solo partido a la vez, con velocidad de x6 a x30.

**Partido final y entregable 3.** En la notebook, `--exportar-entrega` deja `entrega/expediente-final.json` y `entrega/auditoria-final.jsonl` al terminar. Si el partido corrió en la nube (demo con la URL del simulador de la final), se bajan por la API pública, verificando la cadena y el hash antes de escribir:
```bash
py -m plataforma.motor.exportar_web --url https://desafio-futbol-karen.vercel.app
py -m plataforma.motor.exportar entrega/auditoria-final.jsonl entrega/expediente-final.json   # comprobación
```

### Deploy propio en Vercel
1. `npx vercel login` y `npx vercel link` (proyecto nuevo). `.vercel/` está en el `.gitignore`.
2. Base: Storage → Neon en el dashboard del proyecto, en São Paulo (`aws-sa-east-1`), que coincide con `gru1` de `vercel.json`. Vercel carga `DATABASE_URL` sola.
3. `npx vercel env add JUEZ_PIN --environment production` con un secreto propio (tipo Secret). Nunca se sube al repo. Las contraseñas de los jueces se ven con `py -m plataforma.claves` (pide el secreto sin mostrarlo).
4. `npx vercel deploy --prod`. La app crea el esquema de la base al arrancar.
5. Probar: `/juez/` con el usuario y la contraseña de un juez y `/juez/demo.html` para el partido online.

## Estado (se actualiza durante el evento)
| Tarea | Estado |
|---|---|
| T01 Cerebro | ✅ Hecho y probado (17 de 17, más 9 de 9 en vivo contra el simulador) |
| T02 Despacho | ✅ Firma HMAC, IP o nombre según proveedor, seguimiento, reintentos con `orden_id` nuevo, levantamiento confirmado. Probado contra el simulador oficial |
| T03 Evidencia y auditoría | ✅ Hecho y probado. El expediente guarda una foto del caso, así su hash no cambia |
| T04 Pantalla del juez | ✅ Contra la API real, con reclamos. **Ingreso con usuario y contraseña por juez**: cada uno firma solo en su turno; al cambio, el saliente queda bloqueado y el entrante ratifica lo pendiente (probado con clics en un partido real). Sesión firmada en `sessionStorage`. Probada desde el celular con la URL pública |
| T05 Motor y API | ✅ Loop completo, turno *fail-closed*, solicitudes con resultado real. Probado con el verificador oficial |
| T06 Reclamos | ✅ Correlación real con órdenes activas, levantamiento en todos los proveedores y reemplazo por dominio |
| T07 Registro público | ✅ Desde la base: una entrada por objetivo, estado real por proveedor (`/api/publico`) |
| T08 Propuesta normativa | ✅ [`propuesta_normativa.md`](propuesta_normativa.md), de una página, basada en la versión de Rocío |
| T10 Validación | ✅ Partido completo y cambio de turno del equipo, en `validacion/` |
| T11 Base y Vercel | ✅ Código de Selene (base y API). **Deploy propio en https://desafio-futbol-karen.vercel.app** con base Postgres en Neon (São Paulo) y el secreto de las contraseñas de los jueces como Secret de Vercel |
| Video y pitch | Guion listo en [`pitch.md`](pitch.md). El video todavía no está grabado |
| T12 Partido de demo online | ✅ Código de Alejo; el Sandbox clona este fork. **Partido 100 % online: 7 de 7, 3,8 % de visibilidad residual, todo en 0 y auditoría íntegra (162 eventos) sobre Neon** ([`evidencias/online/`](evidencias/RESULTADOS.md#corrida-100--online-deploy-propio-en-vercel--neon-12112026)) |
| Integración (este fork) | ✅ Main después del merge: 6 de 6 pruebas unitarias y dos partidos completos de práctica a x30 con 7 de 7 (3,3 % y 3,5 % de visibilidad residual), todo en 0, 12 de 12 chequeos. En Windows con Python 3.15 |

## Corridas del equipo en `main` antes de la integración
Las hizo el motor anterior (en memoria, sincronizado con la base por `sincro_db.py`), que en esta integración se reemplazó por el motor de `plataforma/motor/motor.py`. Se conservan como evidencia de esa etapa; las corridas del motor actual están en [`evidencias/RESULTADOS.md`](evidencias/RESULTADOS.md).

Dos corridas del partido de práctica. Cada una tiene su evidencia (expediente con hash verificado, auditoría íntegra y salida del verificador):

- [`practica-juez-automatico/`](practica-juez-automatico/): a x30, el juez aprueba al instante. Es el techo técnico.
- [`practica-juez-humano/`](practica-juez-humano/): a x10, **con la web de T11 y la base**, y un juez que firma desde la pantalla revisándola cada ~10 segundos. Es la prueba de integración completa: el motor escribe en la base, la web la lee, el juez decide ahí, el cambio de turno va por solicitud y el motor despacha.

| Métrica | Cliente de ejemplo | Juez automático (x30) | **Juez desde la web (x10)** |
|---|---|---|---|
| Fases piratas bloqueadas | 1 de 7 | 7 de 7 | **7 de 7** |
| Visibilidad residual promedio | 92,4 % | 3,1 % | **6,3 %** |
| Primer bloqueo después de la detección | 14,7 min | 0,4–0,9 min | **0,9–1,8 min** (5,3 en el primero, que esperó el ingreso del PIN) |
| Clientes cubiertos por fase | — | 100 % | **100 %** |
| Sitios legítimos afectados / falsos positivos | 0 / 0 | 0 / 0 | **0 / 0** |
| Órdenes rechazadas / firmadas fuera de turno | 1 / 0 | 0 / 0 | **0 / 0** |
| IP bloqueadas después del partido | 0 | 0 | **0** |

**Cómo leer la diferencia:** a x10, los 10 segundos que tarda el juez son 1,7 minutos de partido. En un partido real (x1), esos mismos 10 segundos son 0,17 minutos, así que el resultado real se acerca al del juez automático. Las órdenes que Cumbre hace fallar se reintentan solas.

## Supuestos
- **La firma del juez es un HMAC** con la clave de demostración del simulador, porque es lo que acepta. **Legalmente no alcanza:**
  - la clave es compartida, así que cualquiera que la tenga puede firmar;
  - no se puede verificar sin tenerla;
  - el art. 288 del Código Civil y Comercial exige **firma digital** en documentos electrónicos.

  En producción, la plataforma arma cada orden como documento PDF con su expediente y sus hashes. **El juez la firma con su propio certificado** de firma digital (Ley 25.506), desde el celular, con la [Plataforma de Firma Digital Remota](https://www.argentina.gob.ar/jefatura/innovacion-ciencia-y-tecnologia/innovacion/firma-digital/pfdr), que funciona sin token y con un código de un solo uso. **La plataforma nunca tiene la clave del juez.** Cada proveedor verifica la firma con el certificado público antes de bloquear. "Firmar en lote" son varias firmas, una por orden y cada una con su fundamento; no una sola firma que cubra todo.
- **Cada juez entra con su usuario y una contraseña de demostración**, derivada con HMAC del secreto `JUEZ_PIN` y su usuario (así sirve también para los jueces de un escenario nuevo). La sesión es un token firmado que vence a las 12 h, y la API toma de ahí quién firma: nadie puede firmar por otro (403) ni fuera de su turno (409). En producción, la identidad la da la propia firma digital.
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
- **Contraseñas de los jueces.** Salen del secreto `JUEZ_PIN`; si no está definido, nadie puede ingresar. `1234` existe solo con `--local`. No se guardan en ningún lado. La web guarda solo la sesión en `sessionStorage`, y después de 5 intentos fallidos por minuto la API responde 429.
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
- [`propuesta_normativa.md`](propuesta_normativa.md): propuesta normativa de una página (T08), la versión de entrega. [`anexos/propuesta-normativa-original-rocio.md`](anexos/propuesta-normativa-original-rocio.md) es la versión original de Rocío, conservada como referencia.
- `expediente-final.json` y `auditoria-final.jsonl`: **del partido final (`final-01`)**, íntegros (cadena de 68 eventos y hash del expediente verificados con `python -m plataforma.motor.exportar`). **Aclaración honesta:** la instancia pasó a la final recién a las 11:10; al arrancar, el simulador respondió un 502 y luego un timeout, y ese corte de red detuvo el motor a los pocos segundos. La plataforma se volvió a correr contra la misma instancia a las 11:53, con el partido ya terminado: leyó todas las detecciones de la final desde el principio (8 streams piratas, 2 descartados por el cerebro) y armó los 8 expedientes y pedidos, pero **no se envió ninguna orden** porque el partido había terminado. El motor ya está corregido: un corte de red ahora se anota y se reintenta en el ciclo siguiente, sin detener el partido. Las corridas completas del circuito (7 de 7, todo en 0) están en [`evidencias/RESULTADOS.md`](evidencias/RESULTADOS.md).
- `registro.jsonl`: registro **oficial del simulador** de esa misma corrida, el que lee `evaluacion/verificar.py`. La plataforma no lo escribe.
- [`evidencias/`](evidencias/RESULTADOS.md): salida del verificador, registro y chequeos de cada corrida definitiva, más la base y el log del motor de la práctica. La corrida v2 anterior está en `evidencias/v2/` y la v1 (anterior al fix de IP compartida) en `evidencias/v1/`.
- [`evidencias/verificacion/`](evidencias/verificacion/practica.txt): verificación cruzada orden por orden de la práctica (registro, auditoría, base y verificador) y el script que la genera.
- [`evidencias/demo-manual/`](evidencias/demo-manual/README.md): partido completo firmado a mano desde la pantalla del juez (sin juez automático), con registro, base, auditoría, verificador, capturas y scripts. Incluye la prueba de firma en lote con su cruce contra el registro del simulador.

## Autoría
- **Karen Gutierrez (esta entrega):** el sitio del producto Tarjeta Roja (`plataforma/sitio/`: portada, monitoreo en vivo y registro público) y la verificación de la auditoría en la API, el motor actual y su CLI (`plataforma/motor/motor.py`, `__main__.py`, `simulador.py`, `exportar.py`, `plataforma/main.py`), el despacho firmado (`plataforma/despacho/`), los ajustes de integración en cerebro, evidencia, reclamos, registro público, base, API y web, las pruebas de punta a punta (`plataforma/pruebas/`, con el escenario de reclamos y la falla inyectada), las evidencias de `entrega/evidencias/` y la integración con el `main` del equipo (PR #1 de este fork).
- **Equipo Desafío Fútbol (Alejo, Selene, Rocío y el resto del equipo):** diseño y contratos (`coordinacion/`), cerebro (Alejo), pantalla del juez y partido de demo online en Vercel Sandbox (Alejo), base y API (Selene), registro público, reclamos y la propuesta normativa original (Rocío), pitch y escenarios. Quién hizo qué está en [`coordinacion/equipo.md`](../coordinacion/equipo.md), en `coordinacion/tareas/` y en el historial de git.
