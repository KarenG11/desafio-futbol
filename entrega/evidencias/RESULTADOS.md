# Resultados de la corrida definitiva

**Cómo se hizo:**
- Se copió el repo limpio (archivos versionados y nuevos, sin `salida/` ni caches) a otro directorio, con un entorno virtual nuevo instalado desde `requirements.txt`. Python 3.10.12, Linux.
- Se corrieron los 4 escenarios en paralelo con `plataforma/pruebas/partido_completo.py`: simulador oficial a x20, motor con `--juez-automatico` (solo pruebas) y `evaluacion/verificar.py` oficial sin modificar.
- Cada corrida empieza de cero: base SQLite y auditoría nuevas, y el `registro.jsonl` lo escribe el simulador.
- Se volvió a generar el escenario de reclamos con `generar_reclamos.py` y es idéntico byte a byte al versionado.

**Correspondencia con el código:**
- El código de la corrida es el de este árbol de trabajo (rama `devin/motor-despacho-entrega`).
- La única diferencia posterior es que `plataforma/motor/exportar.py` ganó una función `main()` para verificar los archivos por línea de comandos. Esa función no la usa el motor.
- `simulador/`, `evaluacion/`, `datos/` y `ejemplos/` son idénticos al commit `3dd19fa`.

Cada carpeta tiene `verificar.txt`/`verificar.json` (salida del verificador), `registro.jsonl` (del simulador), `publico.json` (lo que devuelve `/api/publico`) y `resumen.json` (chequeos del runner).

| Métrica del verificador | [Cliente de ejemplo](cliente-ejemplo/verificar.txt) | [Práctica](practica/verificar.txt) | [Hosting compartido](reclamos/verificar.txt) | [Cambio de turno](turno/verificar.txt) (`--inicio-min 40`) | [DNS desactualizado](reclamo-forzado/verificar.txt) (**falla inyectada**) |
|---|---|---|---|---|---|
| Fases piratas bloqueadas | 1 de 7 | **7 de 7** | **7 de 7** | 6 de 7 (la fase 1 terminó en el min 36, antes de arrancar) | 7 de 7 |
| Visibilidad residual promedio | 86,5 % | **3,1 %** | **3,1 %** | 27,6 % (cuenta los minutos previos al arranque) | 3,1 % |
| Primer bloqueo de cada fase (min de partido desde el inicio de la fase) | — | 0,48 a 0,68 | 0,42 a 0,65 | 0,43 a 3,41 en las fases que empezaron después del arranque | 0,46 a 0,72 |
| Órdenes recibidas / aplicadas / fallidas | 3 / 3 / 0 | 32 / 28 / 4 | 34 / 28 / 6 | 32 / 28 / 4 | 35 / 31 / 4 |
| Órdenes rechazadas | 1 | 0 | 0 | 0 | 0 |
| Bloqueos con daño colateral | 0 | **0** | **0** | **0** | 3 (deliberado) |
| Dominios legítimos afectados | 0 | **0** | **0** | **0** | 2 |
| Falsos positivos | 0 | **0** | **0** | **0** | 0 |
| IP activas después del partido (min 110) | 0 | **0** | **0** | **0** | 0 |
| Reclamos / resueltos por levantamiento | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1 / 1 |
| Órdenes firmadas fuera de turno | 0 | **0** | **0** | **0** | 0 |
| Chequeos del runner | — | todos OK | todos OK | todos OK | todos OK |

## Criterios de aceptación
Los cinco: 7 de 7 fases, y 0 en daño colateral, falsos positivos, órdenes fuera de turno e IP post partido.
- **Práctica** y **hosting compartido** cumplen los cinco.
- **Cambio de turno** cumple cuatro. La fase 1 ya había terminado cuando arrancó la corrida y no se puede bloquear, así que llega a 6 de 7. El cambio de turno del minuto 50 se ratificó y no hubo órdenes fuera de turno.
- **DNS desactualizado** no es una corrida de aceptación. Inyecta a propósito un DNS falso para que la plataforma bloquee una IP compartida y el simulador emita un reclamo real:
  - el reclamo llegó en el minuto 13,46 y se resolvió en 0,13 minutos de partido;
  - las órdenes por IP estuvieron activas 4,13 min (Aurora), 3,10 min (Andina) y 1,19 min (Cumbre);
  - todas se levantaron con firma y se reemplazaron por el dominio. El daño colateral es el que informa el verificador, sin ocultar nada.

**Reintentos:** Cumbre (tasa de falla 0,35 en `datos/proveedores.json`) falló 4 veces en la práctica. Las 4 se reenviaron con un `orden_id` nuevo (4 `orden_reenviada` en la auditoría) y quedaron aplicadas.

**Vencimiento y levantamiento:**
- Todas las órdenes vencen en el minuto 105. Las cinco corridas terminan con 0 IP activas en el minuto 110.
- El levantamiento firmado de IP se ejercitó en el reclamo forzado y en `test_despacho` contra el simulador.

**Pruebas con asserts:** [`unitarias.txt`](unitarias.txt) da 6 de 6 módulos OK. El cerebro pasa 17 de 17 pruebas.

## Entregables de esta corrida (práctica)
| Archivo | Verificación | SHA-256 del archivo |
|---|---|---|
| [`../expediente-final.json`](../expediente-final.json) | hash del expediente `6dcf6e53…` recalculado y coincide. El hash figura en la auditoría | `493e0433699dc974ddc60fd408be21c8a31c6b0bca6fbd1ea926f31cb38c81bd` |
| [`../auditoria-final.jsonl`](../auditoria-final.jsonl) | 160 eventos con la cadena íntegra. Si se altera un evento, el chequeo falla con `cadena de auditoría rota en seq 41` | `c1804d78f183ec55bd6e56c7e4460ce33d6e535226a6cb37b9c20d540d2b09c1` |
| [`../registro.jsonl`](../registro.jsonl) | registro del simulador. Volver a correr `evaluacion/verificar.py --log entrega/registro.jsonl` da exactamente [`practica/verificar.txt`](practica/verificar.txt) | `fb1c36d58ed2049470675c909a72f97e391ad0a1e809b9446490231d45ce3422` |

Para verificarlo: `python -m plataforma.motor.exportar entrega/auditoria-final.jsonl entrega/expediente-final.json`.

**Verificación cruzada orden por orden** (registro del simulador, auditoría, base de la plataforma y verificador): [`verificacion/practica.txt`](verificacion/practica.txt), generado con:
```bash
python entrega/evidencias/verificacion/verificar_corrida.py --corrida entrega/evidencias/practica \
    --auditoria entrega/auditoria-final.jsonl --expediente entrega/expediente-final.json --db entrega/evidencias/practica/plataforma.db
```
Las 4 fallidas son de Cumbre y corresponden a 3 pedidos (P-001, P-004 y P-007; P-007 falló dos veces seguidas). Todas se reenviaron con un `orden_id` nuevo en ~0,1 min y la última de cada cadena quedó aplicada y vencida en el minuto 105. Las 28 aplicadas tienen recepción con juez de turno, aplicación, vencimiento en el 105, el mismo minuto en el registro, la auditoría y la base, y una sola orden aplicada por objetivo y proveedor.

Son del **partido de práctica**. Si se corre el partido final, hay que regenerarlos con `--exportar entrega`.

## Corridas anteriores (conservadas)
- [`v2/`](v2/RESULTADOS.md): primera corrida después del fix de IP compartida. Mismos criterios, con 2,9 % de visibilidad residual en la práctica. La diferencia con la definitiva es variación entre corridas, por cuándo cae cada detección respecto de los envíos.
- [`v1/`](v1/RESULTADOS.md): antes del fix, el escenario de hosting compartido tuvo daño colateral.
