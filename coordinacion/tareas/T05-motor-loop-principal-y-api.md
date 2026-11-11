---
id: T05
titulo: Motor: loop principal y API
carpeta: plataforma/motor/, plataforma/main.py
estado: libre
dueno: 
desde: 
creada_por: alejo
depende_de: T00, T01, T02, T03
---
## Qué hay que hacer
- Loop que lee detecciones y reclamos del simulador, llama al cerebro, a evidencia y crea pedidos.
- API de contratos.md punto 4 para la web.
- Al aprobar, pasa el pedido a despacho.
- Modo --juez-automatico solo para pruebas aceleradas.
- Un solo comando: python -m plataforma.main --sim http://localhost:8080

## Terminada cuando
Un partido de práctica completo corre de punta a punta con el juez automático.
