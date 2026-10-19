"""Tavily shared search slot: no-key path makes no network call; mocked HTTP response is shaped correctly.
No test here ever reaches the network (urlopen is replaced)."""
import io
import json
import sys
import urllib.request

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "scripts"))
import oai_compat  # noqa: E402
import tavily_search as ts  # noqa: E402


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network call attempted")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_no_key_is_not_configured(tmp_path):
    rc = ts.main(["--query", "PZT-4 sound speed", "--out", str(tmp_path)])
    assert rc == 0
    rec = json.loads((tmp_path / "results.json").read_text())
    assert rec["status"] == "not configured" and rec["results"] == []
    assert "not configured" in (tmp_path / "results.md").read_text()


def test_mocked_response_shape_and_request():
    seen = {}

    def opener(req, timeout):
        seen["url"], seen["auth"] = req.full_url, req.get_header("Authorization")
        seen["body"] = json.loads(req.data.decode())
        return FakeResp(json.dumps({"query": "q", "response_time": 1.2, "usage": {"credits": 1}, "results": [
            {"title": "A", "url": "https://a.example", "content": "alpha  text\n here", "score": 0.9},
            {"title": "B", "url": "https://b.example", "content": "beta", "score": 0.5},
            {"title": "C", "url": "https://c.example", "content": "gamma", "score": 0.1}]}).encode())

    rec = ts.run("q", max_results=2, search_depth="basic", key="tvly-TESTKEY123456", opener=opener)
    assert seen["url"] == "https://api.tavily.com/search"
    assert seen["auth"] == "Bearer tvly-TESTKEY123456"
    assert seen["body"]["query"] == "q" and seen["body"]["max_results"] == 2 and seen["body"]["search_depth"] == "basic"
    assert rec["status"] == "ok" and len(rec["results"]) == 2
    assert rec["results"][0] == {"title": "A", "url": "https://a.example", "snippet": "alpha text here", "score": 0.9}
    md = ts.to_markdown(rec)
    assert "[A](https://a.example)" in md and "tvly-" not in md and "tvly-" not in json.dumps(rec)


def test_error_is_redacted():
    def opener(req, timeout):
        raise RuntimeError("bad Bearer tvly-SECRETSECRET")
    rec = ts.run("q", key="tvly-SECRETSECRET", opener=opener)
    assert rec["status"] == "error" and "SECRETSECRET" not in rec["message"]


def test_rote_context_default_off_and_no_key(tmp_path, monkeypatch):
    # dial default (enabled: false): skipped, nothing written
    assert ts.main(["--rote-context", "--query", "x", "--out", str(tmp_path / "a")]) == 0
    assert not (tmp_path / "a" / "context.md").exists()
    # explicitly on but no key: still exit 0, no network, no context
    assert ts.main(["--rote-context", "--web-search", "true", "--query", "x", "--out", str(tmp_path / "b")]) == 0
    assert not (tmp_path / "b" / "context.md").exists()


def test_rote_context_injected_into_cheap_model_prompt(tmp_path, monkeypatch):
    ctx = tmp_path / "context.md"
    monkeypatch.setenv("TAVILY_CONTEXT_FILE", str(ctx))
    assert oai_compat._web_context() == ""
    ctx.write_text("WEB SEARCH CONTEXT (Tavily) ...")
    assert oai_compat._web_context().startswith("WEB SEARCH CONTEXT")


def test_dial_tavily_default_off():
    d = ts.dial_tavily()
    assert d.get("enabled") is False and d.get("search_depth") == "basic"


# ---- Grok uses Tavily (one pre-search, default on) instead of xAI's built-in web search ----

def _fake_search(calls):
    def fake(query, max_results, search_depth, key, timeout=60, opener=None):
        calls.append((query, max_results, search_depth))
        return {"results": [{"title": "PZT-4 datasheet", "url": "https://src.example/pzt4", "content": "cL ...",
                             "score": 0.8}], "usage": {"credits": 1}}
    return fake


def test_grok_context_default_on_one_search_derived_query(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ts, "search", _fake_search(calls))
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-TESTKEY123456")
    (tmp_path / "intent.txt").write_text("[round 3] acoustic: PZT-4 shell breathing mode\n\nbody")
    (tmp_path / "changed.txt").write_text(".github/workflows/x.yml\nsolver_v0.py\nmodel_data_v0.json\n")
    out = tmp_path / "out"
    assert ts.main(["--grok-context", "--intent-file", str(tmp_path / "intent.txt"),
                    "--changed-files", str(tmp_path / "changed.txt"), "--out", str(out)]) == 0
    assert len(calls) == 1                                        # capped at one search
    q, mr, sd = calls[0]
    assert mr == 5 and sd == "basic"
    assert q == "PZT-4 shell breathing mode solver v0 model data v0"
    ctx = (out / "context.md").read_text()
    assert ctx.startswith("WEB SEARCH CONTEXT") and "https://src.example/pzt4" in ctx and "tvly-" not in ctx


def test_grok_context_explicit_query_and_opt_out(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ts, "search", _fake_search(calls))
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-TESTKEY123456")
    assert ts.main(["--grok-context", "--query", "BTO Curie point", "--out", str(tmp_path / "a")]) == 0
    assert calls[-1][0] == "BTO Curie point"
    assert ts.main(["--grok-context", "--web-search", "false", "--query", "x", "--out", str(tmp_path / "b")]) == 0
    assert len(calls) == 1 and not (tmp_path / "b").exists()


def test_grok_context_no_key_or_failure_never_fails(tmp_path, monkeypatch):
    assert ts.main(["--grok-context", "--query", "x", "--out", str(tmp_path / "a")]) == 0   # no key: no network
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-TESTKEY123456")

    def broken(*a, **k):
        raise TimeoutError("slow")
    monkeypatch.setattr(ts, "search", broken)
    assert ts.main(["--grok-context", "--query", "x", "--out", str(tmp_path / "b")]) == 0
    assert not (tmp_path / "b" / "context.md").exists()


def test_rote_query_turns_search_on_unless_false(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ts, "search", _fake_search(calls))
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-TESTKEY123456")
    assert ts.main(["--rote-context", "--query", "q1", "--out", str(tmp_path / "a")]) == 0
    assert ts.main(["--rote-context", "--web-search", "false", "--query", "q2", "--out", str(tmp_path / "b")]) == 0
    assert ts.main(["--rote-context", "--out", str(tmp_path / "c")]) == 0          # no query, dial off
    assert [c[0] for c in calls] == ["q1"]


def _grok_payload(monkeypatch, cfg_extra, ctx_file=None):
    import review_grok as rg
    seen = {}

    def fake_sse(url, payload, headers, idle_timeout=0, deadline=0):
        seen["url"], seen["payload"] = url, payload
        return [{"type": "response.completed", "response": {"status": "completed", "usage": {}, "output": [
            {"type": "message", "content": [{"type": "output_text", "text": "ok", "annotations": []}]}]}}]
    monkeypatch.setattr(rg.hc, "post_sse", fake_sse)
    if ctx_file:
        monkeypatch.setenv("TAVILY_CONTEXT_FILE", str(ctx_file))
    else:
        monkeypatch.delenv("TAVILY_CONTEXT_FILE", raising=False)
    cfg = {"grok_model": "grok-4.7", "grok_max_tokens": 100, **cfg_extra}
    text, _, _ = rg.call("SYS", "USER", cfg, "xai-test")
    return seen, text


def test_grok_builtin_search_off_by_default_and_tavily_injected(tmp_path, monkeypatch):
    ctx = tmp_path / "context.md"
    ctx.write_text("WEB SEARCH CONTEXT (Tavily) https://src.example/pzt4")
    seen, text = _grok_payload(monkeypatch, {}, ctx)
    p = seen["payload"]
    assert seen["url"].endswith("/responses") and "tools" not in p and "max_turns" not in p and text == "ok"
    sysmsg = p["input"][0]["content"]
    assert sysmsg.startswith("SYS") and "built-in web search tool is off" in sysmsg and "src.example/pzt4" in sysmsg


def test_grok_dial_off_and_builtin_reenable(monkeypatch):
    from harness_common import load_dial
    d = load_dial()
    assert all(lv["grok_web_search"] is False for lv in d["levels"].values())
    assert d["tavily"]["grok_presearch"] is True and d["tavily"]["grok_max_results"] == 5
    seen, _ = _grok_payload(monkeypatch, {"grok_web_search": True, "grok_max_turns": 3})
    assert seen["payload"]["tools"] == [{"type": "web_search"}] and seen["payload"]["max_turns"] == 3
    assert "built-in web search tool is off" not in seen["payload"]["input"][0]["content"]
