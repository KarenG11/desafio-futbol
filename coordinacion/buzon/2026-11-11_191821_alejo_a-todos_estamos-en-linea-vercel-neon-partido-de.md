---
de: alejo
para: todos
fecha: 2026-11-11 19:18
asunto: Estamos en línea: Vercel + Neon + partido de demo online
requiere_respuesta: no
---
La plataforma está publicada: https://desafio-futbol-iota.vercel.app
- Pantalla del juez: /juez/ (pide PIN; el PIN lo tiene Alejo, se pasa por privado).
- Partido de práctica en vivo: /juez/demo.html. Un botón prende un Vercel Sandbox con el simulador y el motor; al terminar muestra el verificador.
- Base Postgres en Neon (São Paulo).

Resultado del partido 100 % online (x30, juez automático): 7 de 7, 3,8 % de visibilidad residual, 0 rechazos, 0 colateral, 0 fuera de turno. Evidencia en entrega/validacion/.

Arreglos importantes para el viernes:
- El motor con --base reusa la conexión a la base (antes cada consulta tardaba 0,8 s y a x30 llegaba tarde).
- El despacho no manda órdenes ya vencidas (cada rechazo resta).

T10 y T12 hechas. Lo que queda: video, pitch y preguntarle a la organización si el simulador del final se alcanza desde internet.
