"""Genera un escenario de PRUEBA de reclamos a partir del de práctica oficial (no modifica datos/ ni evaluacion/).

Caso de hosting compartido con sufijo común: el stream pirata tv.verpartido-hd pasa a vivir en hostcomun.test junto
a dos sitios legítimos, así que los tres dominios de la IP comparten el sufijo hostcomun.test. Con solo mirar el sufijo
(sitio_de) parecen un mismo sitio. La plataforma tiene que darse cuenta de que la IP es compartida (el ASN es "Pampa
Web Hosting Compartido") y bloquear solo el dominio: daño colateral 0 y sin reclamos.
Para ejercitar los reclamos de punta a punta se corre con --falla dns-desactualizado (ver pruebas/motor_con_falla.py).
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
AQUI = Path(__file__).resolve().parent
RENOMBRES = {
    "tv.verpartido-hd.test": "tv.verpartido.hostcomun.test",
    "panaderia-la-espiga.test": "panaderia-la-espiga.hostcomun.test",
    "club-atletico-barrio-norte.test": "club-atletico-barrio-norte.hostcomun.test",
}
IP = "192.0.2.50"


def _renombrar(texto: str) -> str:
    for viejo, nuevo in RENOMBRES.items():
        texto = texto.replace(f'"{viejo}', f'"{nuevo}').replace(f"//{viejo}", f"//{nuevo}")
    return texto


def generar() -> None:
    esc = json.loads(_renombrar((RAIZ / "datos" / "escenario_practica.json").read_text(encoding="utf-8")))
    esc["id"] = "practica-01-reclamos"
    esc["dns_pasivo"][IP] = list(RENOMBRES.values())
    verdad = json.loads(_renombrar((RAIZ / "evaluacion" / "verdad_practica.json").read_text(encoding="utf-8")))
    verdad["escenario_id"] = esc["id"]
    verdad["dominios_piratas"] = [d for d in verdad["dominios_piratas"] if d != "verpartido-hd.test"]
    (AQUI / "escenario_reclamos.json").write_text(json.dumps(esc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (AQUI / "verdad_reclamos.json").write_text(json.dumps(verdad, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("escenario de reclamos generado en", AQUI)


if __name__ == "__main__":
    generar()
