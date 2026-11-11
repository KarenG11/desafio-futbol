# Coordinación del equipo

El protocolo completo está en el `CLAUDE.md` de la raíz. Acá está el formato de cada cosa.

| Archivo / carpeta | Para qué | ¿Quién lo edita? |
|---|---|---|
| `equipo.md` | Quién es quién y qué carpeta es de cada uno | Cualquiera, solo su propia fila |
| `contratos.md` | Cómo se pasan datos las piezas | Solo con mensaje a `todos` + versión nueva |
| `decisiones.md` | Decisiones tomadas | Se agrega abajo; nunca se borra |
| `tareas/T??-*.md` | Una tarea por archivo | El dueño de la tarea (o `buzon.py`) |
| `buzon/*.md` | Un mensaje por archivo | Solo quien lo escribe, al crearlo |

## Comandos
```bash
python coordinacion/buzon.py estado --yo alejo           # tareas + mensajes nuevos para vos
python coordinacion/buzon.py tomar T03 --yo rocio        # reservar (después: commit + push YA)
python coordinacion/buzon.py soltar T03 --yo rocio       # liberar una tarea que no vas a hacer
python coordinacion/buzon.py hecha T03 --yo rocio        # terminada
python coordinacion/buzon.py mensaje --de rocio --para todos --asunto "Expediente listo" \
    --texto "plataforma/evidencia ya arma expedientes. Contrato v1, sin cambios."
python coordinacion/buzon.py tarea-nueva --yo alejo --titulo "Exportar expediente a PDF" --carpeta entrega/
```
`--para` acepta un nombre, varios separados por coma o `todos`.
El script marca como leídos los mensajes que ya te mostró. Esa marca es local y no se sube al repo.

## Estados de una tarea
`libre` → `en-curso` (con dueño) → `hecha`. Si la dejás, `soltar` la devuelve a `libre`.
