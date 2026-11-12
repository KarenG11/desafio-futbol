"""Recorrido manual de la pantalla del juez en Chrome (sin juez automático)."""
import asyncio, json, time, urllib.request
from playwright.async_api import async_playwright
BASE = "http://localhost:8001"; CAP = "/home/ubuntu/demo/capturas"
H = {"X-Juez-Pin": "1234", "Content-Type": "application/json"}
def api(ruta, cuerpo=None):
    req = urllib.request.Request(BASE + ruta, data=json.dumps(cuerpo).encode() if cuerpo is not None else None, headers=H)
    try:
        with urllib.request.urlopen(req, timeout=10) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")
def log(*a):
    m = api("/api/estado")[1].get("minuto_actual")
    print(f"[min {m}]", *a, flush=True)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://localhost:29229")
        pg = await b.contexts[0].new_page()
        await pg.set_viewport_size({"width": 430, "height": 900})
        pg.on("pageerror", lambda e: print("PAGEERROR", e, flush=True))
        pg.on("console", lambda m: print("CONSOLE", m.text, flush=True) if m.type == "error" and "favicon" not in m.text else None)
        await pg.goto(BASE + "/juez/")
        await pg.evaluate("sessionStorage.clear()"); await pg.reload()
        await pg.screenshot(path=f"{CAP}/01-ingreso.png")
        await pg.fill("#pin", "1234"); await pg.press("#pin", "Enter")
        vistos, estados_orden, firmas, publico_prev = set(), {}, 0, None
        asumido, prueba_saliente = False, False
        while True:
            st = api("/api/estado")[1]; m = st.get("minuto_actual") or 0
            # expedientes de las tarjetas nuevas
            for card in await pg.locator(".pedido").all():
                pid = await card.get_attribute("data-id")
                if pid in vistos: continue
                vistos.add(pid)
                host = await card.locator(".pedido__sitio").inner_text()
                await card.locator(".expediente summary").click()
                try:
                    await card.locator('.expediente__cuerpo[data-cargado="si"]').wait_for(timeout=8000)
                    txt = await card.locator(".expediente__cuerpo").inner_text()
                except Exception as e:
                    txt = "NO CARGÓ: " + await card.locator(".expediente__cuerpo").inner_text()
                bloqueo = await card.locator(".d-bloqueo").inner_text()
                log(f"PEDIDO {pid} {host}\n  Qué se bloquea: {bloqueo}\n  " + txt.replace("\n\n", "\n").replace("\n", "\n  "))
                if host.startswith(("s1.pelotaya", "live.golazo")):
                    await card.scroll_into_view_if_needed()
                    await card.screenshot(path=f"{CAP}/02-expediente-{host.split('.')[1]}.png")
            # cambio de turno
            if m >= 50 and not asumido:
                if not prueba_saliente:
                    pend = [x["pedido_id"] for x in api("/api/pedidos?estado=pendiente")[1]["pedidos"]] or ["P-999"]
                    log("FIRMA JUEZA SALIENTE ->", api("/api/pedidos/aprobar", {"pedido_ids": pend, "juez_id": "jueza-laura-ficticia"}))
                    prueba_saliente = True
                    await pg.wait_for_timeout(2500)
                    await pg.screenshot(path=f"{CAP}/05-cambio-turno.png")
                boton = pg.locator('[data-aviso="traspaso"] button')
                if await boton.count():
                    await boton.first.click(); asumido = True
                    await pg.wait_for_timeout(2500)
                    log("ASUMIR TURNO (UI):", (await pg.locator(".avisos, [data-aviso]").all_inner_texts())[-2:])
                    await pg.screenshot(path=f"{CAP}/06-turno-asumido.png")
            # firma: individual si hay 1, en lote si hay más
            n = await pg.locator(".pedido").count()
            listo = st.get("turno_ratificado") and (m < 50 or asumido)
            if n and listo:
                await pg.wait_for_timeout(300)
                if n == 1 or firmas == 0:
                    card = pg.locator(".pedido").first; pid = await card.get_attribute("data-id")
                    await card.locator(".b-firmar").click(); log(f"FIRMA INDIVIDUAL {pid} por {st['jueces_de_turno']}")
                else:
                    ids = [await c.get_attribute("data-id") for c in await pg.locator(".pedido").all()]
                    await pg.click("#firmar-todos"); log(f"FIRMA EN LOTE {ids} por {st['jueces_de_turno']}")
                firmas += 1
                await pg.wait_for_timeout(2500)
                if firmas in (1, 2): await pg.screenshot(path=f"{CAP}/03-firma-{firmas}.png", full_page=True)
            # estados de órdenes
            for o in api("/api/ordenes")[1]["ordenes"]:
                if estados_orden.get(o["orden_id"]) != o["estado"]:
                    estados_orden[o["orden_id"]] = o["estado"]
                    log(f"ORDEN {o['orden_id']} {o['proveedor_id']} {o['tipo']} {o['objetivo']} -> {o['estado']} (intento {o.get('intentos')}, juez {o.get('juez_id')})")
            pub = api("/api/publico")[1]["entradas"]
            resumen = [(e.get("objetivo"), e.get("tipo"), json.dumps(e.get("estados") or e.get("proveedores"), ensure_ascii=False)) for e in pub]
            if resumen != publico_prev:
                log(f"PUBLICO {len(pub)} entradas; última: {json.dumps(pub[-1], ensure_ascii=False)[:400] if pub else '-'}")
                publico_prev = resumen
            if st.get("finalizado"):
                await pg.wait_for_timeout(4000)
                await pg.screenshot(path=f"{CAP}/07-final.png", full_page=True)
                break
            await pg.wait_for_timeout(1000)
        json.dump({"ordenes": api("/api/ordenes")[1]["ordenes"], "publico": api("/api/publico")[1]["entradas"],
                   "pedidos": api("/api/pedidos")[1]["pedidos"]}, open(f"{CAP}/final.json", "w"), ensure_ascii=False, indent=1)
        await pg.goto(BASE + "/api/publico"); await pg.screenshot(path=f"{CAP}/08-publico.png")
        print("FIN", flush=True)
asyncio.run(main())
