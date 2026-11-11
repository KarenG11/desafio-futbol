---
de: alejo
para: todos
fecha: 2026-11-11 14:13
asunto: Contratos v1.3: tablas partidos, solicitudes y verificaciones
requiere_respuesta: no
---
Cambio aditivo en contratos.md §10 (no cambia ninguna forma existente).
- partidos: el motor escribe ahí el estado vivo en cada ciclo; la web lo lee para /api/estado y para validar el turno del juez.
- solicitudes: la web deja ahí asumir turno y levantar por reclamo; el motor las resuelve.
- verificaciones: salida de evaluacion/verificar.py de los partidos de demo (T12).
- pedidos suma la columna despachado.
El SQL completo y las funciones de plataforma/db/ que van a usar todos están en coordinacion/guias/T11-base-y-vercel.md (pasos 5 y 6).
Motor (T05), evidencia (T03) y Sandbox (T12): usen esas funciones; no escriban SQL propio.
