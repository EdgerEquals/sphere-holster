#!/usr/bin/env python3
"""Review ledger core (issue #7): schema validation, sanitising, dedup hashing, parsers, append-only storage.

Stdlib only. Used by scripts/ledger.py (CLI), scripts/ledger_score.py (#8) and scripts/ledger_costs.py (#9).
Record format: ledger/schema/finding.v1.schema.json. Config: harness/ledger.json.

Storage decision: the ledger lives on main (ledger/findings.jsonl), not a data branch. Reasons are in ledger/README.md:
pushes made with the workflow GITHUB_TOKEN do not trigger other workflows (so no CI or paid-audit churn), the scorer,
cost rollup, tests and Pages read the same tree as the code, and there is no second branch to protect or keep in sync.
Append-only is enforced in code (append_records + verify_append_only) and checked again in CI before every push.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "harness" / "ledger.json"
SCHEMA_PATH = ROOT / "ledger" / "schema" / "finding.v1.schema.json"
SCHEMA_TAG = "ssm-ledger/v1.1"   # v1.1 adds receipt/class kinds + review_class; v1 lines stay valid
REVIEW_CLASSES = ("code-review", "spec-review", "legacy")
REVIEWERS = {"claude": "Claude", "grok": "Grok", "kimi": "Kimi", "deepseek": "DeepSeek"}


def load_config(path: Path | None = None) -> dict:
    return json.loads((path or CONFIG_PATH).read_text(encoding="utf-8"))


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ sanitising
_SECRET_PATTERNS = [
    r"sk-ant-[A-Za-z0-9_\-]{8,}", r"sk-(?:proj-|sp-)?[A-Za-z0-9_\-]{16,}", r"xai-[A-Za-z0-9_\-]{16,}",
    r"tvly-[A-Za-z0-9_\-]{6,}", r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}", r"(?i)bearer\s+[A-Za-z0-9._\-]{12,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    r"(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*['\"]?[A-Za-z0-9._\-]{12,}",
]


def trigger_patterns(cfg: dict) -> list[re.Pattern]:
    """Live trigger patterns rebuilt from config parts (slash commands, at-mentions, bracket tags)."""
    s = cfg["sanitise"]
    slash = "|".join(re.escape(w) for w in s["slash_commands"])
    tags = "|".join(re.escape(w) for w in s["bracket_tags"])
    return [re.compile("/" + "(" + slash + r")\b", re.I),
            re.compile(r"\[\s*(" + tags + r")(\s*\d+)?\s*\]", re.I),
            re.compile(r"@([A-Za-z0-9][A-Za-z0-9_\-]*)")]


def contains_trigger(text: str, cfg: dict) -> bool:
    return any(p.search(text or "") for p in trigger_patterns(cfg))


def injection_flags(text: str, cfg: dict) -> list[str]:
    t = (text or "").lower()
    return sorted({p for p in cfg["sanitise"]["injection_phrases"] if re.search(p, t)})


def sanitise(text, cfg: dict, limit: int | None = None) -> str:
    """Make reviewer text safe to store and to post: no secrets, no live triggers or mentions, no HTML/markdown
    tricks, bounded length. Reviewer text is data, never instructions."""
    t = "" if text is None else str(text)
    for pat in _SECRET_PATTERNS:
        t = re.sub(pat, "[redacted]", t)
    t = re.sub(r"<!--[\s\S]*?-->", "", t)                    # hidden HTML comments
    t = re.sub(r"<[^>\n]{1,200}>", "", t)                      # HTML tags
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"(image: \1)", t)   # images (tracking pixels)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r"\1 <\2>", t)  # make link targets visible
    t = t.replace("```", "'''")
    slash_p, tag_p, at_p = trigger_patterns(cfg)
    t = slash_p.sub(lambda m: m.group(1), t)                   # drop the slash: command name stays readable
    t = tag_p.sub(lambda m: "(" + m.group(1) + (m.group(2) or "") + ")", t)
    t = at_p.sub(lambda m: m.group(1), t)                      # drop the at-sign: no mentions, no bot wake-ups
    t = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069]", "", t)  # zero-width / bidi controls
    t = re.sub(r"[ \t]+", " ", t).strip()
    lim = limit or int(cfg["sanitise"]["max_text_chars"])
    return t if len(t) <= lim else t[: lim - 1] + "…"


# ------------------------------------------------------------------ hashing / records
def _norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def dedup_hash(*parts) -> str:
    return hashlib.sha256("\x1f".join(_norm(p) for p in parts).encode()).hexdigest()


def normalise_severity(sev, cfg: dict) -> str:
    s = _norm(sev)
    s = cfg["severity_aliases"].get(s, s)
    return s if s in cfg["severity_order"] else "note"


def severity_rank(sev: str, cfg: dict) -> int:
    return cfg["severity_order"].index(normalise_severity(sev, cfg))


def make_finding(cfg, *, reviewer, model, severity, domain, file, claim, note, source, verdict=None, event_utc=None,
                 salt: str = "") -> dict:
    raw = f"{claim}\n{note}"
    claim_s, note_s = sanitise(claim, cfg, 600), sanitise(note, cfg)
    h = dedup_hash("finding", reviewer, domain, file, claim_s, salt)  # salt: planted runs stay distinct per run
    return {"schema": SCHEMA_TAG, "kind": "finding", "id": h[:16], "hash": h, "recorded_utc": now_utc(),
            "event_utc": event_utc, "source": source, "reviewer": reviewer, "model": model,
            "severity": normalise_severity(severity, cfg), "domain": sanitise(domain or "general", cfg, 60),
            "file": sanitise(file or "", cfg, 200), "claim": claim_s, "note": note_s,
            "review_verdict": verdict, "injection_flags": injection_flags(raw, cfg), "status": "open"}


def price_for(cfg, model: str | None):
    pr = cfg["prices_usd_per_mtok"]
    if not model:
        return None
    return next((v for k, v in sorted(pr.items(), key=lambda kv: -len(kv[0])) if not k.startswith("_") and model.startswith(k)), None)


def deepseek_offpeak(when_iso: str | None) -> bool:
    if not when_iso:
        return False
    t = _dt.datetime.fromisoformat(when_iso.replace("Z", "+00:00")).astimezone(_dt.timezone.utc)
    return not (t.weekday() < 5 and (1 <= t.hour < 4 or 6 <= t.hour < 10))


def compute_cost(cfg, model, tokens: dict, when_iso=None):
    p = price_for(cfg, model)
    if p is None:
        return None, f"unknown: no price on file for {model}"
    cached, cw = tokens.get("cached") or 0, tokens.get("cache_write") or 0
    miss = max((tokens.get("input") or 0) - cached - cw, 0)
    c = (miss * p["in"] + cached * p["cached"] + cw * p.get("cache_write", p["in"]) + (tokens.get("output") or 0) * p["out"]) / 1e6
    note = "computed from harness/ledger.json prices"
    if "offpeak_factor" in p and deepseek_offpeak(when_iso):
        c *= p["offpeak_factor"]; note += " (off-peak)"
    return round(c, 6), note


def make_cost(cfg, *, reviewer, model, tokens, source, cost_usd=None, cost_basis=None, event_utc=None) -> dict:
    if cost_usd is None:
        cost_usd, cost_basis = compute_cost(cfg, model, tokens, event_utc)
    h = dedup_hash("cost", reviewer, source.get("type"), source.get("ref"), source.get("run_id"), source.get("scope"), model)
    return {"schema": SCHEMA_TAG, "kind": "cost", "id": h[:16], "hash": h, "recorded_utc": now_utc(),
            "event_utc": event_utc, "source": source, "reviewer": reviewer, "model": model,
            "tokens": {k: tokens.get(k) for k in ("input", "cached", "cache_write", "output", "reasoning")},
            "cost_usd": None if cost_usd is None else round(float(cost_usd), 6), "cost_basis": cost_basis or "reported"}


def make_status(finding_id: str, status: str, source: dict, issue_number=None) -> dict:
    h = dedup_hash("status", finding_id, status, source.get("ref"))
    return {"schema": SCHEMA_TAG, "kind": "status", "id": h[:16], "hash": h, "recorded_utc": now_utc(),
            "source": source, "finding_id": finding_id, "status": status, "issue_number": issue_number}


def make_mirror(finding_id: str, issue_number: int, source: dict) -> dict:
    h = dedup_hash("mirror", finding_id, issue_number)
    return {"schema": SCHEMA_TAG, "kind": "mirror", "id": h[:16], "hash": h, "recorded_utc": now_utc(),
            "source": source, "finding_id": finding_id, "issue_number": int(issue_number)}


# ------------------------------------------------------------------ usage normalisation
def tokens_from_usage(u: dict) -> dict:
    """Anthropic / xAI responses / OpenAI-compatible / oai_compat-normalised usage -> ledger tokens."""
    u = u or {}
    if "cache_creation_input_tokens" in u or "cache_read_input_tokens" in u:     # Anthropic
        cr, cw = u.get("cache_read_input_tokens") or 0, u.get("cache_creation_input_tokens") or 0
        return {"input": (u.get("input_tokens") or 0) + cr + cw, "cached": cr, "cache_write": cw,
                "output": u.get("output_tokens") or 0,
                "reasoning": (u.get("output_tokens_details") or {}).get("thinking_tokens")}
    if "cached_input_tokens" in u:                                               # oai_compat.normalise_usage
        return {"input": u.get("input_tokens") or 0, "cached": u.get("cached_input_tokens") or 0, "cache_write": 0,
                "output": u.get("output_tokens") or 0, "reasoning": u.get("reasoning_tokens")}
    if "prompt_tokens" in u:                                                     # raw OpenAI-compatible
        cached = u.get("prompt_cache_hit_tokens") or (u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
        return {"input": u.get("prompt_tokens") or 0, "cached": cached, "cache_write": 0,
                "output": u.get("completion_tokens") or 0,
                "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens")}
    return {"input": u.get("input_tokens") or 0,                                 # xAI responses
            "cached": (u.get("input_tokens_details") or {}).get("cached_tokens") or 0, "cache_write": 0,
            "output": u.get("output_tokens") or 0,
            "reasoning": (u.get("output_tokens_details") or {}).get("reasoning_tokens")}


def reported_cost(u: dict):
    u = u or {}
    if u.get("cost_usd") is not None:
        return float(u["cost_usd"])
    if u.get("cost_in_usd_ticks"):
        return u["cost_in_usd_ticks"] / 1e10
    return None


# ------------------------------------------------------------------ parsers
def parse_verdict_json(v: dict, cfg: dict, ref: str, run_id: str | None = None, source_type: str = "verdict_artifact",
                       salt: str = "") -> list[dict]:
    """A harness verdict.json (claude/grok via harness_common, kimi/deepseek via oai_compat) -> records."""
    reviewer = REVIEWERS.get(str(v.get("reviewer", "")).lower(), v.get("reviewer") or "Cursor")
    head = v.get("head_sha")
    when = v.get("generated_utc")
    out = []
    for r in v.get("results") or []:
        src = {"type": source_type, "ref": ref, "run_id": run_id, "head_sha": head, "scope": r.get("scope")}
        p = r.get("parsed") or {}
        verdict = (p.get("verdict") or v.get("overall_verdict") or None)
        verdict = verdict if verdict in ("PASS", "FAIL", "ERROR", "SKIPPED") else None
        for f in p.get("findings") or []:
            if not isinstance(f, dict):
                continue
            out.append(make_finding(cfg, reviewer=reviewer, model=r.get("model"), severity=f.get("severity"),
                                    domain=f.get("domain"), file=f.get("file"), claim=f.get("claim"), note=f.get("note"),
                                    source=src, verdict=verdict, event_utc=when, salt=salt))
        for label in p.get("retired_reintroduced") or []:
            out.append(make_finding(cfg, reviewer=reviewer, model=r.get("model"), severity="blocker", domain="retired",
                                    file="", claim=f"retired item reintroduced: {label}", note="", source=src,
                                    verdict=verdict, event_utc=when, salt=salt))
        u = r.get("usage") or {}
        if u:
            main = u.get("main") if isinstance(u.get("main"), dict) else None
            toks = tokens_from_usage(u if not main else {**main, "input_tokens": u.get("input_tokens"),
                                                          "output_tokens": u.get("output_tokens")})
            out.append(make_cost(cfg, reviewer=reviewer, model=r.get("model"), tokens=toks, source=src,
                                 cost_usd=reported_cost(u), event_utc=when))
    return out


def parse_ping_json(p: dict, cfg: dict, ref: str, run_id=None) -> list[dict]:
    reviewer = REVIEWERS.get(str(p.get("reviewer", "")).lower(), p.get("reviewer") or "Cursor")
    u = p.get("usage") or {}
    src = {"type": "ping_artifact", "ref": ref, "run_id": run_id, "head_sha": None, "scope": "ping"}
    return [make_cost(cfg, reviewer=reviewer, model=p.get("model") or p.get("model_requested"),
                      tokens=tokens_from_usage(u), source=src, cost_usd=reported_cost(u),
                      event_utc=p.get("generated_utc"))]


def parse_tavily_json(recs, ref: str, cfg: dict) -> list[dict]:
    recs = recs if isinstance(recs, list) else [recs]
    out = []
    for i, r in enumerate(recs):
        if r.get("status") != "ok":
            continue
        src = {"type": "review_round", "ref": ref, "run_id": None, "head_sha": None, "scope": f"search {i + 1}"}
        rec = make_cost(cfg, reviewer="Tavily", model="tavily-" + r.get("search_depth", "basic"),
                        tokens={}, source=src, cost_usd=0.0, cost_basis="free plan credits",
                        event_utc=r.get("generated_utc"))
        rec["credits"] = float(r.get("credits") or 1)
        out.append(rec)
    return out


_BULLET = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+\*\*(.+?)\*\*[:.]?\s*(.*)$")


def findings_from_prose(text: str) -> list[tuple[str, str]]:
    """Bold-led bullets ('- **Claim.** detail' or '1. **Claim** detail') -> (claim, note). Round replies are prose."""
    out = []
    for line in (text or "").splitlines():
        m = _BULLET.match(line)
        if m and len(m.group(1)) > 8:
            out.append((m.group(1).strip().rstrip(".:"), m.group(2).strip()))
    return out


def parse_review_round(folder: Path, cfg: dict) -> list[dict]:
    """reviews/<date>_roundN/results.json (+ tavily_results.json) -> finding/cost records (severity note)."""
    folder = Path(folder)
    rel = str(folder.relative_to(ROOT)) if folder.is_relative_to(ROOT) else str(folder)
    data = json.loads((folder / "results.json").read_text(encoding="utf-8"))
    out = []
    for name in ("Claude", "Grok", "Kimi", "DeepSeek"):
        attempts = data.get(name)
        if not isinstance(attempts, list):
            continue
        for i, a in enumerate(attempts):
            src = {"type": "review_round", "ref": rel, "run_id": None, "head_sha": None, "scope": f"{name} attempt {i + 1}"}
            toks = {"input": a.get("input"), "cached": a.get("cached") or 0, "cache_write": 0,
                    "output": a.get("output"), "reasoning": a.get("reasoning")}
            rec = make_cost(cfg, reviewer=name, model=a.get("model"), tokens=toks, source=src,
                            cost_usd=a.get("cost_usd"), cost_basis="reported by round runner (list prices)",
                            event_utc=a.get("started_utc"))
            out.append(rec)
        final = attempts[-1]
        text = final.get("text") or ""
        m = re.search(r"VERDICT:\s*(PASS|FAIL)", text)
        verdict = m.group(1) if m else None
        src = {"type": "review_round", "ref": rel, "run_id": None, "head_sha": None, "scope": name}
        head = re.search(r"^\W*(SOLUTION|TOP)\W*:\s*(.+)$", text, re.M | re.I)
        points = ([(f"{head.group(1).upper()}: {head.group(2).strip().strip('*')}", "headline answer")] if head else [])
        for claim, note in points + findings_from_prose(text):
            out.append(make_finding(cfg, reviewer=name, model=final.get("model"), severity="note",
                                    domain="holster" if "round1" not in rel else "design", file=rel,
                                    claim=claim, note=note, source=src, verdict=verdict,
                                    event_utc=final.get("started_utc")))
    if (folder / "tavily_results.json").is_file():
        out += parse_tavily_json(json.loads((folder / "tavily_results.json").read_text()), rel, cfg)
    return out


def parse_gateway_run(g: dict, cfg: dict, ref: str, run_id=None) -> list[dict]:
    h = dedup_hash("gateway_run", ref, g.get("tool"), g.get("started_utc"))
    return [{"schema": SCHEMA_TAG, "kind": "gateway_run", "id": h[:16], "hash": h, "recorded_utc": now_utc(),
             "event_utc": g.get("started_utc"),
             "source": {"type": "gateway", "ref": ref, "run_id": run_id, "head_sha": g.get("head_sha"), "scope": g.get("server")},
             "reviewer": "Gateway", "tool": sanitise(g.get("tool"), cfg, 120), "ok": bool(g.get("ok")),
             "summary": sanitise(g.get("summary"), cfg, 800)}]


# ------------------------------------------------------------------ receipts + review class (v1.1, round 4)
class ReceiptRefused(Exception):
    pass


def make_receipt(evidence: dict, digest: str, attestation: str, ref: str, run_id=None) -> dict:
    h = dedup_hash("receipt", evidence.get("component"), evidence.get("head_sha"), digest)
    return {"schema": SCHEMA_TAG, "kind": "receipt", "id": h[:16], "hash": h, "recorded_utc": now_utc(),
            "event_utc": evidence.get("generated_utc"),
            "source": {"type": "receipt_artifact", "ref": ref, "run_id": str(run_id or evidence.get("run_id")),
                       "head_sha": evidence.get("head_sha"), "scope": evidence.get("job")},
            "reviewer": "Gateway" if evidence.get("component") == "mcp-gateway" else "Cursor",
            "component": evidence.get("component"), "artifact_digest": digest, "attestation": attestation[:300],
            "target_files": list(evidence.get("files") or []), "evidence": evidence, "ok": evidence.get("result") == "pass",
            "summary": f"{evidence.get('component')} at {str(evidence.get('head_sha'))[:12]}: "
                       f"{evidence.get('numeric_checks')} numeric checks pass, run {evidence.get('run_url')}"}


def accept_receipt(evidence_bytes: bytes, ref: str, run_meta: dict | None, verifier=None, env=os.environ) -> dict:
    """Turn an uploaded receipt into a ledger record, or raise ReceiptRefused. CI-only: needs GITHUB_ACTIONS, the
    producing run's metadata (workflow path, head sha, run id from the workflow_run event / API) and a signature
    verifier. There is no local write path: called outside Actions it always refuses."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import receipt as R  # local import: receipt.py imports nothing from here
    if env.get("GITHUB_ACTIONS") != "true" or not run_meta or verifier is None:
        raise ReceiptRefused("receipt ingest runs only inside the ledger workflow (no local/Cursor/reviewer write path)")
    ev = json.loads(evidence_bytes)
    if R.canonical(ev) != evidence_bytes.strip():
        raise ReceiptRefused("evidence.json is not in canonical form (edited after CI wrote it)")
    for k_ev, k_run in (("workflow", "workflow_path"), ("head_sha", "head_sha"), ("run_id", "run_id")):
        if str(ev.get(k_ev)) != str(run_meta.get(k_run)):
            raise ReceiptRefused(f"evidence {k_ev}={ev.get(k_ev)} does not match the producing run ({run_meta.get(k_run)})")
    res = R.verify_receipt(ev, R.digest(evidence_bytes.strip()), attest=verifier)
    if not res["ok"]:
        raise ReceiptRefused("; ".join(res["reasons"]))
    return make_receipt(ev, res["digest"], res["attestation"], ref, run_meta.get("run_id"))


def make_class(finding_id: str, review_class: str, why: str) -> dict:
    h = dedup_hash("class", finding_id, review_class)
    return {"schema": SCHEMA_TAG, "kind": "class", "id": h[:16], "hash": h, "recorded_utc": now_utc(),
            "source": {"type": "backfill", "ref": why}, "finding_id": finding_id, "review_class": review_class}


def review_classes(records: list[dict]) -> dict[str, str]:
    """id -> effective review_class for finding and cost records (record field, else class record, else legacy)."""
    out = {r["id"]: r.get("review_class") or "legacy" for r in records if r["kind"] in ("finding", "cost")}
    explicit = {r["id"] for r in records if r["kind"] in ("finding", "cost") and r.get("review_class")}
    for r in records:
        if r["kind"] == "class" and r["finding_id"] in out and r["finding_id"] not in explicit:
            out[r["finding_id"]] = r["review_class"]
    return out


def legacy_backfill(records: list[dict]) -> list[dict]:
    have = {r["finding_id"] for r in records if r["kind"] == "class"}
    return [make_class(r["id"], "legacy", "pre-receipt-gate backfill (no receipt)") for r in records
            if r["kind"] in ("finding", "cost") and not r.get("review_class") and r["id"] not in have]


def parse_artifact_dir(d: Path, cfg: dict, ref: str, run_id=None, run_meta=None, verifier=None, refused=None) -> list[dict]:
    d = Path(d)
    out = []
    rc = None
    rcf = next(iter(sorted(d.rglob("review_class.json"))), None)
    if rcf is not None:
        try:
            rc = json.loads(rcf.read_text(encoding="utf-8")).get("review_class")
        except (json.JSONDecodeError, AttributeError):
            rc = None
        rc = rc if rc in REVIEW_CLASSES else None
    for f in sorted(d.rglob("evidence.json")):
        try:
            out.append(accept_receipt(f.read_bytes(), ref, run_meta, verifier))
        except (ReceiptRefused, json.JSONDecodeError) as e:
            if refused is not None:
                refused.append(f"{f}: {e}")
    for f in sorted(d.rglob("*.json")):
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(obj, (dict, list)):
            continue
        if f.name == "verdict.json":
            out += parse_verdict_json(obj, cfg, ref, run_id)
        elif f.name == "ping.json":
            out += parse_ping_json(obj, cfg, ref, run_id)
        elif f.name == "gateway_run.json":
            for g in (obj if isinstance(obj, list) else [obj]):
                out += parse_gateway_run(g, cfg, ref, run_id)
        elif f.name == "results.json" and isinstance(obj, (dict, list)) and ("tavily" in f.parent.name.lower() or "tavily" in ref.lower()):
            out += parse_tavily_json(obj, ref, cfg)
    if rc:
        for r in out:
            if r["kind"] in ("finding", "cost"):
                r["review_class"] = rc
    return out


# ------------------------------------------------------------------ storage
def read_ledger(path: Path) -> list[dict]:
    path = Path(path)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def dedup(new: list[dict], existing: list[dict]) -> list[dict]:
    seen = {r["id"] for r in existing}
    out = []
    for r in new:
        if r["id"] not in seen:
            seen.add(r["id"]); out.append(r)
    return out


def append_records(path: Path, records: list[dict], schema: dict | None = None, allow_receipts: bool = False) -> list[dict]:
    """Validate, dedup against the file, and append. Never rewrites existing lines. Receipt records are only
    accepted from the verified CI ingest path (allow_receipts=True after accept_receipt)."""
    path = Path(path)
    schema = schema or load_schema()
    if not allow_receipts and any(r.get("kind") == "receipt" for r in records):
        raise ReceiptRefused("receipt records can only be appended by the CI ingest path (accept_receipt)")
    for r in records:
        errs = validate(r, schema)
        if errs:
            raise ValueError(f"record {r.get('id')} fails schema: {errs[:3]}")
    fresh = dedup(records, read_ledger(path))
    if fresh:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            for r in fresh:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    return fresh


def verify_append_only(old_text: str, new_text: str) -> bool:
    return new_text.startswith(old_text) and (not old_text or old_text.endswith("\n"))


# ------------------------------------------------------------------ minimal JSON Schema validator
def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


_TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool,
          "null": type(None)}


def _type_ok(val, t) -> bool:
    ts = t if isinstance(t, list) else [t]
    for x in ts:
        if x in ("integer", "number") and isinstance(val, bool):
            continue
        if isinstance(val, _TYPES[x]):
            return True
    return False


def validate(obj, schema: dict, path: str = "$") -> list[str]:
    """Subset of JSON Schema used by finding.v1: type, required, enum, const, pattern, properties, items, allOf/if/then."""
    errs = []
    if "type" in schema and not _type_ok(obj, schema["type"]):
        return [f"{path}: expected {schema['type']}"]
    if "const" in schema and obj != schema["const"]:
        errs.append(f"{path}: must be {schema['const']!r}")
    if "enum" in schema and obj not in schema["enum"]:
        errs.append(f"{path}: {obj!r} not in enum")
    if "pattern" in schema and isinstance(obj, str) and not re.search(schema["pattern"], obj):
        errs.append(f"{path}: does not match {schema['pattern']}")
    if isinstance(obj, dict):
        for k in schema.get("required", []):
            if k not in obj:
                errs.append(f"{path}: missing {k}")
        for k, sub in (schema.get("properties") or {}).items():
            if k in obj:
                errs += validate(obj[k], sub, f"{path}.{k}")
    if isinstance(obj, list) and "items" in schema:
        for i, it in enumerate(obj):
            errs += validate(it, schema["items"], f"{path}[{i}]")
    for sub in schema.get("allOf", []):
        if "if" in sub:
            if not validate(obj, sub["if"], path):
                errs += validate(obj, sub.get("then", {}), path)
        else:
            errs += validate(obj, sub, path)
    return errs


# ------------------------------------------------------------------ derived views
def current_status(records: list[dict]) -> dict[str, str]:
    st = {r["id"]: r.get("status", "open") for r in records if r["kind"] == "finding"}
    for r in records:
        if r["kind"] == "status" and r["finding_id"] in st:
            st[r["finding_id"]] = r["status"]
    return st


def mirrored(records: list[dict]) -> dict[str, int]:
    return {r["finding_id"]: r["issue_number"] for r in records if r["kind"] == "mirror"}


def ledger_as_of(records: list[dict]) -> str:
    """Deterministic timestamp for derived files (latest record time), so regenerating them without new
    records produces no diff and no commit."""
    return max((r["recorded_utc"] for r in records), default="1970-01-01T00:00:00Z")
