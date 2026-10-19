import asyncio, sys, json
from playwright.async_api import async_playwright
OUT = "/workspace/grok_thread/sphere_model_v0/screenshots"
async def main():
    import os; os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await b.new_page(viewport={"width": 1500, "height": 900})
        errs = []
        pg.on("console", lambda m: errs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        await pg.goto("file:///workspace/grok_thread/sphere_model_v0/index.html")
        await pg.wait_for_function("window.VIEWER_READY===true", timeout=60000)
        await pg.wait_for_timeout(1500)
        shots = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
        for s in shots:
            await pg.evaluate(s["js"]); await pg.wait_for_timeout(s.get("wait", 900))
            if s.get("el"):
                await pg.locator(s["el"]).screenshot(path=f"{OUT}/{s['name']}.png")
            else:
                await pg.screenshot(path=f"{OUT}/{s['name']}.png")
        print("\n".join(errs) or "no console errors"); print("LASTERR", await pg.evaluate("window.LASTERR||null"), "FRAMES", await pg.evaluate("window.FRAMES"))
        await b.close()
asyncio.run(main())
