---
id: T06
titulo: Reclamos: verificar, levantar con firma y reemplazar
carpeta: plataforma/reclamos/
estado: en-curso
dueno: rocio
desde: 2026-11-11 15:25
creada_por: alejo
depende_de: T02, T05
---
## Qué hay que hacer (extra)
- Leer GET /reclamos. Verificar que el dominio reclamante no es pirata y está detrás de una orden nuestra.
- Pedir al juez levantar (firma LEVANTAR|orden_id|juez_id) y reemplazar por bloqueo por dominio del host pirata.

## Terminada cuando
El verificador muestra los reclamos resueltos por levantamiento.
