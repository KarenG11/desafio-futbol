# Demo manual de la pantalla del juez

Esta carpeta tiene dos pruebas independientes de la pantalla del juez. En las dos se firmó a mano, sin `--juez-automatico`:

| Prueba | Carpeta | Tipo | Qué demuestra |
|---|---|---|---|
| **Partido completo manual** | `demo-manual/` (esta) | Corrida completa, minuto 0 a 110, con verificador oficial | Todo el circuito operado desde la pantalla: expediente, firma, estados, reintentos, cambio de turno, vencimiento y registro público |
| **Firma en lote** | [`lote/`](lote/README.md) | Corrida **parcial y complementaria**, minuto 0 a 10,6 | El botón «Firmar los N pedidos» con dos pedidos pendientes a la vez |

Las dos son independientes de las corridas automáticas de `evidencias/` (`practica/`, `turno/`, `reclamos/`, `reclamo-forzado/`, `v1/`, `v2/`), que no se tocaron.

## Objetivo

Comprobar desde un navegador, como lo usaría un juez, que la plataforma cumple el circuito completo contra el simulador oficial. Esto no reemplaza a las corridas automáticas: en ellas el juez lo simula el código.

## Procedimiento

1. Se levantó el simulador oficial (`simulador/servidor.py --acelerar 10`) y la plataforma (`python -m plataforma.main --sim … --local`), **sin juez automático**. Las dos corrieron en una copia del repo, para que su carpeta `salida/` no escribiera sobre las evidencias.
2. [`recorrido.py`](recorrido.py) maneja Chrome con Playwright, con una pantalla de celular de 430x900. Se conecta por CDP y hace lo mismo que haría una persona:
   - entra con el PIN;
   - en cada pedido nuevo abre «Ver expediente» y espera a que cargue;
   - toca «Firmar» en cada pedido, de a uno, porque en el partido de práctica llegan separados.
3. En el minuto 50 el script intenta aprobar con la jueza saliente (`jueza-laura-ficticia`) llamando directamente a la API. Así se prueba que el control no depende de la pantalla. Después toca «Asumir turno» en la pantalla, como el juez entrante (`juez-martin-ejemplo`).
4. Cada segundo, el script anota en [`recorrido.log`](recorrido.log) los cambios de estado de las órdenes y del registro público (`/api/publico`).
5. Con el partido terminado se guardó [`final.json`](final.json) desde la API. Cuando el simulador pasó el minuto 110, se corrió `evaluacion/verificar.py`, sin modificar, sobre el registro.

## Archivos

Originales, tal como los escribieron el simulador, la plataforma y el script, sin editar:

| Archivo | Lo escribió | Contenido |
|---|---|---|
| `registro.jsonl` | Simulador oficial | Registro de eventos del partido hasta el minuto 110 (lo que lee el verificador) |
| `verificar.txt` | `evaluacion/verificar.py` | Resultado oficial sobre `registro.jsonl` |
| `plataforma/plataforma.db` | Plataforma | Base SQLite: casos, expedientes, pedidos, órdenes y auditoría |
| `plataforma/auditoria_interna.jsonl` | Plataforma | Auditoría encadenada por hashes (155 eventos) |
| `plataforma/registro_publico.json` | Plataforma | Registro público al final del partido |
| `recorrido.log` | `recorrido.py` | Bitácora minuto a minuto: pedidos, expediente leído en pantalla, firmas, estados de las órdenes, registro público |
| `final.json` | `recorrido.py` | Pedidos, órdenes y registro público según la API al terminar |
| `capturas/01…08` | `recorrido.py` | Capturas de pantalla (ver tabla abajo) |
| `recorrido.py` | — | El script que hizo la prueba |

Agregados después para revisar la prueba (no son resultados de la corrida):

| Archivo | Contenido |
|---|---|
| `verificar_demo.py` | Verificación de solo lectura de las dos pruebas (ver abajo) |
| `verificacion.txt` | Su salida: **TODO OK** |
| `SHA256SUMS` | Hashes de todos los archivos originales de las dos pruebas (`sha256sum -c SHA256SUMS` desde esta carpeta) |

**Referencias de una prueba anterior, no son evidencia verificable:** `lote.txt`, `lote.py`, `capturas/04-lote-antes.png` y `capturas/04-lote-despues.png` son de un primer intento de firma en lote cuyo registro del simulador no se conservó. Además, `lote.txt` se transcribió a mano desde la consola. Se conservan como referencia, pero no se pueden contrastar con ningún registro. La prueba de lote verificable está en [`lote/`](lote/README.md).

## Capturas

| Captura | Minuto | Paso |
|---|---|---|
| `01-ingreso.png` | 0 | Pantalla de ingreso con PIN, antes de que el motor publique el estado |
| `02-expediente-pelotaya.png` | 2 | Pedido P-001 con «Ver expediente» abierto: `s1.pelotaya.test`, IP 203.0.113.10, Bruma Hosting Dedicado (ASN 64600), marca de agua, licenciatarios, justificación del bloqueo por IP y qué recibe cada proveedor (FibraValle, el dominio) |
| `02-expediente-golazo-libre.png` | 6 | Pedido P-002 con el expediente abierto: `live.golazo-libre.test` en NubeRápida CDN, con los 11 sitios de terceros listados. Se bloquea solo el dominio en los 4 proveedores |
| `03-firma-1.png` | 2 | Después de firmar P-001: las 4 órdenes en «Recibida, aplicando» |
| `03-firma-2.png` | 6 | Después de firmar P-002: P-001 ya «Bloqueado» en Andina, Aurora y Cumbre (FibraValle todavía aplicando), y P-002 recibida |
| `05-cambio-turno.png` | 50,14 | Pantalla justo después del intento de la jueza saliente (el 409 fue por API y queda en `recorrido.log`). La cabecera ya muestra al Dr. Martín Ejemplo de turno; abajo se ven las órdenes vigentes, incluido el «intento 4» de Cumbre |
| `06-turno-asumido.png` | 50,98 | «Turno asumido por Dr. Martín Ejemplo. Ratificaste 16 órdenes vigentes» |
| `07-final.png` | 105 | Partido terminado: todas las casillas en «Venció», con el número de intento cuando Cumbre necesitó reenvíos |
| `08-publico.png` | 105 | `/api/publico` en el navegador (JSON crudo): cada entrada con juez, juzgado, minuto de la orden, estado y minuto de aplicación por proveedor, y vencimiento |

En `02-expediente-*` y `07-final` la barra fija de firma o la cabecera aparecen superpuestas en el medio. Es un efecto de capturar la página entera con elementos fijos; no se ve así en el celular.

## Resultados

Verificador oficial ([`verificar.txt`](verificar.txt)):

| Métrica | Resultado |
|---|---|
| Fases piratas bloqueadas | **7 de 7** |
| Visibilidad residual promedio | **4,0 %** |
| Bloqueos con daño colateral / dominios legítimos afectados | **0 / 0** |
| Falsos positivos | **0** |
| Bloqueos IP activos después del partido | **0** |
| Órdenes firmadas fuera de turno | **0** |
| Órdenes recibidas / aplicadas / fallidas / rechazadas | 33 / 28 / 5 / 0 |

- Firmas: 7 pedidos, todos con firma individual desde la pantalla. P-001 a P-004 los firmó la Dra. Laura Ficticia; P-005 a P-007, el Dr. Martín Ejemplo, después de asumir.
- Cambio de turno: en el minuto 50,14 la API rechazó a la jueza saliente con `409` («jueza-laura-ficticia no está de turno en el minuto 50.14»). En el 50,98 el juez entrante asumió desde la pantalla y ratificó 16 órdenes.
- Reintentos: las 5 fallas son de Cumbre (3 en P-003 y 2 en P-007). Cada una se reenvió con un `orden_id` nuevo. Queda una sola orden no fallida por pedido y proveedor (28 combinaciones), así que no hubo bloqueos duplicados.
- Vencimiento: las 28 órdenes aplicadas vencieron en el minuto 105. En el minuto 110 el simulador no tiene órdenes activas.

### Por qué 4,0 % y no 3,1 %

La corrida automática de referencia ([`../practica/`](../practica/verificar.txt)) dio 3,1 %, con el mismo código de motor y el mismo partido. La diferencia está en el tiempo hasta el primer bloqueo de cada fase:
- en la automática fue de 0,5 a 0,7 minutos de partido;
- en la manual, de 0,8 a 1,0.

Ese tiempo extra es la intervención humana: el pedido tiene que aparecer en la pantalla (que se refresca cada 2 segundos), la persona lo lee y toca «Firmar». En el log, la firma llegó entre 0 y 0,09 minutos después de que el script vio el pedido.

A x10, cada segundo real equivale a 0,17 minutos de partido, así que a velocidad real esa demora pesaría menos. Esto último es una inferencia: no se midió.

## PIN de demostración

El PIN `1234` es **exclusivo del modo local de demostración**:
- existe solo si la plataforma se inicia con `--local` y no hay variable `JUEZ_PIN`;
- sin `--local` y sin `JUEZ_PIN`, la API rechaza todas las decisiones;
- después de 5 intentos fallidos por minuto, responde `429`.

No es una credencial real. Tampoco aparecen en esta carpeta las claves HMAC: son las ficticias de `datos/juzgados.json` y no quedan ni en la base ni en la auditoría.

## Cómo verificar

Desde la raíz del repo:

```bash
python entrega/evidencias/demo-manual/verificar_demo.py
cd entrega/evidencias/demo-manual && sha256sum -c SHA256SUMS
```

`verificar_demo.py` no escribe nada. Comprueba:
- la cadena de la auditoría, y que la base tenga la misma auditoría;
- el hash de cada expediente, contra el guardado y contra el de la auditoría;
- que la API, la auditoría y el registro del simulador tengan las mismas órdenes, con el mismo objetivo, juez y estado final;
- que no haya bloqueos duplicados;
- el 409 y la asunción del turno en el log;
- que el verificador oficial, corrido de nuevo, dé exactamente `verificar.txt`;
- que el cruce de la firma en lote siga dando lo mismo.

## Cómo repetirla

Siguiendo `entrega/README.md`, punto 5: simulador con `--acelerar 3` (o 10), plataforma con `--local` y PIN `1234` en http://localhost:8000/juez/.

Para repetirla con el script hace falta Playwright y un Chrome con CDP en `localhost:29229`. `recorrido.py` usa los puertos 8001 y 8081 y guarda las capturas fuera del repo.
