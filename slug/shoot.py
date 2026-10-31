import asyncio, os
from playwright.async_api import async_playwright
H="/workspace/ssm-fx2"; ARGS=["--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=ARGS); errs=[]
        pg=await b.new_page(viewport={"width":1500,"height":900})
        pg.on("console",lambda m: errs.append(f"{m.type}: {m.text}") if m.type in("error","warning") else None)
        pg.on("pageerror",lambda e: errs.append(f"pageerror: {e}"))
        await pg.goto("file://"+H+"/index.html"); await pg.wait_for_function("window.VIEWER_READY===true",timeout=60000)
        await pg.wait_for_timeout(2500); await pg.screenshot(path=H+"/screenshots/60_slug_v0_default_mode1.png")
        await pg.select_option("#mode","3"); await pg.wait_for_timeout(1500); await pg.screenshot(path=H+"/screenshots/61_slug_v0_mode3.png")
        pg2=await b.new_page(viewport={"width":1500,"height":900}); await pg2.goto("file://"+H+"/archive/stratified_sphere/index_rev1.html")
        await pg2.wait_for_function("window.VIEWER_READY===true",timeout=60000); print("archive sphere loads:", await pg2.inner_text("#ver"))
        print("errors:", errs or "none"); await b.close()
asyncio.run(main())
