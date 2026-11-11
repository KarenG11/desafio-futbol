---
id: T05
titulo: Motor: loop principal y API
carpeta: plataforma/motor/, plataforma/main.py
estado: libre
dueno: 
desde: 
creada_por: alejo
depende_de: T00, T01, T02, T03, T11
---
## Qué hay que hacer
- Loop que lee detecciones y reclamos del simulador, llama al cerebro, a evidencia y crea pedidos.
- Guarda todo en la base (plataforma/db/, T11) y es el único que escribe la auditoría.
- Cada ~1 s toma de la base los pedidos que el juez aprobó en la web (Vercel) y los pasa a despacho. La API la sirve T11 (decisiones 15 a 21).
- Modo --local: motor + web en un proceso con SQLite (plan B si se cae internet).
- Modo --juez-automatico solo para pruebas aceleradas.
- Comandos: python -m plataforma.motor --sim http://localhost:8080 (con DATABASE_URL) y python -m plataforma.main --sim http://localhost:8080 --local

## Terminada cuando
Un partido de práctica completo corre de punta a punta con el juez automático.
