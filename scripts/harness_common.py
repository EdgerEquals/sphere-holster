"""Shared helpers for the information-layer reviewers (stdlib only; PyYAML optional)."""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
PROMPTS = HARNESS / "prompts"
DOMAINS = ["optical", "acoustic", "electric", "magnetic", "thermal", "chemical"]
EXIT_MISSING_SECRET = 2
EXIT_API_ERROR = 3


# ---------- config ----------
def _mini_yaml(text: str):
    """Tiny YAML-subset parser (maps, inline [lists], scalars, comments) used if PyYAML is absent."""
    def scalar(v: str):
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            items, cur, q = [], "", None
            for ch in v[1:-1]:
                if q:
                    if ch == q:
                        q = None
                    else:
                        cur += ch
                elif ch in "\"'":
                    q = ch
                elif ch == ",":
                    items.append(cur.strip()); cur = ""
                else:
                    cur += ch
            if cur.strip():
                items.append(cur.strip())
            return [i.replace("\\\\", "\\") for i in items]
        if v.lower() in ("true", "false"):
            return v.lower() == "true"
        if (v[:1] in "\"'") and v[-1:] == v[:1]:
            return v[1:-1]
        try:
            return int(v)
        except ValueError:
            try:
                return float(v)
            except ValueError:
                return v
    root: dict = {}
    stack = [(-1, root)]
    for raw in text.splitlines():
        line = re.sub(r"\s+#.*$", "", raw) if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if val.strip() == "":
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            parent[key] = scalar(val)
    return root


def load_dial() -> dict:
    text = (HARNESS / "dial.yml").read_text()
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        return _mini_yaml(text)


def level_cfg(dial: dict, depth: str | None) -> tuple[str, dict]:
    depth = (depth or dial.get("default_level") or "shallow").strip().lower()
    if depth not in dial["levels"]:
        sys.exit(f"Unknown depth '{depth}'. Valid: {', '.join(dial['levels'])}")
    return depth, dial["levels"][depth]


def load_retired() -> list[tuple[str, re.Pattern, str]]:
    out = []
    for line in (HARNESS / "retired.txt").read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        label, pat, note = [p.strip() for p in line.split(" | ", 2)]
        out.append((label, re.compile(pat, re.I), note))
    return out


def prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text()


# ---------- git ----------
def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def resolve_range(base: str | None, head: str | None) -> tuple[str, str]:
    head = head or "HEAD"
    if not base:
        parents = git("rev-list", "--parents", "-n", "1", head).split()
        base = parents[1] if len(parents) > 1 else git("hash-object", "-t", "tree", "/dev/null").strip()
    return base, head


def collect_diff(base: str, head: str, max_chars: int) -> dict:
    files = [f for f in git("diff", "--name-only", base, head).splitlines() if f]
    # Skip huge generated artefacts from the prompt (still listed by name).
    skip = re.compile(r"(\.png|\.jpg|\.pdf|\.zip|model_data.*\.json|index\.html)$", re.I)
    text_files = [f for f in files if not skip.search(f)]
    diff = git("diff", "--unified=3", base, head, "--", *text_files) if text_files else ""
    truncated = len(diff) > max_chars
    log = git("log", "--format=%h %s%n%b", f"{base}..{head}") if _is_commit(base) else git("log", "-1", "--format=%h %s%n%b", head)
    return {
        "base": base, "head": head, "head_sha": git("rev-parse", head).strip(),
        "files": files, "skipped_from_prompt": sorted(set(files) - set(text_files)),
        "diff": diff[:max_chars], "diff_truncated": truncated, "diff_chars": len(diff), "log": log.strip(),
    }


def _is_commit(ref: str) -> bool:
    try:
        return git("cat-file", "-t", ref).strip() == "commit"
    except subprocess.CalledProcessError:
        return False


def added_lines(diff: str) -> list[tuple[str, str]]:
    out, cur = [], ""
    for ln in diff.splitlines():
        if ln.startswith("+++ "):
            cur = ln[6:] if ln.startswith("+++ b/") else ln[4:]
        elif ln.startswith("+") and not ln.startswith("+++"):
            out.append((cur, ln[1:]))
    return out


def retired_scan(diff: str) -> list[dict]:
    """Deterministic, free pre-check: retired items appearing in ADDED lines."""
    hits = []
    for label, pat, note in load_retired():
        for f, line in added_lines(diff):
            if f.startswith("harness/") or f in ("AGENTS.md", ".cursor/rules/handoffs.mdc"):
                continue  # the retired list itself lives here
            if pat.search(line):
                hits.append({"label": label, "file": f, "line": line.strip()[:200], "note": note})
    return hits


def detect_domains(dial: dict, d: dict, requested: str) -> list[str]:
    if requested and requested != "auto":
        doms = DOMAINS if requested == "all" else [x.strip() for x in requested.split(",") if x.strip()]
        bad = [x for x in doms if x not in DOMAINS]
        if bad:
            sys.exit(f"Unknown domain(s): {bad}. Valid: {DOMAINS}")
        return doms
    hay = (" ".join(d["files"]) + "\n" + "\n".join(l for _, l in added_lines(d["diff"]))).lower()
    found = []
    for dom, kws in (dial.get("domains") or {}).items():
        if any(re.search(k.lower(), hay) for k in kws):
            found.append(dom)
    return found


# ---------- HTTP ----------
def post_json(url: str, payload: dict, headers: dict, timeout: int = 900) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"content-type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:2000]
        raise RuntimeError(f"HTTP {e.code} from {url}: {body}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error calling {url}: {e.reason}") from None
    except (TimeoutError, OSError) as e:  # socket read timeouts are TimeoutError, not URLError
        raise RuntimeError(f"Timed out / connection error calling {url} after {timeout}s: {e}") from None


def post_sse(url: str, payload: dict, headers: dict, idle_timeout: int = 180, deadline: int = 900):
    """POST with stream=true and parse Server-Sent Events. Returns the list of decoded event dicts.

    idle_timeout: max seconds with no bytes at all (socket read timeout).
    deadline: hard wall-clock limit for the whole stream.
    """
    import time
    req = urllib.request.Request(url, data=json.dumps({**payload, "stream": True}).encode(), method="POST",
                                 headers={"content-type": "application/json", "accept": "text/event-stream", **headers})
    events, t0, data = [], time.monotonic(), []
    try:
        with urllib.request.urlopen(req, timeout=idle_timeout) as r:
            for raw in r:
                if time.monotonic() - t0 > deadline:
                    raise RuntimeError(f"Stream from {url} exceeded the {deadline}s deadline "
                                       f"({len(events)} events received). Lower the dial's reasoning effort / turns.")
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                if line.startswith("data:"):
                    data.append(line[5:].lstrip())
                elif line == "" and data:
                    chunk = "\n".join(data); data = []
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        events.append(json.loads(chunk))
                    except json.JSONDecodeError:
                        pass
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:2000]
        raise RuntimeError(f"HTTP {e.code} from {url}: {body}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error calling {url}: {e.reason}") from None
    except (TimeoutError, OSError) as e:
        raise RuntimeError(f"No data from {url} for {idle_timeout}s ({len(events)} events so far): {e}") from None
    return events


# ---------- verdicts ----------
def parse_verdict(text: str) -> dict:
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    for b in reversed(blocks):
        try:
            v = json.loads(b)
            v["verdict"] = str(v.get("verdict", "")).upper()
            if v["verdict"] in ("PASS", "FAIL"):
                return v
        except json.JSONDecodeError:
            continue
    return {"verdict": "ERROR", "summary": "Reviewer reply had no parseable JSON verdict block.", "findings": []}


def combine(results: list[dict], retired_hits: list[dict]) -> str:
    vs = [r["parsed"]["verdict"] for r in results]
    if retired_hits or "FAIL" in vs:
        return "FAIL"
    if not vs or "ERROR" in vs:
        return "ERROR"
    return "PASS"


def require_secret(name: str, reviewer: str, out_dir: Path, meta: dict) -> str:
    val = os.environ.get(name, "").strip()
    if val:
        return val
    msg = (f"{name} is not set, so the {reviewer} review was skipped. No API call was made and nothing was billed. "
           f"Add it under Settings > Secrets and variables > Actions > New repository secret (name: {name}).")
    write_outputs(out_dir, {**meta, "overall_verdict": "SKIPPED", "error": msg, "results": []}, msg)
    print(f"::error title=Missing secret {name}::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"ERROR: {msg}",
          file=sys.stderr)
    sys.exit(EXIT_MISSING_SECRET)


def write_outputs(out_dir: Path, verdict: dict, markdown: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "verdict.json").write_text(json.dumps(verdict, indent=2))
    (out_dir / "verdict.md").write_text(markdown)
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a") as fh:
            fh.write(markdown + "\n")


def render_md(title: str, v: dict) -> str:
    icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️", "SKIPPED": "⏭️"}.get(v["overall_verdict"], "")
    L = [f"## {icon} {title}: **{v['overall_verdict']}**", "",
         f"Depth `{v['depth']}` · mode `{v['mode']}` · range `{v['base'][:12]}..{v['head_sha'][:12]}` · "
         f"domains: {', '.join(v['domains']) or 'none detected'} · models: {', '.join(sorted({r['model'] for r in v['results']}))}",
         ""]
    if v.get("diff_truncated"):
        L.append(f"> Diff truncated to {v['max_diff_chars']} of {v['diff_chars']} chars for this depth. Use `deep` for more.\n")
    if v["retired_hits"]:
        L.append("### Retired items reintroduced (deterministic scan)")
        L += [f"- **{h['label']}** in `{h['file']}`: `{h['line']}`" for h in v["retired_hits"]]
        L.append("")
    for r in v["results"]:
        p = r["parsed"]
        L.append(f"### {r['scope']} — {p['verdict']}")
        L.append(p.get("summary", ""))
        for f in p.get("findings", [])[:40]:
            L.append(f"- [{f.get('severity','?')}] {f.get('domain','')} `{f.get('file','')}` {f.get('claim','')} — {f.get('note','')}")
        for s in p.get("sources", [])[:40]:
            L.append(f"- source: {s.get('status','?')} — {s.get('claim','')} <{s.get('url','')}> {s.get('note','')}")
        for c in p.get("crosscheck", [])[:40]:
            L.append(f"- cross-check: {c.get('position','?')} — {c.get('other_finding','')} ({c.get('reason','')})")
        if p.get("claims_needing_source_check"):
            L.append("- needs source check: " + "; ".join(p["claims_needing_source_check"][:20]))
        u = r.get("usage", {}) or {}
        extra = ""
        if u.get("cost_in_usd_ticks"):
            extra += f" · cost ${u['cost_in_usd_ticks'] / 1e10:.4f}"
        if u.get("num_server_side_tools_used"):
            extra += f" · server tool calls {u['num_server_side_tools_used']}"
        L.append(f"<sub>tokens in/out: {u.get('input_tokens','?')}/{u.get('output_tokens','?')}{extra}</sub>")
        L.append("")
    L.append(f"<sub>Generated {v['generated_utc']} · JSON in workflow artifact.</sub>")
    return "\n".join(L)


def base_args(desc: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--depth", choices=["shallow", "deep"], default=None, help="granularity dial level")
    ap.add_argument("--base", default=None, help="base ref (default: first parent of head)")
    ap.add_argument("--head", default=None, help="target ref (default: HEAD)")
    ap.add_argument("--domains", default="auto", help="auto | all | comma list")
    ap.add_argument("--mode", choices=["review", "crosscheck"], default="review")
    ap.add_argument("--other-verdict", default=None, help="path to the other reviewer's verdict.json (crosscheck mode)")
    ap.add_argument("--intent", default="", help="PR body / stated intent of the change")
    ap.add_argument("--out", default="review-out", help="output directory")
    return ap


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_user_message(d: dict, intent: str, other: dict | None) -> str:
    parts = [f"Commit range {d['base'][:12]}..{d['head_sha'][:12]}", "", "Commit log:", d["log"] or "(none)", ""]
    if intent:
        parts += ["Stated intent / PR body:", intent[:8000], ""]
    parts += ["Changed files:", *[f"- {f}" for f in d["files"]]]
    if d["skipped_from_prompt"]:
        parts += ["", "Binary/generated files changed but not shown: " + ", ".join(d["skipped_from_prompt"])]
    if d["diff_truncated"]:
        parts += ["", f"NOTE: diff truncated to {len(d['diff'])} of {d['diff_chars']} characters."]
    parts += ["", "Diff:", "```diff", d["diff"] or "(empty)", "```"]
    if other is not None:
        parts += ["", "OTHER REVIEWER'S LATEST VERDICT (JSON):", "```json", json.dumps(other, indent=1)[:40000], "```"]
    return "\n".join(parts)


def system_prompt(scopes: list[str], extra: list[str]) -> str:
    retired = "\n".join(f"- {l}: {n}" for l, _, n in load_retired())
    body = [prompt("_base"), "Retired items:\n" + retired]
    body += [prompt(s) for s in scopes]
    body += extra
    return "\n\n---\n\n".join(body)


def run_review(reviewer: str, secret: str, call) -> None:
    """Generic driver. `call(model, max_tokens, system, user, cfg, key)` -> (text, usage)."""
    ap = base_args(f"{reviewer} reviewer for the stratified-sphere harness")
    a = ap.parse_args()
    out = Path(a.out)
    dial = load_dial()
    depth, cfg = level_cfg(dial, a.depth)
    base, head = resolve_range(a.base, a.head)
    max_chars = int(cfg.get(f"{reviewer.lower()}_max_diff_chars") or cfg["max_diff_chars"])
    cfg = {**cfg, "max_diff_chars": max_chars}
    d = collect_diff(base, head, max_chars)
    hits = retired_scan(d["diff"])
    domains = detect_domains(dial, d, a.domains)
    meta = {"reviewer": reviewer, "depth": depth, "mode": a.mode, "base": base, "head": head,
            "head_sha": d["head_sha"], "files": d["files"], "domains": domains, "retired_hits": hits,
            "diff_truncated": d["diff_truncated"], "diff_chars": d["diff_chars"],
            "max_diff_chars": cfg["max_diff_chars"], "generated_utc": now_utc()}
    key = require_secret(secret, reviewer, out, meta)

    other = None
    if a.mode == "crosscheck":
        if not a.other_verdict or not Path(a.other_verdict).is_file():
            print("WARNING: crosscheck mode but no other verdict file found; running a normal review instead.", file=sys.stderr)
            meta["mode"] = "review (crosscheck requested, other verdict missing)"
        else:
            other = json.loads(Path(a.other_verdict).read_text())
    extra = [prompt("crosscheck")] if other is not None else []
    if reviewer == "Grok":
        extra.append(prompt("_grok_source_check"))

    if cfg.get("per_domain_calls"):
        plan = [("coordinator-merge", ["coordinator-merge"])] + [(dm, [dm]) for dm in domains]
    else:
        plan = [("coordinator-merge + " + (", ".join(domains) or "no domain"), ["coordinator-merge", *domains])]
    plan = plan[: int(cfg.get("max_calls", len(plan)))]

    user = build_user_message(d, a.intent, other)
    results = []
    for scope, scopes in plan:
        sysmsg = system_prompt(scopes, extra)
        try:
            text, usage, model = call(sysmsg, user, cfg, key)
            parsed = parse_verdict(text)
        except Exception as e:  # never crash without writing a verdict
            text, usage, model = f"{type(e).__name__}: {e}", {}, "?"
            parsed = {"verdict": "ERROR", "summary": text[:500], "findings": []}
        results.append({"scope": scope, "model": model, "parsed": parsed, "raw": text, "usage": usage})

    verdict = {**meta, "overall_verdict": combine(results, hits), "results": results}
    md = render_md(f"{reviewer} {'cross-check' if other is not None else 'review'}", verdict)
    write_outputs(out, verdict, md)
    print(md)
    if verdict["overall_verdict"] == "ERROR":
        sys.exit(EXIT_API_ERROR)
