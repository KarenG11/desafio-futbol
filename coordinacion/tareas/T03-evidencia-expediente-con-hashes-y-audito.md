---
id: T03
titulo: Evidencia: expediente con hashes y auditoría encadenada
carpeta: plataforma/evidencia/
estado: libre
dueno: 
desde: 
creada_por: alejo
depende_de: T00
---
## Qué hay que hacer
- Armar el expediente de cada caso: marca verificada, servidor (host, IP, ASN), sitios en la misma IP, SHA-256 de cada captura (contenido_b64 decodificado), sellos de tiempo.
- Hash del expediente completo.
- Auditoría append-only en JSONL con cadena de hashes (ver contratos.md punto 6) y un verificador que detecte alteraciones.
- Exportar a entrega/ un expediente y la auditoría del partido.

## Terminada cuando
Si se modifica un byte de una línea de auditoría o de un expediente, el verificador lo detecta y dice dónde.
