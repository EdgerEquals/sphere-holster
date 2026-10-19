"""MCP gateway (#10): protocol handling, tool dispatch, smoke client, hardening config. No Docker, no network."""
import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gateway"))
import ssm_mcp_server as M  # noqa: E402
import mcp_smoke_client as CL  # noqa: E402


def test_initialize_list_and_unknown():
    r = M.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
    assert r["result"]["protocolVersion"] == "2025-06-18" and r["result"]["capabilities"]["tools"] is not None
    assert M.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    names = [t["name"] for t in M.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]]
    assert names == ["list_sim_tools", "fenics_poisson_smoke", "openfoam_cavity_smoke"]
    assert M.handle({"jsonrpc": "2.0", "id": 3, "method": "nope"})["error"]["code"] == -32601
    assert M.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "x"}})["error"]["code"] == -32602


def test_tool_call_runs_smoke_in_tmp_copy(monkeypatch, tmp_path):
    monkeypatch.setattr(M, "SIM_ROOT", ROOT / "sim")
    monkeypatch.setenv("TMPDIR", str(tmp_path)); monkeypatch.setenv("HOME", str(tmp_path / "h"))
    monkeypatch.setattr(M, "available", lambda: {"fenics": True, "openfoam": False})
    seen = []

    def fake_run(cmd, cwd, **kw):
        seen.append((cmd, Path(cwd)))
        out = Path(cwd) / "sim" / "fenics" / "out"; out.mkdir(parents=True); (out / "summary.md").write_text("| PASS |")
        return subprocess.CompletedProcess(cmd, 0, "ok", "")
    r = M.handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "fenics_poisson_smoke"}}, runner=fake_run)
    sc = r["result"]["structuredContent"]
    assert sc["ok"] and "PASS" in sc["summary"] and r["result"]["isError"] is False
    assert seen[0][0] == ["python3", "sim/fenics/smoke_fenics.py"] and str(seen[0][1]).startswith(str(tmp_path))
    r = M.handle({"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "openfoam_cavity_smoke"}})
    assert r["result"]["isError"] is True


def test_serve_loop_and_parse_error():
    out = io.StringIO()
    M.serve(io.StringIO('not json\n{"jsonrpc":"2.0","id":1,"method":"ping"}\n'), out)
    lines = [json.loads(x) for x in out.getvalue().splitlines()]
    assert lines[0]["error"]["code"] == -32700 and lines[1]["result"] == {}


def test_smoke_client_against_real_server_process(tmp_path):
    cmd = [sys.executable, str(ROOT / "gateway" / "ssm_mcp_server.py")]
    rec = CL.session(cmd, "list_sim_tools")
    assert rec["ok"] and rec["server"] == "ssm-sim-gateway" and "fenics_poisson_smoke" in rec["tools"]


def test_gateway_record_goes_into_ledger():
    sys.path.insert(0, str(ROOT / "scripts"))
    import ledger_lib as L
    cfg = L.load_config()
    recs = L.parse_gateway_run({"tool": "fenics_poisson_smoke", "ok": True, "summary": "ok", "started_utc": "2026-10-19T06:00:00Z",
                                "server": "ssm-fenics"}, cfg, "gateway-run-1", "1")
    assert recs[0]["kind"] == "gateway_run" and L.validate(recs[0], L.load_schema()) == []
    assert "mcp-gateway" in (ROOT / ".github/workflows/ledger.yml").read_text()


def test_hardening_flags_everywhere():
    compose = (ROOT / "gateway" / "docker-compose.yml").read_text()
    for s in ("network_mode: none", "read_only: true", 'user: "10001:10001"', "cap_drop: [ALL]", ":ro"):
        assert s in compose
    mcp = json.loads((ROOT / ".cursor" / "mcp.json").read_text())
    for srv in mcp["mcpServers"].values():
        a = " ".join(srv["args"])
        assert "--network none" in a and "--read-only" in a and "--user 10001:10001" in a and ":ro" in a
    wf = (ROOT / ".github/workflows/mcp-gateway.yml").read_text()
    assert "--network none --read-only --user 10001:10001" in wf
    for df in ("Dockerfile.fenics", "Dockerfile.openfoam"):
        t = (ROOT / "gateway" / df).read_text()
        assert "@sha256:" in t and "USER 10001" in t
