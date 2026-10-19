"""Round ping replies land in reviews/<round>/{model}.md; a run with replies only in the scratch dir is NOT complete.
No test here reaches the network (urlopen is replaced; API calls are faked)."""
import json
import sys
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import land_review_reply as lr  # noqa: E402
import launch_round  # noqa: E402
import oai_compat  # noqa: E402
import ping_common as pc  # noqa: E402
import review_kimi  # noqa: E402


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network call attempted")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)


def test_land_extract_check(tmp_path):
    run, rnd = tmp_path / "run", tmp_path / "reviews" / "r"
    (run / "kimi").mkdir(parents=True)
    (run / "kimi" / "ping.json").write_text(json.dumps({"ok": True, "model": "kimi-k2.6", "reply": "kimi says hi",
                                                        "generated_utc": "2026-10-19T00:00:00Z"}))
    (run / "claude").mkdir()
    (run / "claude" / "reply.md").write_text("claude body\n")
    (run / "claude" / "raw.json").write_text(json.dumps({"resp": {"model": "claude-x", "content": []}}))
    assert lr.main(["--round-dir", str(rnd), "--from-run-dir", str(run)]) == 1      # grok/deepseek missing
    assert sorted(lr.check(rnd)) == ["deepseek", "grok"]
    kimi = (rnd / "kimi.md").read_text()
    assert kimi.startswith("<!-- landed: reviewer=kimi") and "model=kimi-k2.6" in kimi and kimi.endswith("kimi says hi\n")
    assert "model=claude-x" in (rnd / "claude.md").read_text()
    for m in ("deepseek", "grok"):
        lr.land(rnd, m, f"{m} body")
    assert lr.main(["--round-dir", str(rnd), "--check"]) == 0
    lr.land(rnd, "kimi", (rnd / "kimi.md").read_text())                              # re-land: one header only
    assert (rnd / "kimi.md").read_text().count("<!-- landed:") == 1


def test_empty_or_failed_reply_not_landed(tmp_path):
    with pytest.raises(ValueError):
        lr.land(tmp_path, "grok", "   ")
    bad = tmp_path / "ping.json"
    bad.write_text(json.dumps({"ok": False, "reply": None, "error": "HTTP 500"}))
    with pytest.raises(ValueError):
        lr.extract(bad)
    (tmp_path / "grok.md").write_text("<!-- landed: reviewer=grok -->\n\n")
    assert "grok" in lr.check(tmp_path)


def test_oai_ping_lands_reply(tmp_path, monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "dummy")
    monkeypatch.setattr(oai_compat, "chat", lambda *a, **k: (
        "pong", {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1, "reasoning_tokens": 0}, "kimi-k2.6", "stop", 0))
    rnd = tmp_path / "reviews" / "r"
    assert oai_compat.ping(review_kimi.KIMI, "ping?", None, tmp_path / "out", str(rnd)) == 0
    assert (rnd / "kimi.md").read_text().endswith("pong\n")
    assert json.loads((tmp_path / "out" / "ping.json").read_text())["landed"].endswith("kimi.md")


def test_ping_main_lands_reply_and_missing_secret_lands_nothing(tmp_path, monkeypatch):
    rnd = tmp_path / "r"
    brief = tmp_path / "brief.txt"
    brief.write_text("brief")
    argv = ["--ping-file", str(brief), "--out", str(tmp_path / "out"), "--land-dir", str(rnd)]
    monkeypatch.setenv("XAI_API_KEY", "dummy")
    assert pc.ping_main("Grok", "grok", "XAI_API_KEY", lambda s, u, c, k: ("grok reply to " + u, {}, "grok-x"), argv) == 0
    assert (rnd / "grok.md").read_text().endswith("grok reply to brief\n")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert pc.ping_main("Claude", "claude", "ANTHROPIC_API_KEY", lambda *a: ("x", {}, "m"), argv) == 2
    assert not (rnd / "claude.md").exists()


def test_launch_land_only_incomplete(tmp_path):
    (tmp_path / "run" / "kimi").mkdir(parents=True)
    (tmp_path / "run" / "kimi" / "reply.md").write_text("only kimi")
    assert launch_round.main(["--round-dir", str(tmp_path / "r"), "--run-dir", str(tmp_path / "run"), "--land-only"]) == 1
