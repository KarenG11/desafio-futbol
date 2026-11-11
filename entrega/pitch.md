# Pitch y video

**La idea en una frase:** un juez de turno firma desde el celular en segundos, y la orden de bloqueo llega a todos los proveedores de internet del país, no solo a los grandes, con evidencia que nadie puede trucar.

Los números salen solo del verificador oficial. Hoy son los del partido de práctica; el viernes se reemplazan por los del final si cambian.

---

## Pitch (3 minutos)

### 1. El problema (0:00–0:30)
> "El 1 de noviembre, antes del Superclásico, la Justicia tuvo que pedir el bloqueo de 182 sitios piratas. Un partido dura dos horas; un sitio pirata cambia de servidor en minutos.
> Hoy en Argentina eso depende de una sola fiscalía y un solo juzgado. La orden sale por oficio, ENACOM o las cámaras se la reenvían a más de mil proveedores de internet, y **nadie publicó cuántos cumplieron ni cuándo**. Los chicos no llegan a tiempo, y si bloqueás una IP compartida tirás abajo la panadería y el diario del barrio."

### 2. Por qué no copiamos a Europa (0:30–0:50)
> "Europa tuvo que elegir entre rápido y con garantías. Italia bloquea en 30 minutos sin juez, y dejó a Google Drive bloqueado durante horas. Francia acaba de sacar la revisión humana. España tiene juez, pero la lista la maneja LaLiga: miles de IP por fin de semana con una sentencia que nombra unas 120. Y desde septiembre LaLiga tiene autorización para hacer lo mismo acá.
> Acá sacar al juez ni siquiera es legal: la Ley 27.078 dice que un proveedor solo puede bloquear con orden judicial. Así que no sacamos al juez: lo pusimos en el centro, de turno, en el celular."

### 3. Demo en vivo (0:50–2:10)
Una persona maneja el celular del juez, proyectado. Otra muestra el registro y el verificador.
1. **El pedido llega solo.** El celular vibra: "s1.pelotaya.test". Leer en voz alta las cuatro líneas: por qué es el partido (la marca de agua coincide), de dónde sale el video, qué se bloquea y hasta cuándo.
2. **La trampa de la CDN.** Mostrar el pedido de `live.golazo-libre.test`: "Esta IP la comparten 11 sitios legítimos. La plataforma no la bloquea: bloquea solo el nombre."
3. **Lo que no se bloquea.** "Canal Norte pasa el partido legalmente en su dominio, y los resúmenes son de otro partido: la plataforma los descarta sola."
4. **Firmar los N pedidos**, con un toque. Las casillas de los proveedores pasan a verde. Cumbre falla y se reintenta sola. FibraValle recibe el nombre porque no sabe bloquear por IP.
5. **Cambio de turno, minuto 50.** "Entra el juez Martín: ratifica con un toque y desde ahí todo sale con su firma."
6. **Evidencia que no se puede trucar.** Abrir el expediente y mostrar la huella SHA-256. Alterar una línea de la auditoría y correr la verificación: "Salta la alerta en la línea exacta."

### 4. Resultado (2:10–2:35)
> "Corrimos el verificador oficial del desafío. El cliente de ejemplo bloqueó 1 de 7 streams y dejó ver el partido pirata al 92 % de la gente. Nosotros: 7 de 7 streams bloqueados, en todos los proveedores, a menos de un minuto de cada detección. El partido pirata lo pudo ver el 3 % de la gente, contra el 92 % de antes. Cero sitios legítimos afectados, cero bloqueos al licenciatario, cero firmas fuera de turno y cero IPs bloqueadas después del partido."

*(Partido de práctica a x30 con juez automático, `entrega/practica/verificador-practica.txt`. En vivo hay que sumarle lo que tarda el juez en firmar. Si la corrida del final da otros números, reemplazarlos.)*

### 5. Quién paga y qué hace falta (2:35–2:50)
> "Lo paga quien pierde la plata: los titulares de derechos, que según la industria pierden cientos de millones de dólares por año solo en Argentina. El mismo problema está en Perú, México y Colombia. El juez y los proveedores lo usan sin costo. El software nunca fue lo caro: en Italia los proveedores reclaman unos 10 millones de euros por año de trabajo manual. A nosotros vigilar un partido nos cuesta centavos de dólar de nube, según nuestra estimación. Para arrancar alcanza con un piloto en un partido de la liga y una resolución del ENACOM que obligue a cada proveedor a tener un canal electrónico de órdenes. Está en nuestra propuesta normativa y en `escenarios-y-modelo.md`."

### 6. Cierre (2:50–3:00)
> "Un juez, en segundos, con evidencia, y llegando a todos. Somos Alejo, Selene, Luciano, Rocío y Nahuel."

---

## Video de respaldo (hasta 3 minutos)
Se graba sobre un partido de práctica con `--acelerar 6` (con OBS o Win+Alt+R) y se sube a Hacki. **Es también el plan B si falla el Wi-Fi en el pitch.**

| Tiempo | Pantalla | Qué se dice |
|---|---|---|
| 0:00–0:15 | Título + la frase de la idea | El problema en una oración |
| 0:15–0:40 | Simulador y plataforma arrancando; llega el primer pedido al celular | "Detección → expediente → juez" |
| 0:40–1:20 | Pantalla del juez: tarjeta de pelotaya, después la de golazo (IP compartida → nombre) | Evidencia y control de daño colateral |
| 1:20–1:50 | Firmar en lote; las casillas de órdenes pasan a verde; el reintento de Cumbre | Proveedores, confirmación, reintento |
| 1:50–2:15 | Minuto 50: cambio de turno y ratificación | Juez de turno real, firma válida |
| 2:15–2:35 | Expediente con hashes; auditoría alterada → alerta | Integridad de la evidencia |
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
- [x] Números reales del verificador en la sección 4 (práctica; actualizar con el final si cambian)
- [ ] Video grabado y subido a Hacki
- [ ] URL pública de Vercel funcionando desde un celular
- [ ] `entrega/` con el expediente y la auditoría del partido final, y la propuesta normativa
- [ ] Ensayado con cronómetro, dos veces
