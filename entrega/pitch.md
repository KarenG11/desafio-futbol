# Pitch y video

**La idea en una frase:** un juez de turno firma desde el celular en segundos, y la orden de bloqueo llega a todos los proveedores de internet del país, no solo a los grandes, con evidencia que nadie puede trucar.

Los números de la sección 4 son reales: salen del verificador oficial sobre la corrida definitiva del partido de práctica (simulador x20), en [`evidencias/RESULTADOS.md`](evidencias/RESULTADOS.md). Si se corre el partido final, se reemplazan por los de esa corrida. No inventar ninguno.

---

## Pitch (3 minutos)
Ritmo de referencia: unas 140 palabras por minuto. Lo que se dice suma unas 350 palabras; el resto del tiempo es demo.

### 1. El problema (0:00–0:25)
> "El 1 de noviembre, antes del Superclásico, la Justicia pidió bloquear 182 sitios piratas. Un partido dura dos horas; un sitio pirata cambia de servidor en minutos. Hoy la orden sale por oficio, ENACOM o las cámaras la reenvían a más de mil proveedores, y nadie publica quién cumplió ni cuándo. Y si bloqueás una IP compartida, tirás abajo la panadería del barrio."

### 2. Nuestra respuesta (0:25–0:40)
> "Italia bloquea sin juez, y dejó a Google Drive bloqueado durante horas. Acá no se puede: la Ley 27.078 exige orden judicial. Así que pusimos al juez en el centro: de turno, en el celular, firmando en segundos."

### 3. Demo en vivo (0:40–2:05)
Una persona maneja el celular del juez, proyectado. Otra muestra el registro público y el verificador.
1. **Llega el pedido** (`s1.pelotaya.test`). "La marca de agua es la del partido. Se ve de dónde sale el video, qué se bloquea y hasta cuándo."
2. **La trampa de la CDN** (`live.golazo-libre.test`). "Esta IP la comparten 11 sitios legítimos: bloqueamos solo el nombre."
3. **Lo que no se bloquea.** "Canal Norte es licenciatario y los resúmenes son de otro partido: se descartan solos."
4. **Firma en lote**, con un toque. Las casillas de los proveedores pasan a verde. "Si Cumbre falla, se reenvía sola con otro número de orden. FibraValle recibe el nombre porque no bloquea por IP."
5. **Cambio de turno, minuto 50.** "Entra el juez Martín, ratifica con un toque y desde ahí todo sale con su firma."
6. **Evidencia.** Se muestra la huella SHA-256 del expediente. Se altera una línea de la auditoría y `python -m plataforma.motor.exportar` responde `cadena de auditoría rota en seq 41`.
7. **Vencimiento.** "Al minuto 105 todo vence solo y el registro público lo muestra."

Si en vivo aparece un reclamo, se resuelve desde la misma pantalla: levantamiento firmado en todos los proveedores y reemplazo por el nombre. En el partido de práctica no hubo ninguno, porque no bloqueamos IPs compartidas.

### 4. Resultado (2:05–2:30)
> "Corrimos el verificador oficial del desafío sobre el partido de práctica. El cliente de ejemplo bloqueó 1 de 7 streams y dejó 86,5 % de visibilidad residual. Nosotros: 7 de 7, cada uno en menos de un minuto de partido, con 3,1 % de visibilidad residual. Cero sitios legítimos afectados, cero falsos positivos, cero órdenes fuera de turno y cero IPs bloqueadas después del partido."

Si preguntan por los reclamos: "Para probarlos le hicimos creer a la plataforma que una IP compartida era exclusiva. El reclamo de la panadería se resolvió en 0,13 minutos de partido, pero las órdenes por IP alcanzaron a estar activas entre 1 y 4 minutos. Por eso no bloqueamos IPs compartidas." Es una prueba con **falla inyectada**, no un resultado normal.

### 5. Quién paga y qué hace falta (2:30–2:50)
> "Paga el titular de derechos; al juez y a los proveedores no les cuesta nada. Para arrancar alcanza con un piloto en un partido de la liga, una acordada de turno y una resolución del ENACOM que obligue a cada proveedor a tener un canal electrónico de órdenes. Está en nuestra propuesta normativa."

### 6. Cierre (2:50–3:00)
> "Un juez, en segundos, con evidencia, y llegando a todos. Somos Alejo, Selene, Luciano, Rocío y Nahuel."

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
Se graba sobre un partido de práctica con `--acelerar 6` (con OBS o Win+Alt+R) y se sube a Hacki. **Es también el plan B si falla el Wi-Fi en el pitch.**

| Tiempo | Pantalla | Qué se dice |
|---|---|---|
| 0:00–0:15 | Título + la frase de la idea | El problema en una oración |
| 0:15–0:40 | Simulador y plataforma arrancando; llega el primer pedido al celular | "Detección → expediente → juez" |
| 0:40–1:20 | Pantalla del juez: tarjeta de pelotaya, después la de golazo (IP compartida → nombre) | Evidencia y control de daño colateral |
| 1:20–1:50 | Firmar en lote; las casillas de órdenes pasan a verde; el reintento de Cumbre | Proveedores, confirmación, reintento |
| 1:50–2:15 | Minuto 50: cambio de turno y ratificación | Juez de turno real, firma válida |
| 2:15–2:35 | Expediente con hashes; auditoría alterada → alerta. Si apareció, un reclamo levantado | Integridad de la evidencia y reclamos |
| 2:35–2:55 | Fin del partido: las IP vencen solas. Salida de `evaluacion/verificar.py` | Vencimiento + números finales |
| 2:55–3:00 | Repo y nombres | — |

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
- [ ] Cronómetro en pantalla durante la demo: desde la detección hasta la confirmación del último proveedor
- [x] Números reales del verificador en la sección 4 (partido de práctica; reemplazar si se corre el final)
- [ ] Video grabado y subido a Hacki
- [ ] URL pública de Vercel funcionando desde un celular
- [x] `entrega/` con expediente, auditoría (del partido de práctica) y [propuesta normativa](propuesta_normativa.md). Regenerar con el partido final si se corre
- [ ] Ensayado con cronómetro, dos veces
