---
id: T01
titulo: Cerebro: clasificar detecciones y armar casos
carpeta: plataforma/analisis/
estado: libre
dueno: 
desde: 
creada_por: alejo
depende_de: T00
---
## Qué hay que hacer
- Agrupar detecciones repetidas en casos (host + IP).
- Clasificar con la marca de agua contra GET /partido: pirata, licenciatario_legal (marca LIC en su dominio autorizado), otra_senal, sin_marca. Marca LIC fuera de sus dominios = pirata.
- Consultar DNS pasivo: si la IP aloja dominios de otros sitios es compartida y el tipo recomendado es dominio.
- Detectar mudanzas: mismo sitio en otro host o IP es un caso nuevo.

## Terminada cuando
Con escenario_practica.json da exactamente los 7 casos piratas del verificador, sin el licenciatario ni las señales ajenas.
