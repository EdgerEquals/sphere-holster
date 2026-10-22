import os, httpx
from mcp.server.fastmcp import FastMCP
for line in open("/opt/harness/.env"):
    if "=" in line:
        k, v = line.strip().split("=", 1)
        os.environ[k] = v
URL = "https://api.poe.com/v1/chat/completions"
HEAD = {"Authorization": "Bearer " + os.environ["POE_API_KEY"], "User-Agent": "Mozilla/5.0"}
from mcp.server.transport_security import TransportSecuritySettings
# Listen on localhost only; Caddy (HTTPS, secret path) is the only way in from outside.
mcp = FastMCP("harness", host="127.0.0.1", port=8000, transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
async def ask(model, prompt):
    async with httpx.AsyncClient(timeout=300) as c:
        r = await c.post(URL, headers=HEAD, json={"model": model, "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

@mcp.tool()
async def ask_poe(model: str, prompt: str) -> str:
    """Ask one Poe model, e.g. gemini-3.1-pro, deepseek-v4-pro-el, grok-4.7."""
    return await ask(model, prompt)

@mcp.tool()
async def poe_chain(question: str) -> str:
    """Gemini answers, DeepSeek critiques, Qwen writes the final answer."""
    a = await ask("gemini-3.1-pro", question)
    c = await ask("deepseek-v4-pro-el", "Critique this rigorously.\n\nQ: " + question + "\n\nA: " + a)
    f = await ask("qwen3.5-397b-a17b", "Q: " + question + "\n\nDraft: " + a + "\n\nCritique: " + c + "\n\nWrite the best final answer.")
    return "FINAL:\n" + f + "\n\nCRITIQUE:\n" + c

@mcp.tool()
async def ask_deepseek(prompt: str, model: str = "deepseek-v4-flash") -> str:
    """Ask DeepSeek directly. Default V4 Flash; use deepseek-v4-pro for harder jobs."""
    import os, httpx
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"]},
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

import repo_tools
repo_tools.register(mcp)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
