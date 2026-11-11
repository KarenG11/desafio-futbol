#!/usr/bin/env python3
"""Buzón del equipo: tareas (un archivo por tarea) y mensajes (un archivo por mensaje).

Solo biblioteca estándar. Ver coordinacion/LEEME.md para el uso.
"""
import argparse
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
TAREAS = RAIZ / "tareas"
BUZON = RAIZ / "buzon"
LEIDOS = RAIZ / ".leidos"  # local, en .gitignore
ARG = timezone(timedelta(hours=-3))
ESTADOS = ("libre", "en-curso", "hecha")


def ahora() -> datetime:
    return datetime.now(ARG)


def slug(texto: str, largo: int = 40) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:largo].strip("-") or "sin-asunto"


def nombre(valor: str) -> str:
    valor = slug(valor, 30)
    if not valor:
        sys.exit("Falta un nombre válido (ver coordinacion/equipo.md).")
    return valor


def leer(ruta: Path) -> tuple:
    """Devuelve (campos del encabezado, cuerpo) de un archivo con encabezado '---'."""
    texto = ruta.read_text(encoding="utf-8")
    campos, cuerpo = {}, texto
    if texto.startswith("---\n"):
        cabecera, _, cuerpo = texto[4:].partition("\n---\n")
        for linea in cabecera.splitlines():
            clave, sep, valor = linea.partition(":")
            if sep:
                campos[clave.strip()] = valor.strip()
    return campos, cuerpo


def escribir(ruta: Path, campos: dict, cuerpo: str) -> None:
    cabecera = "\n".join(f"{k}: {v}" for k, v in campos.items())
    ruta.write_text(f"---\n{cabecera}\n---\n{cuerpo.lstrip(chr(10))}", encoding="utf-8")


def buscar_tarea(tid: str) -> Path:
    tid = tid.upper()
    hallados = sorted(TAREAS.glob(f"{tid}-*.md"))
    if not hallados:
        sys.exit(f"No existe la tarea {tid}. Mirá: python coordinacion/buzon.py estado --yo <vos>")
    return hallados[0]


def recordar_push(accion: str) -> None:
    print(f"\nAhora subilo YA para que nadie te pise:\n"
          f"  git pull --rebase && git add coordinacion && git commit -m \"{accion}\" && git push")


# --- comandos ---------------------------------------------------------------------

def cmd_estado(args) -> None:
    yo = nombre(args.yo)
    tareas = []
    for ruta in sorted(TAREAS.glob("T*.md")):
        campos, _ = leer(ruta)
        tareas.append(campos)
    print("TAREAS")
    for estado in ESTADOS:
        grupo = [t for t in tareas if t.get("estado") == estado]
        if estado == "hecha" and not args.todo:
            print(f"  [hecha] {len(grupo)} tarea(s)  (--todo para verlas)")
            continue
        for t in grupo:
            dueno = f" · {t.get('dueno')} desde {t.get('desde')}" if t.get("dueno") else ""
            marca = "  ← TUYA" if t.get("dueno") == yo else ""
            print(f"  [{estado}] {t.get('id')} {t.get('titulo')} ({t.get('carpeta')}){dueno}{marca}")

    LEIDOS.mkdir(exist_ok=True)
    archivo_leidos = LEIDOS / f"{yo}.txt"
    leidos = set(archivo_leidos.read_text(encoding="utf-8").split()) if archivo_leidos.exists() else set()
    mensajes = []
    for ruta in sorted(BUZON.glob("*.md")):
        campos, cuerpo = leer(ruta)
        para = {p.strip() for p in campos.get("para", "").split(",")}
        if "todos" in para or yo in para or campos.get("de") == yo:
            mensajes.append((ruta, campos, cuerpo))
    nuevos = [m for m in mensajes if m[0].name not in leidos and m[1].get("de") != yo]
    mostrar = mensajes if args.todo else nuevos
    print(f"\nMENSAJES {'(todos)' if args.todo else f'nuevos para {yo}'}: {len(mostrar)}")
    for ruta, campos, cuerpo in mostrar:
        aviso = "  [ESPERA RESPUESTA]" if campos.get("requiere_respuesta") == "si" else ""
        print(f"\n— {campos.get('fecha')} · de {campos.get('de')} para {campos.get('para')}{aviso}")
        print(f"  Asunto: {campos.get('asunto')}  ({ruta.name})")
        for linea in cuerpo.strip().splitlines():
            print(f"  {linea}")
    archivo_leidos.write_text("\n".join(sorted(leidos | {m[0].name for m in mensajes})), encoding="utf-8")


def cmd_mensaje(args) -> None:
    de = nombre(args.de)
    para = ",".join(nombre(p) for p in args.para.split(","))
    momento = ahora()
    BUZON.mkdir(exist_ok=True)
    base = f"{momento:%Y-%m-%d_%H%M%S}_{de}_a-{para.replace(',', '-')}_{slug(args.asunto)}"
    ruta = BUZON / f"{base}.md"
    campos = {"de": de, "para": para, "fecha": f"{momento:%Y-%m-%d %H:%M}", "asunto": args.asunto,
              "requiere_respuesta": "si" if args.requiere_respuesta else "no"}
    if args.responde_a:
        campos["responde_a"] = args.responde_a
    escribir(ruta, campos, args.texto.replace("\\n", "\n") + "\n")
    print(f"Mensaje creado: {ruta.relative_to(RAIZ.parent)}")
    recordar_push(f"buzon: {de} a {para}: {args.asunto}")


def cambiar_tarea(tid: str, yo: str, nuevo: str) -> None:
    ruta = buscar_tarea(tid)
    campos, cuerpo = leer(ruta)
    actual, dueno = campos.get("estado"), campos.get("dueno", "")
    if nuevo == "en-curso" and actual == "en-curso" and dueno != yo:
        sys.exit(f"{campos['id']} ya la tiene {dueno} desde {campos.get('desde')}. Elegí otra o mandale un mensaje.")
    if nuevo in ("libre", "hecha") and dueno and dueno != yo:
        sys.exit(f"{campos['id']} es de {dueno}. Solo el dueño la suelta o la cierra.")
    campos["estado"] = nuevo
    campos["dueno"] = "" if nuevo == "libre" else yo
    campos["desde"] = "" if nuevo == "libre" else f"{ahora():%Y-%m-%d %H:%M}"
    escribir(ruta, campos, cuerpo)
    print(f"{campos['id']} → {nuevo}" + (f" ({yo})" if campos["dueno"] else ""))
    recordar_push(f"tareas: {campos['id']} {nuevo} ({yo})")


def cmd_tarea_nueva(args) -> None:
    yo = nombre(args.yo)
    TAREAS.mkdir(exist_ok=True)
    numeros = [int(m.group(1)) for r in TAREAS.glob("T*.md") if (m := re.match(r"T(\d+)-", r.name))]
    tid = f"T{(max(numeros) + 1) if numeros else 0:02d}"
    campos = {"id": tid, "titulo": args.titulo, "carpeta": args.carpeta, "estado": "libre",
              "dueno": "", "desde": "", "creada_por": yo, "depende_de": args.depende_de or ""}
    cuerpo = (args.detalle.replace("\\n", "\n") if args.detalle else "## Qué hay que hacer\n\n## Terminada cuando\n") + "\n"
    ruta = TAREAS / f"{tid}-{slug(args.titulo)}.md"
    escribir(ruta, campos, cuerpo)
    print(f"Tarea creada: {ruta.relative_to(RAIZ.parent)}")
    recordar_push(f"tareas: nueva {tid} {args.titulo}")


def main() -> None:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Buzón del equipo")
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("estado", help="tareas y mensajes nuevos para vos")
    s.add_argument("--yo", required=True)
    s.add_argument("--todo", action="store_true", help="incluye tareas hechas y mensajes ya leídos")
    s.set_defaults(fn=cmd_estado)

    s = sub.add_parser("mensaje", help="dejar un mensaje")
    s.add_argument("--de", required=True)
    s.add_argument("--para", required=True, help="nombre, varios con coma, o 'todos'")
    s.add_argument("--asunto", required=True)
    s.add_argument("--texto", required=True)
    s.add_argument("--responde-a", help="nombre del archivo del mensaje al que responde")
    s.add_argument("--requiere-respuesta", action="store_true")
    s.set_defaults(fn=cmd_mensaje)

    for comando, estado in (("tomar", "en-curso"), ("soltar", "libre"), ("hecha", "hecha")):
        s = sub.add_parser(comando, help=f"pasar una tarea a '{estado}'")
        s.add_argument("tarea")
        s.add_argument("--yo", required=True)
        s.set_defaults(fn=lambda a, e=estado: cambiar_tarea(a.tarea, nombre(a.yo), e))

    s = sub.add_parser("tarea-nueva", help="crear una tarea")
    s.add_argument("--yo", required=True)
    s.add_argument("--titulo", required=True)
    s.add_argument("--carpeta", required=True)
    s.add_argument("--depende-de")
    s.add_argument("--detalle", help="texto del cuerpo (usar \\n para saltos de línea)")
    s.set_defaults(fn=cmd_tarea_nueva)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
