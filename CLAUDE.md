# CLAUDE.md — Equipo Desafío Fútbol (Hackatón Argentina Space 2026)

Este repo lo usan **5 personas, cada una con su propio agente**, al mismo tiempo.
La regla número uno es **no pisarse**. Antes de tocar cualquier cosa, seguí el protocolo de abajo.

## Qué estamos construyendo
El MVP de una plataforma federal de órdenes de bloqueo en vivo contra transmisiones piratas de fútbol.
Se conecta al simulador de la organización y hace el circuito completo: expediente → juez de turno → proveedores → confirmación → vencimiento → auditoría.
**Deploy:** la web del juez, el registro público y la API van en **Vercel**, sobre una base Postgres. El motor corre en un Vercel Sandbox, o en la notebook si el simulador del final no se alcanza desde internet (decisiones 15 a 24 y `coordinacion/diseno.md` §1).
El enunciado completo está en `README.md`. Las decisiones tomadas están en `coordinacion/decisiones.md`.

## Qué es nuestro y qué no
- **De la organización (NO se toca):** `simulador/`, `evaluacion/`, `ejemplos/`, `datos/`, `README.md` original.
- **Nuestro:** `plataforma/`, `entrega/`, `coordinacion/`, este `CLAUDE.md`.
- La organización puede actualizar su parte: `git pull upstream main` (el remoto `upstream` es `qualydata-org/desafio-futbol`).

## Protocolo (obligatorio, en este orden)

1. **Al arrancar una sesión:**
   ```bash
   git pull --rebase
   python coordinacion/buzon.py estado --yo <tu-nombre>
   ```
   Leé los mensajes nuevos dirigidos a vos o a `todos` y el estado de las tareas.
2. **Reservá antes de tocar:** `python coordinacion/buzon.py tomar T03 --yo <tu-nombre>`, después commit y push **en el momento**.
   Si el push choca: `git pull --rebase` y fijate si otro la tomó primero. Si la tomó otro, soltala y elegí otra.
3. **Tocá solo tu carpeta.** Cada tarea dice qué carpeta es suya. Si necesitás un cambio en la carpeta de otro, mandale un mensaje; no lo edites vos.
4. **Los contratos no se cambian en silencio.** Cualquier cambio en `coordinacion/contratos.md` va acompañado de un mensaje a `todos` y sube la versión.
5. **Mensajes:** siempre con `python coordinacion/buzon.py mensaje ...`, que crea un archivo nuevo. Nunca edites un mensaje ajeno.
6. **Push seguido:** cada avance chico que funcione → `git pull --rebase` → commit → push a `main`. Nada de ramas largas.
7. **Al terminar una tarea:** `python coordinacion/buzon.py hecha T03 --yo <tu-nombre>`, push, y un mensaje si destraba a alguien.

Si algo del protocolo no se puede cumplir, avisá en el buzón a `todos` antes de seguir.

## Prioridades del equipo
1. El circuito completo funcionando contra el simulador en el partido final. Los extras no compensan un núcleo que no corre.
2. Evidencia válida, cero daño colateral, velocidad.
3. Código original hecho durante el evento. Nada de datos personales reales ni claves reales.

## Correr el simulador (Windows)
```bash
PYTHONUTF8=1 python simulador/servidor.py --acelerar 30
PYTHONUTF8=1 python evaluacion/verificar.py --log salida/registro.jsonl
```
Sin `PYTHONUTF8=1`, en Windows el simulador se cae al imprimir el `≈`.
