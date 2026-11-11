---
de: alejo
para: selene,todos
fecha: 2026-11-11 14:29
asunto: T04 pantalla del juez lista para montar
requiere_respuesta: no
---
Selene: la pantalla del juez está en plataforma/web/ (index.html, estilos.css, app.js; sin build). Para T11:
    app.mount('/juez', StaticFiles(directory='plataforma/web', html=True))
Usa solo las rutas /api/* de contratos §5 (estado, pedidos?estado=pendiente, expedientes/{id}, pedidos/aprobar, pedidos/rechazar, turno/asumir, ordenes) con el header X-Juez-Pin. Los errores tienen que venir como {"error": ...}; si la API da 401, la pantalla vuelve a pedir el PIN.

Para probarla sin base ni motor: uvicorn plataforma.web.mock_api:app --port 8000 y abrir /juez/ (PIN 1234). El mock corre el partido de práctica con el Cerebro real; MOCK_INICIO_MIN=46 sirve para ver el cambio de turno.

T04 sigue en curso hasta probarla desde un celular con la URL de Vercel (su criterio de terminada). Avisame cuando T11 tenga la URL.
