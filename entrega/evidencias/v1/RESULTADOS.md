# Corridas v1 (antes de corregir la detección de IP compartida) — SUPERADAS

> Se conservan como evidencia histórica. En la corrida de reclamos la plataforma bloqueó por IP un hosting compartido (3 órdenes con daño colateral). Los resultados vigentes están en [`../RESULTADOS.md`](../RESULTADOS.md). El expediente y la auditoría de `entrega/` ya son de la corrida v2.

Salidas sin editar de `evaluacion/verificar.py` (oficial) sobre el `registro.jsonl` que escribe el **simulador oficial**. Corridas del 11/11/2026 con Python 3.10.12, simulador x20 y `--juez-automatico` (modo de prueba: el juez de turno aprueba, ratifica y resuelve reclamos solo). Cada carpeta tiene `verificar.txt`, `verificar.json`, `registro.jsonl`, `publico.json` y `resumen.json` (chequeos de `plataforma/pruebas/partido_completo.py`).

| Métrica del verificador | [Cliente de ejemplo](../cliente-ejemplo/verificar.txt) | [Práctica](practica/verificar.txt) | [Cambio de turno](turno/verificar.txt) (`--inicio-min 40`) | [Reclamos](reclamos/verificar.txt) (escenario de prueba) |
|---|---|---|---|---|
| Fases piratas bloqueadas | 1 de 7 | **7 de 7** | 6 de 7 (la fase 1 terminó en el min 36, antes de arrancar) | **7 de 7** |
| Visibilidad residual promedio | 86,5 % | **3,0 %** | 27,9 % (cuenta minutos previos al arranque) | 3,1 % |
| Órdenes recibidas / aplicadas / fallidas | 3 / 3 / 0 | 29 / 28 / 1 | 31 / 28 / 3 | 35 / 31 / 4 |
| Órdenes rechazadas por el proveedor | 1 (FibraValle: no bloquea por IP) | 0 | 0 | 0 |
| Bloqueos con daño colateral | 0 | **0** | 0 | 3 (ver abajo) |
| Falsos positivos | 0 | 0 | 0 | 0 |
| IP activas después del partido (min 110) | 0 | **0** | 0 | 0 |
| Reclamos / resueltos por levantamiento | 0 / 0 | 0 / 0 | 0 / 0 | **1 / 1** |
| Órdenes firmadas fuera de turno | 0 | **0** | 0 | 0 |

**Práctica:** el primer bloqueo de cada fase llegó entre 0,42 y 0,65 minutos de partido después de que empezó la fase (verificador, `primer_bloqueo_min`). El cliente de ejemplo se corrió igual (x20) con `ejemplos/cliente_minimo.py`: manda una sola orden por IP y termina.

**Fallas de proveedor:** todas las `orden_fallida` (Cumbre) se reenviaron con un `orden_id` nuevo (`-2`, `-3`…) y quedaron aplicadas (`orden_reenviada` en la auditoría; chequeo `fallidas_reintentadas`).

**Cambio de turno:** en el min 50 el motor detiene los envíos, el juez entrante ratifica las órdenes vigentes (`cambio_de_turno` y `turno_asumido` en la auditoría) y desde ahí firma él. El verificador dio 0 órdenes fuera de turno en las tres corridas.

**Reclamos:** en el escenario de prueba (`plataforma/pruebas/escenarios/`) el stream de verpartido está en un hosting compartido cuyos dominios comparten sufijo. La heurística `sitio_de()` los toma como un solo sitio y bloquea la IP. Es una **limitación real** que la prueba deja a la vista. A los 4 minutos llega el reclamo de la panadería (min 13,67). La plataforma lo correlaciona con la orden activa y levanta con firma la IP en los 3 proveedores que la tenían. Los 3 confirmaron en 0,07 minutos de partido. Después reemplaza el bloqueo por el dominio pirata. Las 3 órdenes IP estuvieron activas 4,07, 2,33 y 1,33 minutos: ese es el daño colateral que cuenta el verificador.

**Pruebas con asserts:** [`unitarias.txt`](unitarias.txt): 6 de 6 módulos OK.

**Expediente y auditoría exportados** (corrida de práctica): expediente y auditoría de la práctica v1 (ya reemplazados en `entrega/`): 154 eventos con la cadena de hashes verificada. No son del partido final: hay que regenerarlos con `--exportar entrega` en esa corrida.
