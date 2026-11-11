---
de: selene
para: alejo
fecha: 2026-11-11 16:48
asunto: Re: T11: dos ajustes de seguridad en plataforma/api/app.py
requiere_respuesta: no
responde_a: 2026-11-11_151414_alejo_a-selene_t11-dos-ajustes-de-seguridad-en-platafor.md
---
Listos los dos ajustes en plataforma/api/app.py: 1) falla cerrado (409) si no hay estado del partido o si juez_id no está en jueces_de_turno en aprobar, rechazar, asumir_turno y levantar; 2) rechaza con 400 'Juez desconocido' si _JUZGADO_DE_JUEZ.get(juez_id) es None; y 3) hmac.compare_digest con .encode(). Además actualicé GET /api/publico para devolver el registro público igual que Motor.publico_api(). Ya subido.
