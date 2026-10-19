#!/usr/bin/env python3
"""Thin MCP server (stdio, JSON-RPC 2.0, one message per line) around the repo's existing sim/ smoke tests (#10).

Runs INSIDE the pinned solver container (gateway/Dockerfile.fenics or Dockerfile.openfoam) with no network, a
read-only root filesystem, a read-only sim/ mount and a tmpfs /tmp. Stdlib only. Every tool copies the sim folder
into /tmp and runs there, so nothing is written outside /tmp.

Tools:
  list_sim_tools          which solver smoke tests this container can run
  fenics_poisson_smoke    DOLFINx Poisson + 1D heat smoke test (sim/fenics/smoke_fenics.py)
  openfoam_cavity_smoke   OpenFOAM icoFoam lid-driven cavity + checks (sim/openfoam/run_cavity.sh, check_cavity.py)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SERVER = {"name": "ssm-sim-gateway", "version": "0.1.0"}
PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"]
SIM_ROOT = Path(os.environ.get("SSM_SIM_ROOT", "/opt/ssm/sim"))
TIMEOUT = int(os.environ.get("SSM_TOOL_TIMEOUT", "900"))

TOOLS = {
    "list_sim_tools": {"description": "List the solver smoke tests available in this gateway container.", "needs": None},
    "fenics_poisson_smoke": {"description": "Run the DOLFINx smoke test: exact P2 Poisson, sin*sin P1 convergence "
                             "rate ~2, 1D steady heat T_max = qL^2/8k. Returns pass/fail and the summary table.",
                             "needs": "fenics"},
    "openfoam_cavity_smoke": {"description": "Run the OpenFOAM icoFoam lid-driven cavity to t = 0.5 s and check "
                              "residuals, continuity and max|U|. Returns pass/fail and the summary table.",
                              "needs": "openfoam"},
}


def available() -> dict:
    av = {"fenics": False, "openfoam": False}
    try:
        import importlib.util
        av["fenics"] = importlib.util.find_spec("dolfinx") is not None
    except Exception:  # noqa: BLE001
        pass
    av["openfoam"] = any(Path(p).exists() for p in ("/usr/lib/openfoam", "/opt/openfoam")) or bool(shutil.which("icoFoam"))
    return av


def run_smoke(kind: str, runner=subprocess.run) -> dict:
    os.makedirs(os.environ.get("HOME") or "/tmp/home", exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"ssm-{kind}-", dir=os.environ.get("TMPDIR", "/tmp")))
    (work / "sim").mkdir()
    shutil.copy2(SIM_ROOT / "summary.py", work / "sim" / "summary.py")
    shutil.copytree(SIM_ROOT / kind, work / "sim" / kind, ignore=shutil.ignore_patterns("out"))
    if kind == "fenics":
        cmds = [["python3", "sim/fenics/smoke_fenics.py"]]
    else:
        cmds = [["bash", "sim/openfoam/run_cavity.sh"], ["python3", "sim/openfoam/check_cavity.py"]]
    t0, log, code = time.time(), [], 0
    for c in cmds:
        p = runner(c, cwd=work, capture_output=True, text=True, timeout=TIMEOUT)
        log.append((p.stdout or "") + (p.stderr or ""))
        code = p.returncode
        if code:
            break
    summary = work / "sim" / kind / "out" / "summary.md"
    return {"ok": code == 0, "exit_code": code, "seconds": round(time.time() - t0, 1),
            "summary": summary.read_text()[:6000] if summary.is_file() else "", "log_tail": "".join(log)[-3000:]}


def call_tool(name: str, args: dict, runner=subprocess.run) -> dict:
    if name not in TOOLS:
        raise KeyError(name)
    if name == "list_sim_tools":
        av = available()
        res = {"available": [n for n, t in TOOLS.items() if t["needs"] and av[t["needs"]]], "solvers": av}
        return {"content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res, "isError": False}
    need = TOOLS[name]["needs"]
    if not available()[need]:
        msg = f"{need} is not installed in this container; use the ssm-{need} gateway service."
        return {"content": [{"type": "text", "text": msg}], "isError": True}
    res = run_smoke(need, runner)
    return {"content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res, "isError": not res["ok"]}


def handle(msg: dict, runner=subprocess.run):
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if mid is None:                       # notification (e.g. notifications/initialized): no reply
        return None
    try:
        if method == "initialize":
            want = params.get("protocolVersion")
            result = {"protocolVersion": want if want in PROTOCOLS else PROTOCOLS[0],
                      "capabilities": {"tools": {"listChanged": False}}, "serverInfo": SERVER}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": [{"name": n, "description": t["description"],
                                 "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}}
                                for n, t in TOOLS.items()]}
        elif method == "tools/call":
            try:
                result = call_tool(params.get("name"), params.get("arguments") or {}, runner)
            except KeyError:
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {params.get('name')}"}}
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    except Exception as e:  # noqa: BLE001
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": f"{type(e).__name__}: {e}"[:500]}}


def serve(stdin=sys.stdin, stdout=sys.stdout):
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            out = handle(msg)
        if out is not None:
            stdout.write(json.dumps(out) + "\n"); stdout.flush()


if __name__ == "__main__":
    serve()
