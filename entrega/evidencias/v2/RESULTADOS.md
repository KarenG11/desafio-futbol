# Corridas v2 — superadas por la corrida definitiva

> Se conservan como evidencia. Los resultados vigentes están en [`../RESULTADOS.md`](../RESULTADOS.md).

Corridas v2: hechas el 11/11/2026, después de corregir la detección de IP compartida. Las salidas de `evaluacion/verificar.py` (oficial, sin modificar) están sin editar y se calcularon sobre el `registro.jsonl` que escribe el **simulador oficial**. Condiciones: Python 3.10.12, simulador x20 y `--juez-automatico` (modo de prueba). Cada carpeta tiene `verificar.txt`, `verificar.json`, `registro.jsonl`, `publico.json` y `resumen.json`, con los chequeos de `plataforma/pruebas/partido_completo.py`. Las corridas v1 (anteriores al fix) se conservan en [`v1/`](../v1/RESULTADOS.md).

| Métrica del verificador | [Cliente de ejemplo](../cliente-ejemplo/verificar.txt) | [Práctica](practica/verificar.txt) | [Cambio de turno](turno/verificar.txt) (`--inicio-min 40`) | [Reclamos: hosting compartido](reclamos/verificar.txt) | [Reclamo forzado](reclamo-forzado/verificar.txt) (falla inyectada) |
|---|---|---|---|---|---|
| Fases piratas bloqueadas | 1 de 7 | **7 de 7** | 6 de 7 (la fase 1 terminó en el min 36, antes de arrancar) | **7 de 7** | 7 de 7 |
| Visibilidad residual promedio | 86,5 % | **2,9 %** | 27,6 % (cuenta minutos previos al arranque) | **3,1 %** | 3,1 % |
| Órdenes recibidas / aplicadas / fallidas | 3 / 3 / 0 | 38 / 28 / 10 | 30 / 28 / 2 | 31 / 28 / 3 | 32 / 30 / 1 |
| Órdenes rechazadas por el proveedor | 1 | 0 | 0 | 0 | 0 |
| Bloqueos con daño colateral | 0 | **0** | **0** | **0** | 2 (deliberado, ver abajo) |
| Dominios legítimos afectados | 0 | **0** | **0** | **0** | 2 |
| Falsos positivos | 0 | **0** | **0** | **0** | 0 |
| IP activas después del partido (min 110) | 0 | **0** | **0** | **0** | 0 |
| Reclamos / resueltos por levantamiento | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | **1 / 1** |
| Órdenes firmadas fuera de turno | 0 | **0** | **0** | **0** | 0 |

**Criterio de aceptación** (7 de 7 fases, y 0 en daño colateral, falsos positivos, órdenes fuera de turno e IP post partido): lo cumplen la **práctica** y **reclamos: hosting compartido**.
- **Cambio de turno:** cumple todo menos las 7 fases. El simulador arranca en el minuto 40 y la fase 1 ya había terminado: no se puede bloquear. Las 6 fases que estaban en juego se bloquearon.

**Qué se corrigió.** Antes, si todos los dominios de una IP compartían sufijo, la plataforma bloqueaba la IP. Ahora `Cerebro._riesgo_colateral` exige que se cumplan todas estas señales; si una falla o falta, va por dominio:
1. hay datos de DNS pasivo;
2. todos los dominios son del mismo sitio;
3. el titular del ASN es conocido y no es hosting compartido, CDN ni nube;
4. el ASN de la detección coincide con el del DNS;
5. ningún dominio de la IP es de un licenciatario ni de un caso no pirata;
6. la IP no tuvo reclamos verificados.

En el escenario de hosting compartido, la IP 192.0.2.50 es de "Pampa Web Hosting Compartido". Antes se bloqueaba por IP (v1: 3 órdenes con colateral). Ahora la plataforma bloquea solo `tv.verpartido.hostcomun.test`: 0 colateral, la fase igual quedó bloqueada (0,53 min, 1,1 % residual) y no hubo reclamos.

**Práctica:** el primer bloqueo de cada fase llegó entre 0,44 y 0,63 minutos de partido después del inicio de la fase. En esta corrida Cumbre falló 10 veces. Las 10 se reenviaron con un `orden_id` nuevo (10 `orden_reenviada` en la auditoría) y todas quedaron aplicadas.

**Reclamo forzado** (`--falla dns-desactualizado`, solo pruebas): no es una corrida de aceptación. Le hacemos creer al cerebro que el DNS pasivo de 192.0.2.50 solo tiene el dominio pirata y un ASN dedicado, para que bloquee la IP por error y probar el circuito de reclamos real del simulador:
- llega el reclamo de la panadería (min 13,51);
- la plataforma lo verifica con un DNS consultado de nuevo;
- levanta con firma la IP en los proveedores que la tenían;
- reemplaza el bloqueo por el dominio;
- marca la IP como compartida.

El reclamo se resolvió en 0,07 minutos de partido. Las 2 órdenes IP estuvieron activas 4,07 min (Aurora) y 3,08 min (Andina): es el daño colateral que informa el verificador, sin ocultarlo.

**Vencimiento y levantamiento de IP:** en las cinco corridas quedaron 0 IP activas en el minuto 110. `plataforma/despacho/test_despacho.py` levanta una orden IP real contra el simulador y comprueba la confirmación.

**Pruebas con asserts:** [`unitarias.txt`](unitarias.txt): 6 de 6 módulos OK. El cerebro pasa 17 de 17 pruebas, con 4 nuevas de IP compartida.

**Expediente y auditoría** (práctica v2):
- expediente de la práctica v2 (reemplazado en `entrega/` por el de la corrida definitiva).
- auditoría de la práctica v2: 172 eventos, con la cadena de hashes verificada.

No son del partido final: hay que regenerarlos con `--exportar entrega` en esa corrida.
