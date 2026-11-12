# Pitch y video

**Producto:** Tarjeta Roja, plataforma federal de órdenes judiciales de bloqueo en vivo. Entrega individual de Karen Gutierrez, sobre el trabajo del equipo Desafío Fútbol.

**La idea en una frase:** un juez de turno firma desde el celular en segundos, y la orden de bloqueo llega a todos los proveedores de internet del país, no solo a los grandes, con evidencia que nadie puede trucar.

**Pantallas que se muestran:** portada (`/`), tablero en vivo para el titular de derechos (`/monitoreo`), pantalla del juez en el celular (`/juez/`), registro público (`/registro`) y el botón de partido de demo (`/juez/demo.html`).

Los números de la sección 4 son reales: salen del verificador oficial sobre la corrida definitiva del partido de práctica (simulador x20), en [`evidencias/RESULTADOS.md`](evidencias/RESULTADOS.md). Si se corre el partido final, se reemplazan por los de esa corrida. No inventar ninguno.

---

## Pitch (3 minutos)
Ritmo de referencia: unas 140 palabras por minuto. Lo que se dice suma unas 350 palabras; el resto del tiempo es demo.

### 1. El problema (0:00–0:25)
> "El 1 de noviembre, antes del Superclásico, la Justicia pidió bloquear 182 sitios piratas. Un partido dura dos horas; un sitio pirata cambia de servidor en minutos. Hoy la orden sale por oficio, ENACOM o las cámaras la reenvían a más de mil proveedores, y nadie publica quién cumplió ni cuándo. Y si bloqueás una IP compartida, tirás abajo la panadería del barrio."

### 2. Nuestra respuesta (0:25–0:40)
> "Italia bloquea sin juez, y dejó a Google Drive bloqueado durante horas. Acá no se puede: la Ley 27.078 exige orden judicial. Así que pusimos al juez en el centro: de turno, en el celular, firmando en segundos."

### 3. Demo en vivo (0:40–2:05)
En el proyector, el tablero `/monitoreo` en la notebook. En la mano, el celular del juez con `/juez/`; si se puede, duplicar su pantalla. El partido se lanza antes de empezar desde `/juez/demo.html` (x6, juez automático **destildado**) para que el primer pedido llegue durante la demo.
0. **El tablero.** "Esto es lo que ve el dueño de los derechos: el minuto, el juez de turno, cada stream detectado y el estado en cada proveedor."
1. **Llega el pedido** (`s1.pelotaya.test`). "La marca de agua es la del partido. Se ve de dónde sale el video, qué se bloquea y hasta cuándo."
2. **La trampa de la CDN** (`live.golazo-libre.test`). "Esta IP la comparten 11 sitios legítimos: bloqueamos solo el nombre."
3. **Lo que no se bloquea.** "Canal Norte es licenciatario y los resúmenes son de otro partido: se descartan solos."
4. **Firma en lote**, con un toque. En el celular y en el tablero, las casillas de los proveedores pasan a verde y se ve el tiempo de detección al primer bloqueo. "Si Cumbre falla, se reenvía sola con otro número de orden. FibraValle recibe el nombre porque no bloquea por IP."
5. **Cambio de turno, minuto 50.** "Entra el juez Martín, ratifica con un toque y desde ahí todo sale con su firma."
6. **Evidencia.** Se muestra la huella SHA-256 del expediente y el sello "Cadena íntegra" del tablero, que el servidor recalcula con cada evento. Se altera una línea de la auditoría y `python -m plataforma.motor.exportar` responde `cadena de auditoría rota en seq 41`.
7. **Vencimiento y transparencia.** "Al minuto 105 todo vence solo." Se abre `/registro`: cualquier persona busca un sitio y ve quién lo ordenó, por qué, hasta cuándo y en qué proveedores se aplicó.

Si en vivo aparece un reclamo, se resuelve desde la misma pantalla: levantamiento firmado en todos los proveedores y reemplazo por el nombre. En el partido de práctica no hubo ninguno, porque no bloqueamos IPs compartidas.

### 4. Resultado (2:05–2:30)
> "Corrimos el verificador oficial del desafío sobre el partido de práctica. El cliente de ejemplo bloqueó 1 de 7 streams y dejó 86,5 % de visibilidad residual. Nosotros: 7 de 7, cada uno en menos de un minuto de partido, con 3,1 % de visibilidad residual. Cero sitios legítimos afectados, cero falsos positivos, cero órdenes fuera de turno y cero IPs bloqueadas después del partido."

Si preguntan por los reclamos: "Para probarlos le hicimos creer a la plataforma que una IP compartida era exclusiva. El reclamo de la panadería se resolvió en 0,13 minutos de partido, pero las órdenes por IP alcanzaron a estar activas entre 1 y 4 minutos. Por eso no bloqueamos IPs compartidas." Es una prueba con **falla inyectada**, no un resultado normal.

### 5. Quién paga y qué hace falta (2:30–2:50)
> "Paga el titular de derechos; al juez y a los proveedores no les cuesta nada. Para arrancar alcanza con un piloto en un partido de la liga, una acordada de turno y una resolución del ENACOM que obligue a cada proveedor a tener un canal electrónico de órdenes. Está en nuestra propuesta normativa."

### 6. Cierre (2:50–3:00)
> "Tarjeta Roja: un juez, en segundos, con evidencia, y llegando a todos. Soy Karen Gutierrez, del equipo Desafío Fútbol."

---

## Arquitectura (para mostrar si piden detalle)
`simulador → cerebro (clasifica y decide IP o nombre) → evidencia (expediente con hashes) → juez de turno en el celular → despacho (firma HMAC, un envío por proveedor, reintentos) → confirmación → vencimiento o levantamiento`, todo con auditoría encadenada y registro público. El motor es el único que habla con el simulador. La web solo crea pedidos de decisión, y si el motor no reporta estado no se firma nada. Diagrama y piezas: [`README.md`](README.md#cómo-funciona).

## Métricas reales (corrida definitiva v2, simulador x20, verificador oficial)
| Corrida | Tipo | Fases | Residual | Colateral | Falsos positivos | Fuera de turno | IP post partido |
|---|---|---|---|---|---|---|---|
| Cliente de ejemplo de la organización | referencia | 1 de 7 | 86,5 % | 0 | 0 | 0 | 0 |
| Partido de práctica | normal | 7 de 7 | 3,1 % | 0 | 0 | 0 | 0 |
| Hosting compartido con sufijo común | normal | 7 de 7 | 3,1 % | 0 | 0 | 0 | 0 |
| Arranque en el minuto 40 (cambio de turno) | normal | 6 de 7* | 27,6 % | 0 | 0 | 0 | 0 |
| DNS desactualizado | **falla inyectada** | 7 de 7 | 3,1 % | 3 órdenes, 2 dominios (levantadas por reclamo) | 0 | 0 | 0 |

\* La fase 1 terminó antes de que arrancara la corrida. Las cifras definitivas y las salidas del verificador están en [`evidencias/RESULTADOS.md`](evidencias/RESULTADOS.md); si la corrida definitiva cambia algún número, manda esa.

## Video de respaldo (hasta 3 minutos)
Se graba con la grabadora de Windows (Win+Alt+R, o Win+Shift+R para elegir una zona) u OBS, y se sube a Hacki. **Es también el plan B si falla el Wi-Fi en el pitch.**

**Preparación (antes de grabar):**
1. Una terminal de PowerShell en la carpeta del repo:
   ```
   $env:PYTHONUTF8="1"; $env:DATABASE_URL="sqlite:///salida/video/plataforma.db"; $env:JUEZ_PIN="1234"
   py -m uvicorn plataforma.api.app:app --port 8000
   ```
2. En el navegador, dos ventanas lado a lado: a la izquierda `http://localhost:8000/monitoreo`; a la derecha `http://localhost:8000/juez/` en modo celular (F12 → ícono de dispositivo → 390 px de ancho).
3. Desde `http://localhost:8000/juez/demo.html`: PIN `1234`, x6, juez automático **destildado**. A x6 el partido dura ~18 min reales: se graba en tramos y se edita (Clipchamp viene con Windows).

| Tiempo | Pantalla | Qué se dice |
|---|---|---|
| 0:00–0:15 | Portada `/`: título y "El problema que resolvemos" | El problema en una oración: un partido dura dos horas, un pirata cambia de servidor en minutos |
| 0:15–0:35 | `/juez/demo.html` → "Correr partido"; el tablero pasa a "En vivo" | "Detección → expediente → juez" |
| 0:35–1:10 | Celular del juez: tarjeta de pelotaya, después la de golazo (IP compartida → solo nombre). En el tablero, "Detecciones descartadas" | Evidencia y cero daño colateral; licenciatario y otra señal descartados solos |
| 1:10–1:40 | Firmar en lote; en el tablero las casillas pasan a verde, el KPI "Detección → primer bloqueo" y el reintento de Cumbre | Todos los proveedores, confirmación, reintento automático |
| 1:40–2:00 | Minuto 50: el celular pide asumir el turno; el tablero muestra "Turno ratificado" | Juez de turno real, firma válida |
| 2:00–2:20 | Sello "Cadena íntegra" en el tablero; en terminal, auditoría alterada → `cadena rota` | Evidencia que no se puede trucar |
| 2:20–2:45 | `/registro`: buscar `pelotaya`; después la salida del verificador al pie de `demo.html` | Transparencia + números finales: 7 de 7, ~3 %, todo en 0 |
| 2:45–3:00 | Portada: "Quién paga" y nombre | Paga el titular de derechos; Karen Gutierrez, equipo Desafío Fútbol |

## Preguntas probables del jurado
Respuestas de 15 segundos. El detalle y las fuentes están en `coordinacion/investigacion/soluciones-parecidas.md`.

| Si preguntan | Respondemos |
|---|---|
| ¿Y el sobrebloqueo? | Si la IP es compartida (CDN u hosting), bloqueamos solo el nombre. Toda IP vence al terminar el partido. El registro público deja que cualquiera vea si su sitio cayó y reclame. |
| ¿Existe un juez de turno que firme esto un domingo a la noche? | Hoy no lo sabemos: es parte de la propuesta normativa (una acordada de turno). Sin firma no sale ninguna orden: preferimos no bloquear antes que bloquear sin juez. |
| ¿Por qué no administrativo, como Brasil o Perú, que es más rápido? | Porque el art. 57 de la Ley 27.078 exige orden judicial. Nuestro objetivo es que firmar tarde lo mismo que un aviso administrativo. |
| Se van a VPN o a DNS públicos. | Una minoría sí. Apuntamos al acceso masivo durante los 90 minutos y lo medimos con la visibilidad residual. En el Reino Unido, bloquear muchos sitios a la vez bajó la piratería un 16 a 22 %, aunque había VPN (estudio de Carnegie Mellon sobre sitios en general, no sobre fútbol en vivo). |
| ¿Hay pruebas de que el bloqueo en vivo funciona? | No hay un estudio específico, y la Comisión Europea lo admite. Por eso el registro público genera esos datos. |
| LaLiga ya tiene su orden en Argentina. ¿Para qué esto? | Esas órdenes pueden pasar por la plataforma y ganan acuse por proveedor, vencimiento y la regla anti-CDN. Somos el canal, no un competidor. |
| ¿Quién paga? Los ISP chicos no pueden. | Paga el titular de derechos. Para el proveedor es gratis y recibe el tipo de bloqueo que declaró que puede aplicar. |
| ¿No viola la neutralidad de red? | El art. 56 la garantiza y el art. 57 admite el bloqueo con orden judicial. Cada orden la tiene, con alcance y vencimiento. |
| ¿El Estado va a vigilar qué mira la gente? | No. Se detectan streams piratas, no usuarios. Los expedientes no tienen datos de abonados. |
| ¿Cuánto cuesta? | De nube, entre 20 y 60 dólares por mes para 30 partidos (estimación nuestra con precios de Vercel y Neon). Lo caro es la operación, y la cubre el titular. |
| ¿Lo que vimos es real? | Decir qué está simulado (proveedores, firma HMAC, datos) y qué no. |

## Números que no decimos en el escenario
Se contradicen entre fuentes o los publica solo la industria:
- **% de hogares argentinos que piratean** (42,6 / 45,5 / 46 / 54,4 %): el 42,6 % parece ser el promedio de LatAm. Si hace falta: "cerca de la mitad, según la industria".
- **Pérdidas en dólares de Argentina** (258 / 571 / 590 millones): no hay cifra auditada. Decir "cientos de millones, según la industria".
- **El "60 %" de LaLiga**: son dos afirmaciones distintas, las dos autodeclaradas. No usar.
- **Costo de Piracy Shield**: va de 20 mil a 2 millones de euros según la fuente. Usar solo los ~10 M€/año que reclaman los proveedores.
- **Nuestra velocidad**: solo la que muestre el cronómetro de la demo.

## Antes de subir
- [x] Cronómetro en pantalla durante la demo: el tablero `/monitoreo` muestra el minuto y "Detección → primer bloqueo" en vivo
- [x] Números reales del verificador en la sección 4 (partido de práctica; reemplazar si se corre el final)
- [x] Ensayo del comando de la final en la notebook (`--sim http://localhost:8080 --local`): 7 de 7, 3,4 %, todo en 0, auditoría y expediente íntegros
- [ ] Notebook sin suspensión ni acción al cerrar la tapa, enchufada
- [ ] Video grabado y subido a Hacki
- [x] URL pública de Vercel (deploy propio) funcionando: partido online 7 de 7, 3,8 %. Falta probarla desde el celular
- [x] `entrega/` con expediente, auditoría (del partido de práctica) y [propuesta normativa](propuesta_normativa.md). Regenerar con el partido final si se corre
- [ ] Ensayado con cronómetro, dos veces
