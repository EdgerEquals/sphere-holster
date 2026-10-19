"""v0.4 headless screenshots: default view, Front/Side/Top snaps, 3D waves, toggle panel; v0.3 feature checks."""
import asyncio, os, shutil, sys
from playwright.async_api import async_playwright
H = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(H, "screenshots"); COPY = os.path.join(H, "shots")
ARGS = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
SET = 'setPreset("scope","1");setView("cut");setDrive({dFill:"10",dFillU:"torr",dV:"1000",dTs:"293.15",dQz:"danny",dF:"2.5M"});setTime(null,0);'
async def snap(pg, name, js=None, wait=1500, el=None):
    if js: await pg.evaluate(js)
    await pg.wait_for_timeout(wait)
    path = f"{OUT}/{name}.png"
    if el: await pg.locator(el).screenshot(path=path)
    else: await pg.screenshot(path=path)
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
        await pg.wait_for_function("window.VIEWER_READY===true", timeout=60000); await pg.wait_for_timeout(1500)
        print("version", await pg.inner_text("#ver"))
        await pg.evaluate(SET)
        await snap(pg, "51_v04_default_view", 'document.getElementById("gl").scrollIntoView()')
        for n, k in (("52_v04_snap_front", "front"), ("53_v04_snap_side", "side"), ("54_v04_snap_top", "top")):
            await snap(pg, n, f'snapTo("{k}")', wait=1200)
            print(k, await pg.evaluate('[...cam_dbg()]') if False else await pg.evaluate("window.SNAP_STATE"))
        await snap(pg, "55_v04_waves_all_on_front", 'setWaves(true);document.getElementById("qop").value=0.3;document.getElementById("qop").oninput();snapTo("front")', wait=6500)
        await snap(pg, "56_v04_waves_all_on_free_view", 'snapTo("home")', wait=2600)
        await pg.evaluate('setWaves({magenta:false,green:false});document.getElementById("snapShow").click()')
        print("master checked/indeterminate", await pg.evaluate('[wvAll.checked,wvAll.indeterminate]'))
        await pg.evaluate('document.getElementById("snapopts").scrollIntoView({block:"start"})')
        await snap(pg, "57_v04_toggle_panel_some_waves_off", wait=2200)
        await pg.evaluate('document.getElementById("snapShow").click();document.getElementById("side").scrollTop=0')
        # v0.3 feature checks
        print("EMF range axis/regime:", (await pg.inner_text("#dReg"))[:160].replace("\n", " "))
        print("sweep f option:", await pg.evaluate('dSweep.options[0].textContent'))
        print("ID bounds:", await pg.evaluate('setDrive({dSweep:"ID"});[dLo.value,dHi.value,dN.value,dSwU.textContent]'))
        print("f bounds:", await pg.evaluate('setDrive({dSweep:"f"});[dLo.value,dHi.value,dN.value]'))
        print("bad-bounds msg:", await pg.evaluate('setDrive({dSweep:"f",dLo:"5k",dHi:"1k",dN:"10"});document.getElementById("dSweepGo").click();dMsg.textContent'))
        print("danny:", (await pg.inner_text("#dQzSrc"))[:90], "| QZ_CL", await pg.evaluate("window.QZ_CL"))
        print("wave note:", await pg.inner_text("#wvNote"))
        fr0 = await pg.evaluate("window.FRAMES"); await pg.wait_for_timeout(2000); fr1 = await pg.evaluate("window.FRAMES")
        print("fps (swiftshader, waves on):", (fr1 - fr0) / 2)
        print("desktop errors:", "\n".join(errs) or "none", "| LASTERR", await pg.evaluate("window.LASTERR||null"))
        await b.close()
asyncio.run(main())
