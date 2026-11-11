# Pitch y video

**La idea en una frase:** un juez de turno firma desde el celular en segundos, y la orden de bloqueo llega a todos los proveedores de internet del país, no solo a los grandes, con evidencia que nadie puede trucar.

Los números entre [corchetes] se completan con la corrida del partido final. No inventar ninguno.

---

## Pitch (3 minutos)

### 1. El problema (0:00–0:30)
> "El 1 de noviembre, antes del Superclásico, la Justicia tuvo que pedir el bloqueo de 182 sitios piratas. Un partido dura dos horas; un sitio pirata cambia de servidor en minutos.
> Hoy en Argentina eso depende de una sola fiscalía y un solo juzgado, y la orden les llega a mil proveedores de internet por las cámaras empresarias. Los chicos no llegan a tiempo, y si bloqueás una IP compartida tirás abajo la panadería y el diario del barrio."

### 2. Por qué no copiamos a Italia (0:30–0:50)
> "Italia bloquea en 30 minutos sin juez, y bloqueó sitios legítimos. Acá eso ni siquiera es legal: la Ley 27.078 dice que un proveedor solo puede bloquear con orden judicial. Así que no sacamos al juez: lo pusimos en el centro, de turno, en el celular."

### 3. Demo en vivo (0:50–2:10)
Una persona maneja el celular del juez, proyectado. Otra muestra el registro y el verificador.
1. **El pedido llega solo.** El celular vibra: "s1.pelotaya.test". Leer en voz alta las cuatro líneas: por qué es el partido (la marca de agua coincide), de dónde sale el video, qué se bloquea y hasta cuándo.
2. **La trampa de la CDN.** Mostrar el pedido de `live.golazo-libre.test`: "Esta IP la comparten 11 sitios legítimos. La plataforma no la bloquea: bloquea solo el nombre."
3. **Lo que no se bloquea.** "Canal Norte pasa el partido legalmente en su dominio, y los resúmenes son de otro partido: la plataforma los descarta sola."
4. **Firmar los N pedidos**, con un toque. Las casillas de los proveedores pasan a verde. Cumbre falla y se reintenta sola. FibraValle recibe el nombre porque no sabe bloquear por IP.
5. **Cambio de turno, minuto 50.** "Entra el juez Martín: ratifica con un toque y desde ahí todo sale con su firma."
6. **Evidencia que no se puede trucar.** Abrir el expediente y mostrar la huella SHA-256. Alterar una línea de la auditoría y correr la verificación: "Salta la alerta en la línea exacta."

### 4. Resultado (2:10–2:35)
> "Corrimos el verificador oficial del desafío. El cliente de ejemplo bloqueó 1 de 7 streams y dejó ver el partido pirata al 92 % de la gente. Nosotros: [7 de 7] streams bloqueados, visibilidad residual [X %], cero sitios legítimos afectados, cero bloqueos al licenciatario, cero IPs bloqueadas después del partido."

### 5. Quién paga y qué hace falta (2:35–2:50)
> "Lo paga quien pierde la plata: los titulares de derechos. La industria calcula entre 258 y 590 millones de dólares por año solo en Argentina, y el mismo problema está en Perú, México y Colombia. El juez y los proveedores lo usan sin costo. Para arrancar alcanza con un piloto en un partido de la liga y una resolución del ENACOM que obligue a cada proveedor a tener un canal electrónico de órdenes. Está en nuestra propuesta normativa y en `escenarios-y-modelo.md`."

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

## Antes de subir
- [ ] Números reales del verificador en la sección 4 (sin corchetes)
- [ ] Video grabado y subido a Hacki
- [ ] URL pública de Vercel funcionando desde un celular
- [ ] `entrega/` con el expediente y la auditoría del partido final, y la propuesta normativa
- [ ] Ensayado con cronómetro, dos veces
