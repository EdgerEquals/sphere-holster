import asyncio, sys, json
from playwright.async_api import async_playwright
OUT = "/workspace/grok_thread/sphere_model_v0/screenshots"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await b.new_page(viewport={"width": 1500, "height": 900})
        errs = []
        pg.on("console", lambda m: errs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        await pg.goto("file:///workspace/grok_thread/sphere_model_v0/index.html")
        await pg.wait_for_function("window.VIEWER_READY===true", timeout=60000); await pg.wait_for_timeout(1000)
        print("preset", await pg.evaluate("document.getElementById('preset').selectedOptions[0].text"))
        # blank inputs -> must refuse
        await pg.click("#dRun"); print("blank msg:", await pg.inner_text("#dMsg"))
        await pg.locator("#dRun").scroll_into_view_if_needed()
        await pg.locator("#side").screenshot(path=f"{OUT}/20_drive_panel_blank_required.png")
        await pg.evaluate("setDrive({dFill:'22', dV:'600', dF:'1000'})"); await pg.click("#dRun"); await pg.wait_for_timeout(500)
        r = await pg.evaluate("({E:DRIVE_LAST.E_dis,dTg:DRIVE_LAST.dTg,Vb:DRIVE_LAST.Vb,flags:DRIVE_LAST.flags,N:DRIVE_LAST.N})"); print("run", r)
        await pg.evaluate("document.getElementById('dTr').scrollIntoView()")
        await pg.locator("#side").screenshot(path=f"{OUT}/21_drive_single_cycle_1kHz_22Torr_600V.png")
        await pg.select_option("#dSweep", "f"); await pg.click("#dSweepGo"); await pg.wait_for_timeout(800)
        await pg.evaluate("document.getElementById('dSw').scrollIntoView()")
        await pg.locator("#dSw").screenshot(path=f"{OUT}/22_drive_sweep_frequency.png")
        await pg.select_option("#dSweep", "fill"); await pg.click("#dSweepGo"); await pg.wait_for_timeout(800)
        await pg.locator("#dSw").screenshot(path=f"{OUT}/23_drive_sweep_fill.png")
        await pg.locator("#dOut").screenshot(path=f"{OUT}/24_drive_response_table.png")
        await pg.evaluate('setView("ortho"); document.getElementById("clock").value="shared"; setTime(1.5e-7,0)'); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f"{OUT}/25_scope_ortho_with_drive_f.png")
        print("\n".join(errs) or "no console errors"); print("LASTERR", await pg.evaluate("window.LASTERR||null"))
        await b.close()
asyncio.run(main())
