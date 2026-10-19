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
