# Contratos entre piezas — v0 (borrador)

> **v0 es un borrador.** Lo cierra la tarea T00 como v1. Se puede arrancar con datos de mentira que respeten estas formas.
> Cualquier cambio se avisa con un mensaje a `todos` y sube la versión.

Todo el código nuestro va en el paquete `plataforma/`. Los datos viajan como `dict` con estas claves. Los minutos son **minutos de partido** (float), como en el simulador.

## 1. Caso — lo produce `analisis/` (T01)
Un caso = un stream pirata en un servidor (host + IP). Varias detecciones del mismo host e IP son el mismo caso.
```python
{
  "caso_id": "C-001",
  "host": "s1.pelotaya.test",          # host_stream: lo que se bloquea por dominio
  "ip": "203.0.113.10",
  "asn": 64600, "organizacion": "...",
  "pagina": "https://pelotaya.test/en-vivo",
  "deteccion_ids": ["D-0001", "D-0004"],
  "primer_minuto": 2.0,
  "marca": "LP26-PRA-OFI-S048211",
  "clasificacion": "pirata",           # pirata | licenciatario_legal | otra_senal | sin_marca
  "motivo_clasificacion": "Marca oficial del partido en un dominio no autorizado",
  "dominios_en_ip": ["s1.pelotaya.test", "pelotaya.test"],
  "ip_compartida": false,
  "tipo_recomendado": "ip",            # ip | dominio
  "motivo_tipo": "La IP solo aloja dominios del mismo sitio",
}
```
Solo los casos `pirata` siguen al juez. Los demás quedan registrados en la auditoría como descartados.

## 2. Expediente — lo produce `evidencia/` (T03)
```python
{
  "expediente_id": "EXP-2026-000001",
  "caso": {...},                          # el Caso completo
  "capturas": [{"deteccion_id": "D-0001", "capturada_min": 2.0, "sha256": "..."}],
  "creado_min": 2.1,
  "hash": "sha256 del expediente sin este campo",
}
```

## 3. Pedido — lo crea el motor (T05) y lo aprueba el juez desde la web (T04)
```python
{
  "pedido_id": "P-001",
  "expediente_id": "EXP-2026-000001",
  "objetivos": [{"proveedor_id": "aurora", "tipo": "ip", "objetivo": "203.0.113.10"},
                {"proveedor_id": "valle",  "tipo": "dominio", "objetivo": "s1.pelotaya.test"}],
  "vence_min": 105,
  "estado": "pendiente",                  # pendiente | aprobado | rechazado
  "juez_id": null, "decidido_min": null, "motivo_rechazo": null,
}
```

## 4. API del motor que usa la web (T05 la sirve, T04 la consume)
| Método y ruta | Qué hace |
|---|---|
| `GET /api/estado` | Minuto, juez de turno, contadores |
| `GET /api/pedidos?estado=pendiente` | Lista de pedidos con su expediente resumido |
| `GET /api/expedientes/{id}` | Expediente completo |
| `POST /api/pedidos/aprobar` `{"pedido_ids": [...], "juez_id": "..."}` | Aprueba y firma en lote |
| `POST /api/pedidos/rechazar` `{"pedido_ids": [...], "juez_id": "...", "motivo": "..."}` | Rechaza |
| `GET /api/ordenes` | Estado de cada orden por proveedor |
| `GET /api/auditoria` | Registro de auditoría |

## 5. Orden enviada — la maneja `despacho/` (T02)
Una por proveedor y objetivo. Si falla, se reenvía con un `orden_id` nuevo y se conserva el historial.
```python
{"orden_id": "ord-P001-aurora-1", "pedido_id": "P-001", "proveedor_id": "aurora",
 "tipo": "ip", "objetivo": "203.0.113.10", "vence_min": 105,
 "estado": "aplicada", "intentos": 1, "enviada_min": 3.0, "aplicada_min": 3.4}
```

## 6. Evento de auditoría — lo escribe `evidencia/` (T03); todos lo llaman
```python
auditar(actor="motor", accion="caso_descartado", datos={...})
# se guarda como una línea JSONL:
{"seq": 12, "min": 3.2, "ts": "2026-11-13T18:03:12-03:00", "actor": "juez:jueza-laura-ficticia",
 "accion": "pedido_aprobado", "datos": {...}, "hash_prev": "...", "hash": "..."}
```
`hash = sha256(hash_prev + json canónico del evento sin "hash")`. Si se toca una línea, se rompe la cadena desde ahí.
