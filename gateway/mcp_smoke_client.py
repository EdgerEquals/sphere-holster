#!/usr/bin/env python3
"""Minimal MCP stdio client for the gateway smoke test (#10). No LLM involved.

  python gateway/mcp_smoke_client.py --server-name ssm-fenics --call fenics_poisson_smoke --out gateway-out -- \
      docker run --rm -i --network none --read-only --tmpfs /tmp ... ssm-gateway-fenics:ci

Starts the server command, sends initialize -> notifications/initialized -> tools/list -> (optional) tools/call,
checks the replies, and appends a gateway_run record to <out>/gateway_run.json for the ledger (kind gateway_run).
Exit 0 only if every step succeeded.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path


def rpc(proc, mid, method, params=None, timeout=None):
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": mid, "method": method, "params": params or {}}) + "\n")
    proc.stdin.flush()
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError(f"server closed the stream during {method}")
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue                       # ignore stray log lines on stdout
        if msg.get("id") == mid:
            return msg


def session(cmd, call=None, args=None, popen=subprocess.Popen) -> dict:
    proc = popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, text=True, bufsize=1)
    rec = {"steps": []}
    try:
        init = rpc(proc, 1, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                           "clientInfo": {"name": "ssm-smoke", "version": "0.1"}})
        rec["server"] = (init.get("result") or {}).get("serverInfo", {}).get("name")
        rec["steps"].append({"initialize": "result" in init})
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); proc.stdin.flush()
        tl = rpc(proc, 2, "tools/list")
        names = [t["name"] for t in (tl.get("result") or {}).get("tools", [])]
        rec["tools"] = names
        rec["steps"].append({"tools/list": len(names)})
        ok = "result" in init and bool(names)
        summary = f"{len(names)} tools listed"
        if call:
            res = rpc(proc, 3, "tools/call", {"name": call, "arguments": args or {}})
            r = res.get("result") or {}
            ok = ok and "result" in res and not r.get("isError", True)
            sc = r.get("structuredContent") or {}
            rec["steps"].append({"tools/call": call, "isError": r.get("isError"), "error": res.get("error")})
            summary += f"; {call}: {'ok' if ok else 'FAILED'}"
            if sc.get("seconds") is not None:
                summary += f" in {sc['seconds']} s"
            if sc.get("summary"):
                summary += "\n" + sc["summary"][:600]
            elif r.get("content"):
                summary += "\n" + str(r["content"][0].get("text", ""))[:600]
        rec.update(ok=ok, summary=summary, tool=call or "tools/list")
    except Exception as e:  # noqa: BLE001
        rec.update(ok=False, summary=f"{type(e).__name__}: {e}"[:600], tool=call or "tools/list")
    finally:
        try:
            proc.stdin.close(); proc.wait(timeout=30)
        except Exception:  # noqa: BLE001
            proc.kill()
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--server-name", required=True); ap.add_argument("--call", default=None)
    ap.add_argument("--out", default="gateway-out"); ap.add_argument("--allow-fail", action="store_true")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    started = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = session(cmd, a.call)
    rec.update(started_utc=started, server=a.server_name, head_sha=os.environ.get("GITHUB_SHA"))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    f = out / "gateway_run.json"
    runs = json.loads(f.read_text()) if f.is_file() else []
    runs.append(rec)
    f.write_text(json.dumps(runs, indent=2))
    print(json.dumps(rec, indent=2))
    sys.exit(0 if rec["ok"] or a.allow_fail else 1)


if __name__ == "__main__":
    main()
