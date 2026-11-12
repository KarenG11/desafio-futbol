# Firma en lote (corrida parcial y complementaria)

**Es una corrida parcial.** Complementa el [partido completo manual](../README.md) y prueba una sola cosa: la firma en lote desde la pantalla del juez. El partido se cortó en el minuto 10,6 a propósito, así que **no tiene resultado del verificador oficial**, porque el registro no llega al final. Sus cifras no se comparan con las de ninguna corrida completa.

## Por qué aparte

En el partido de práctica los pedidos llegan de a uno (minutos 2, 6, 9, 37…). Con firma inmediata nunca hay dos pendientes a la vez, y por eso el partido completo usó solo firma individual.

## Procedimiento

1. Simulador oficial a x10 y plataforma con `--local`, sin juez automático, en una copia limpia del repo.
2. [`lote.py`](lote.py) entra con el PIN de demo `1234`, exclusivo del modo local, y **no firma nada** hasta tener dos pedidos pendientes: P-001 (`s1.pelotaya.test`) y P-002 (`live.golazo-libre.test`).
3. Toca «Firmar los 2 pedidos como Dra. Laura Ficticia» y guarda lo que responde la API en `lote.json`.
4. Unos segundos después se copiaron el registro del simulador y los archivos de la plataforma, y se cortó la corrida.

## Archivos (originales, sin editar)

| Archivo | Lo escribió | Contenido |
|---|---|---|
| `lote.log` | `lote.py` | Salida de consola: pendientes, texto del botón, aviso de la pantalla, pedidos y órdenes |
| `lote.json` | `lote.py` | Pedidos y órdenes según la API después de firmar |
| `registro.jsonl` | Simulador oficial | Registro hasta el minuto 10,6 (incompleto a propósito) |
| `plataforma.db`, `auditoria_interna.jsonl`, `registro_publico.json` | Plataforma | Base, auditoría encadenada (26 eventos) y registro público |
| `capturas/04-lote-antes.png` | `lote.py` | Los dos pedidos pendientes y el botón de firma en lote |
| `capturas/04-lote-despues.png` | `lote.py` | Aviso «Firmaste la aprobación de 2 pedidos» y las 8 órdenes enviadas |
| `lote.py` | — | El script de la prueba |

Agregado para revisarla: [`cruce.py`](cruce.py), con su salida [`cruce.txt`](cruce.txt).

## Resultado

[`cruce.txt`](cruce.txt): **TODO OK**.
- La API y la base registran los 2 pedidos aprobados por `jueza-laura-ficticia` en el mismo minuto, el 6,22, con un solo toque.
- Salieron 8 órdenes, según lo que acepta cada proveedor:
  - P-001: IP 203.0.113.10 a Aurora, Andina y Cumbre, y dominio `s1.pelotaya.test` a FibraValle;
  - P-002: dominio `live.golazo-libre.test` a los cuatro.
- Las 8 aparecen en la auditoría como enviadas y en el registro del simulador como recibidas con `juez_de_turno: true`, con el mismo proveedor, tipo, objetivo y juez.
- Cuando se cortó la corrida, 7 de las 8 ya estaban aplicadas. Faltaba FibraValle en P-001, porque es el proveedor más lento.

## No confundir con

`../lote.txt` y `../lote.py`, junto con `../capturas/04-lote-*.png`, son de un primer intento anterior cuyo registro no se conservó. `lote.txt` se transcribió a mano. Son **referencias, no evidencia verificable**. La evidencia de la firma en lote es esta carpeta.
