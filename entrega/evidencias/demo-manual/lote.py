import asyncio, json, urllib.request
from playwright.async_api import async_playwright
BASE="http://localhost:8001"; CAP="/home/ubuntu/demo/capturas"
def api(r):
    with urllib.request.urlopen(urllib.request.Request(BASE+r, headers={"X-Juez-Pin":"1234"}), timeout=10) as x: return json.loads(x.read())
async def main():
    async with async_playwright() as p:
        b=await p.chromium.connect_over_cdp("http://localhost:29229"); pg=await b.contexts[0].new_page()
        await pg.set_viewport_size({"width":430,"height":900})
        pg.on("pageerror", lambda e: print("PAGEERROR", e, flush=True))
        await pg.goto(BASE+"/juez/"); await pg.evaluate("sessionStorage.clear()"); await pg.reload()
        await pg.fill("#pin","1234"); await pg.press("#pin","Enter")
        while await pg.locator(".pedido").count() < 2: await pg.wait_for_timeout(1000)
        ids=[await c.get_attribute("data-id") for c in await pg.locator(".pedido").all()]
        print("min", api("/api/estado")["minuto_actual"], "pendientes", ids, "| boton:", await pg.inner_text("#firmar-todos"), "| cabecera:", await pg.inner_text("#juez"), flush=True)
        await pg.screenshot(path=f"{CAP}/04-lote-antes.png")
        await pg.click("#firmar-todos"); await pg.wait_for_timeout(1500)
        print("aviso:", await pg.locator("[data-aviso], .aviso").all_inner_texts(), flush=True)
        print("pedidos:", [(x["pedido_id"],x["estado"],x["juez_id"],x["decidido_min"]) for x in api("/api/pedidos")["pedidos"]], flush=True)
        await pg.wait_for_timeout(6000)
        print("ordenes:", sorted((o["pedido_id"],o["proveedor_id"],o["tipo"],o["estado"]) for o in api("/api/ordenes")["ordenes"]), flush=True)
        await pg.screenshot(path=f"{CAP}/04-lote-despues.png", full_page=True)
asyncio.run(main())
