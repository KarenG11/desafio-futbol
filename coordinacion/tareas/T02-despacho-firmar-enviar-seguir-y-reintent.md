---
id: T02
titulo: Despacho: firmar, enviar, seguir y reintentar
carpeta: plataforma/despacho/
estado: hecha
dueno: alejo
desde: 2026-11-11 16:32
creada_por: alejo
depende_de: T00
---
## Qué hay que hacer
- Firmar con HMAC (clave del juez en datos/juzgados.json): orden_id|tipo|objetivo|vence_min|juez_id.
- Por cada proveedor, mandar el tipo que acepta (FibraValle solo dominio).
- Seguir el estado de cada orden; si queda fallida, reenviar con orden_id nuevo.
- Bloqueos por IP: vence_min = fin del partido (entero).
- Ojo: el turno se valida cuando la orden LLEGA. Cerca del cambio de turno, firmar con el juez entrante.

## Terminada cuando
Todas las órdenes aprobadas quedan aplicadas en todos los proveedores, sin rechazos ni firmas fuera de turno en el verificador.
