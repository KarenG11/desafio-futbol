# Validación con el verificador oficial (T10)

Corridas del 2026-11-11 contra el simulador de práctica, con `evaluacion/verificar.py` sin modificar y con el juez automático (solo para pruebas).

| Corrida | Archivo | Fases bloqueadas | Visibilidad residual | Colateral | Falsos positivos | Rechazos | Fuera de turno | IP después del partido |
|---|---|---|---|---|---|---|---|---|
| Partido completo, x10 | `partido-completo-x10.txt` | 7 de 7 | 2,9 % | 0 | 0 | 0 | 0 | 0 |
| **Online: Vercel Sandbox + Neon, x30** | `online-vercel-sandbox-x30.txt` | 7 de 7 | 3,8 % | 0 | 0 | 0 | 0 | 0 |
| Arranca en el minuto 40, x30 (cambio de turno en el 50) | `cambio-de-turno-min40-x30.txt` | 6 de 7 | 29,6 % | 0 | 0 | 0 | 0 | 0 |

## Qué prueba cada una

- **Partido completo:** todos los streams piratas quedan bloqueados entre 0,4 y 0,6 minutos de partido después de detectarlos, con el 100 % de los clientes cubiertos. Las 10 fallas del proveedor inestable (Cumbre) se reenviaron solas.
- **Cambio de turno:** el partido arranca en el minuto 40 y el turno cambia en el 50. Ninguna orden salió firmada por un juez fuera de turno y no hubo rechazos.
  - La fase 1 de pelotaya figura "nunca" porque terminó en el minuto 36, antes de que arrancara esta corrida.
  - Los streams que ya estaban al aire cuando arrancó (pelotaya fase 2, golazo, verpartido) se bloquearon en el minuto 43, a los ~3 minutos de partido de conectarse el motor. Por eso la visibilidad residual promedio es alta: no es una demora del circuito.

## Cómo repetirlas

```bash
PYTHONUTF8=1 python simulador/servidor.py --acelerar 30 --inicio-min 40
PYTHONUTF8=1 python -m plataforma.main --sim http://localhost:8080 --juez-automatico
PYTHONUTF8=1 python evaluacion/verificar.py --log salida/registro.jsonl
```
