"""SOLO PRUEBAS: corre el motor con una falla inyectada para ejercitar el circuito de reclamos de punta a punta.

Falla: el DNS pasivo que consulta el cerebro al clasificar está desactualizado para una IP. Solo lista los dominios
indicados y dice que el ASN es un hosting dedicado. Por eso la plataforma recomienda bloquear la IP, aunque en
realidad está compartida con sitios legítimos. El simulador no cambia: aplica el bloqueo sobre los dominios reales,
emite los reclamos y la plataforma tiene que verificarlos con un DNS fresco, levantar y reemplazar por dominio.
El daño colateral que produce esta corrida es deliberado y se informa tal cual; no es la corrida de aceptación.

    python -m plataforma.pruebas.motor_con_falla --ip-desactualizada 192.0.2.50 \
        --dominios tv.verpartido.hostcomun.test -- --sim http://127.0.0.1:8080 --juez-automatico ...
"""
import argparse
import sys

from plataforma.analisis import cerebro as mod_cerebro


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip-desactualizada", required=True)
    ap.add_argument("--dominios", nargs="+", required=True)
    a, resto = ap.parse_known_args()
    resto = [x for x in resto if x != "--"]
    original = mod_cerebro.Cerebro.__init__

    def init_con_falla(self, partido, consultar_dns):
        def consultar(ip):
            real = consultar_dns(ip)
            if ip != a.ip_desactualizada or not real:
                return real
            return {**real, "organizacion": "Hosting Dedicado (DNS desactualizado: falla inyectada)",
                    "dominios": list(a.dominios)}
        original(self, partido, consultar)

    mod_cerebro.Cerebro.__init__ = init_con_falla
    from plataforma.motor import __main__ as motor_main
    sys.argv = ["plataforma.motor"] + resto
    motor_main.main()


if __name__ == "__main__":
    main()
