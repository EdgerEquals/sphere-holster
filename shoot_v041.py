"""v0.4.1 headless screenshots: fresh default view (3D waves on by default), v0.4 waves isolated, front snap; console + state checks."""
import asyncio, os, shutil, sys
from playwright.async_api import async_playwright
H = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(H, "screenshots"); COPY = os.path.join(H, "shots")
ARGS = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
async def snap(pg, name, js=None, wait=1500):
    if js: await pg.evaluate(js)
    await pg.wait_for_timeout(wait)
    path = f"{OUT}/{name}.png"; await pg.screenshot(path=path)
    os.makedirs(COPY, exist_ok=True); shutil.copy(path, COPY); print("shot", path)
async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "file://" + os.path.join(H, "index.html")
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=ARGS)
        errs = []
        pg = await b.new_page(viewport={"width": 1500, "height": 900})
        pg.on("console", lambda m: errs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        await pg.goto(url)
        await pg.wait_for_function("window.VIEWER_READY===true", timeout=60000)
        print("version", await pg.inner_text("#ver"))
        print("defaults: view, wvAll, quartz op, oldwf:", await pg.evaluate("[viewmode.value,wvAll.checked,qop.value,oldwf.checked]"))
        await snap(pg, "58_v041_default_view_waves_on", wait=7000)   # untouched fresh load
        await snap(pg, "59_v041_v04_waves_isolated_v03_overlays_off", 'document.getElementById("oldwf").click()', wait=1500)
        await snap(pg, "60_v041_front_snap_waves_on", 'document.getElementById("oldwf").click();snapTo("front")', wait=2000)
        await pg.evaluate('setWaves(false)'); print("all waves off -> quartz op restored:", await pg.evaluate("qop.value"))
        print("danny 5900:", await pg.evaluate('setDrive({dQz:"danny"});window.QZ_CL'), "| f sweep:", await pg.evaluate('dSweep.options[0].textContent'))
        print("errors:", "\n".join(errs) or "none", "| LASTERR", await pg.evaluate("window.LASTERR||null"))
        await b.close()
asyncio.run(main())
