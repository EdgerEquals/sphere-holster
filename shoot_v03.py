import asyncio
from playwright.async_api import async_playwright
OUT = "/workspace/grok_thread/sphere_model_v0/screenshots"
ARGS = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
SET = 'setPreset("scope","1");setView("cut");setDrive({dFill:"10",dFillU:"torr",dV:"1000",dTs:"293.15"});'
async def shot(pg, name, js, anchor):
    await pg.evaluate(js); await pg.wait_for_timeout(1200)
    await pg.evaluate(f'document.getElementById("{anchor}").scrollIntoView({{block:"start"}})'); await pg.wait_for_timeout(600)
    await pg.screenshot(path=f"{OUT}/{name}.png")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=ARGS)
        errs = []
        pg = await b.new_page(viewport={"width": 1500, "height": 900})
        pg.on("console", lambda m: errs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        await pg.goto("file:///workspace/grok_thread/sphere_model_v0/index.html")
        await pg.wait_for_function("window.VIEWER_READY===true", timeout=60000); await pg.wait_for_timeout(1500)
        print("version", await pg.inner_text("#ver"))
        await pg.evaluate(SET)
        await shot(pg, "39_v03_drive_f_axis_2p5MHz_ion_feedback_caution", 'setDrive({dF:"2.5M"});document.getElementById("dRun").click()', "dF")
        await shot(pg, "40_v03_drive_50GHz_quasistatic_invalid_noformation", 'setDrive({dF:"50G"});document.getElementById("dRun").click()', "dF")
        await shot(pg, "41_v03_drive_600THz_optical_band", 'setDrive({dF:"600T"});document.getElementById("dRun").click()', "dF")
        print("regime 600T:", await pg.inner_text("#dReg"))
        await shot(pg, "42_v03_sweep_f_100k_1000T_60pts", 'setDrive({dF:"2.5M",dSweep:"f",dLo:"100k",dHi:"1000T",dN:"60"});document.getElementById("dSweepGo").click()', "dSweepGo")
        await shot(pg, "43_v03_sweep_ID_scope_OD2_f2M", 'setDrive({dF:"2M",dSweep:"ID"});document.getElementById("dRun").click();document.getElementById("dSweepGo").click()', "dSweepGo")
        print("ID bounds", await pg.evaluate('[dLo.value,dHi.value,dN.value,dSwU.textContent]'))
        await shot(pg, "44_v03_sweep_OD_scope_ID1_f2M", 'setDrive({dSweep:"OD"});document.getElementById("dSweepGo").click()', "dSweepGo")
        await shot(pg, "45_v03_sweep_fill_typed_1_to_1k_25pts", 'setDrive({dSweep:"fill",dLo:"1",dHi:"1k",dN:"25"});document.getElementById("dSweepGo").click()', "dSweepGo")
        await shot(pg, "46_v03_sound_speed_selector_danny_5900", 'setDrive({dQz:"danny",dF:"2M"});document.getElementById("dRun").click()', "dQz")
        print("danny:", (await pg.inner_text("#dQzSrc"))[:200])
        await pg.evaluate('setDrive({dQz:"danny"});setView("cut");setTime(null,0);document.getElementById("gl").scrollIntoView()'); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f"{OUT}/47_v03_scope_cut_waveforms_quartz_5900.png")
        await pg.evaluate('setDrive({dQz:"vrh"})')
        bad = await pg.evaluate('setDrive({dSweep:"f",dLo:"5k",dHi:"1k",dN:"10"});document.getElementById("dSweepGo").click();dMsg.textContent')
        print("bad-bounds msg:", bad)
        print("desktop errors:", "\n".join(errs) or "none", "| LASTERR", await pg.evaluate("window.LASTERR||null"))
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
        mp = await ctx.new_page(); merr = []
        mp.on("pageerror", lambda e: merr.append(str(e)))
        mp.on("console", lambda m: merr.append(f"{m.type}: {m.text}") if m.type == "error" else None)
        await mp.goto("file:///workspace/grok_thread/sphere_model_v0/index.html")
        await mp.wait_for_function("window.VIEWER_READY===true", timeout=60000); await mp.wait_for_timeout(1500)
        await mp.evaluate(SET + 'setDrive({dF:"600T"});document.getElementById("dRun").click()'); await mp.wait_for_timeout(1000)
        await mp.evaluate('document.getElementById("dF").scrollIntoView({block:"start"})'); await mp.wait_for_timeout(600)
        await mp.screenshot(path=f"{OUT}/48_v03_iphone_drive_f_axis_regime.png")
        await mp.evaluate('setDrive({dF:"2M",dSweep:"ID"});document.getElementById("dSweepGo").click();document.getElementById("dSw").scrollIntoView({block:"start"})'); await mp.wait_for_timeout(1000)
        await mp.screenshot(path=f"{OUT}/49_v03_iphone_ID_sweep.png")
        await mp.evaluate('window.scrollTo(0,0)'); await mp.wait_for_timeout(800)
        await mp.screenshot(path=f"{OUT}/50_v03_iphone_top_version.png")
        print("mobile errors:", merr or "none")
        await b.close()
asyncio.run(main())
