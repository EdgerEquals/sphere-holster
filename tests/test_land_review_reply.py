"""Round ping replies land in reviews/<round>/{model}.md; a run with replies only in the scratch dir is NOT complete.
No test here reaches the network (urlopen is replaced; API calls are faked)."""
import json
import os
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


def test_teamwork_land_and_check(tmp_path):
    """Teamwork stage lands {model}_teamwork.md and does not overwrite {model}.md."""
    rnd = tmp_path / "r"
    for m in lr.MODELS:
        lr.land(rnd, m, f"{m} primary")
    assert lr.check(rnd) == []
    assert lr.check(rnd, suffix="_teamwork") == list(lr.MODELS)
    for m in lr.MODELS:
        lr.land(rnd, m, f"{m} scores peers", name=f"{m}_teamwork")
    assert lr.check(rnd, suffix="_teamwork") == []
    assert (rnd / "kimi.md").read_text().endswith("kimi primary\n")
    assert (rnd / "kimi_teamwork.md").read_text().endswith("kimi scores peers\n")
    assert lr.main(["--round-dir", str(rnd), "--check", "--suffix", "_teamwork"]) == 0


def test_launch_teamwork_builds_prompt(tmp_path):
    rnd = tmp_path / "reviews" / "r"
    for m in lr.MODELS:
        lr.land(rnd, m, f"body of {m}\nmentions round {'7' if m == 'kimi' else '8'}")
    prompt = launch_round.build_teamwork_prompt(rnd, "grok")
    assert "You are **Grok**" in prompt
    assert "round 8" in prompt
    assert "kimi.md" in prompt and "round 7" in prompt
    assert "### Kimi" in prompt and "### DeepSeek" in prompt
    assert "body of grok" in prompt  # own reply included
    assert "### Grok" not in prompt.split("## Peer replies")[1]  # not in peer section as heading for self


# --- stale-reply guard -------------------------------------------------------------------------------------------

def _ping_json(path, reply, generated_utc, run_id=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"ok": True, "model": "m", "reply": reply, "generated_utc": generated_utc,
                                "run_id": run_id}))


def test_land_stamps_run_id_and_refuses_stale_reply(tmp_path):
    rnd = tmp_path / "r"
    run = lr.start_run(rnd, "primary")
    dest = lr.land(rnd, "kimi", "fresh", {"generated_utc": lr.now_utc()})
    meta = lr.parse_header(dest.read_text())
    assert meta["run_id"] == run["run_id"] and meta["landed_utc"]
    with pytest.raises(lr.StaleReplyError, match="predates current run"):          # older than the run start
        lr.land(rnd, "deepseek", "old", {"generated_utc": "2026-10-19T00:00:00Z"})
    with pytest.raises(lr.StaleReplyError, match="not the current run"):           # belongs to another run
        lr.land(rnd, "grok", "other", {"generated_utc": lr.now_utc()}, run_id="primary-old")
    with pytest.raises(lr.StaleReplyError, match="cannot prove"):                  # no stamp, no timestamp
        lr.land(rnd, "claude", "unknown")
    assert not (rnd / "deepseek.md").exists() and not (rnd / "grok.md").exists()
    lr.land(rnd, "claude", "launcher-stamped", run_id=run["run_id"])               # explicit current run_id is ok


def test_check_fails_when_reply_predates_current_run(tmp_path, capsys):
    rnd = tmp_path / "r"
    for m in lr.MODELS:                                                            # legacy land, no run.json
        lr.land(rnd, m, f"{m} first land", {"generated_utc": "2026-10-19T14:00:00Z"})
    assert lr.check(rnd) == []                                                     # presence-only (legacy)
    lr.start_run(rnd, "primary")                                                   # re-fire starts
    for m in ("deepseek", "claude", "grok"):
        lr.land(rnd, m, f"{m} refire", {"generated_utc": lr.now_utc()})
    detail = lr.check_detail(rnd)
    assert list(detail) == ["kimi"] and detail["kimi"].startswith("STALE")         # kimi.md still the first land
    assert lr.main(["--round-dir", str(rnd), "--check"]) == 1
    assert "kimi.md (STALE" in capsys.readouterr().err


def test_land_only_refuses_old_scratch_run(tmp_path):
    rnd, old = tmp_path / "r", tmp_path / "old-run"
    _ping_json(old / "kimi" / "ping.json", "old kimi", "2026-10-19T14:00:00Z")
    (old / "grok").mkdir(parents=True)
    (old / "grok" / "reply.md").write_text("old grok")
    os.utime(old / "grok" / "reply.md", (1_000_000_000, 1_000_000_000))           # source mtime long before the run
    lr.start_run(rnd, "primary")
    assert launch_round.main(["--round-dir", str(rnd), "--run-dir", str(old), "--land-only"]) == 1
    assert not (rnd / "kimi.md").exists() and not (rnd / "grok.md").exists()


def test_ping_main_stamps_run_id(tmp_path, monkeypatch):
    rnd, brief = tmp_path / "r", tmp_path / "brief.txt"
    brief.write_text("brief")
    rid = lr.start_run(rnd, "primary")["run_id"]
    monkeypatch.setenv("XAI_API_KEY", "dummy")
    argv = ["--ping-file", str(brief), "--out", str(tmp_path / "out"), "--land-dir", str(rnd), "--run-id", rid]
    assert pc.ping_main("Grok", "grok", "XAI_API_KEY", lambda *a: ("ok", {}, "grok-x"), argv) == 0
    assert lr.parse_header((rnd / "grok.md").read_text())["run_id"] == rid
    assert json.loads((tmp_path / "out" / "ping.json").read_text())["run_id"] == rid
    argv[-1] = "primary-stale"                                                     # wrong run -> not landed, exit 3
    (rnd / "grok.md").unlink()
    assert pc.ping_main("Grok", "grok", "XAI_API_KEY", lambda *a: ("ok", {}, "grok-x"), argv) == 3
    assert not (rnd / "grok.md").exists()


# --- cross-review as an explicit stage ---------------------------------------------------------------------------

def _fake_fire(stage, a, round_dir, run, models, run_id):
    for m in models:
        if stage == "teamwork":
            prompt = launch_round.build_teamwork_prompt(round_dir, m)
            lr.land(round_dir, m, f"{m} scores peers ({len(prompt)} chars)", name=f"{m}_teamwork", run_id=run_id)
        else:
            lr.land(round_dir, m, f"{m} primary", {"generated_utc": lr.now_utc()}, run_id=run_id)


def test_round_sequence_fire_land_crossreview_close(tmp_path, monkeypatch):
    monkeypatch.setattr(launch_round, "_fire", _fake_fire)
    rnd, prompt = tmp_path / "r", tmp_path / "prompt.md"
    prompt.write_text("brief")
    base = ["--round-dir", str(rnd), "--run-dir", str(tmp_path / "run")]
    assert launch_round.main(base + ["--prompt", str(prompt)]) == 0                # default --stage all
    runs = lr.load_runs(rnd)
    assert runs["closed"]["primary_run_id"] == runs["primary"]["run_id"]
    assert runs["teamwork"]["primary_run_id"] == runs["primary"]["run_id"]
    assert all((rnd / f"{m}_teamwork.md").is_file() for m in lr.MODELS)
    # Re-fire primaries only: old cross-reviews no longer count and the round re-opens.
    assert launch_round.main(base + ["--prompt", str(prompt), "--stage", "primary"]) == 0
    assert "closed" not in lr.load_runs(rnd)
    assert launch_round.main(base + ["--stage", "close"]) == 1
    assert sorted(lr.check(rnd, suffix="_teamwork")) == sorted(lr.MODELS)           # all teamwork files stale
    assert launch_round.main(base + ["--stage", "teamwork"]) == 0
    assert launch_round.main(base + ["--stage", "close"]) == 0


def test_crossreview_refuses_stale_primaries(tmp_path, monkeypatch):
    monkeypatch.setattr(launch_round, "_fire", _fake_fire)
    rnd = tmp_path / "r"
    for m in lr.MODELS:
        lr.land(rnd, m, f"{m} first land", {"generated_utc": "2026-10-19T14:00:00Z"})
    lr.start_run(rnd, "primary")
    lr.land(rnd, "kimi", "kimi refire", {"generated_utc": lr.now_utc()})
    with pytest.raises(lr.StaleReplyError, match="primary gate not passed"):
        launch_round.build_teamwork_prompt(rnd, "kimi")
    assert launch_round.main(["--round-dir", str(rnd), "--run-dir", str(tmp_path / "t"), "--stage", "teamwork"]) == 1
    assert not any((rnd / f"{m}_teamwork.md").exists() for m in lr.MODELS)
    assert launch_round.main(["--round-dir", str(rnd), "--run-dir", str(tmp_path / "t"), "--stage", "close"]) == 1
