"""Collects expected-vs-got rows from the locked-value tests and writes them to the job summary."""
import json
import os
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
ROWS: list[dict] = []


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def locked():
    cfg = yaml.safe_load((ROOT / "harness/locked_values.yml").read_text(encoding="utf-8"))
    for key, v in cfg["values"].items():
        c = v["cite"]
        lines = (ROOT / c["file"]).read_text(encoding="utf-8").splitlines()
        hint = c.get("line")
        order = ([hint - 1] if hint and 0 < hint <= len(lines) else []) + list(range(len(lines)))
        v["found"], v["found_line"] = None, None
        for i in order:
            m = re.search(c["pattern"], lines[i])
            if m:
                v["found"], v["found_line"] = float(m.group(1)), i + 1
                break
    return cfg


@pytest.fixture
def record(request):
    def _rec(check, expected, got, tol, source, ok=None, info=False):
        if ok is None:
            ok = True
        ROWS.append(dict(test=request.node.name, check=check, expected=expected, got=got, tol=tol,
                         source=source, status="INFO" if info else ("PASS" if ok else "FAIL")))
        return ok
    return _rec


def _fmt(x):
    if isinstance(x, float):
        return f"{x:.6g}"
    return str(x)


def pytest_sessionfinish(session, exitstatus):
    if not ROWS:
        return
    icon = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️"}
    md = ["## Engineering tests: locked values (SymPy)", "",
          "| | Check | Expected | Got | Tolerance | Source |", "|---|---|---|---|---|---|"]
    for r in ROWS:
        md.append(f"| {icon[r['status']]} {r['status']} | {r['check']} | {_fmt(r['expected'])} | {_fmt(r['got'])} | "
                  f"{r['tol']} | {r['source']} |")
    fails = [r for r in ROWS if r["status"] == "FAIL"]
    md += ["", f"**{len(fails)} failing check(s).**" if fails else "**All locked-value checks pass.**"]
    text = "\n".join(md) + "\n"
    out = ROOT / "tests" / "out"
    out.mkdir(exist_ok=True)
    (out / "locked_values_report.md").write_text(text, encoding="utf-8")
    (out / "locked_values_report.json").write_text(json.dumps(ROWS, indent=2), encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(text)
    for r in fails:  # GitHub annotations: visible on the run page without opening logs
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"\n::error title=Locked value mismatch: {r['check']}::expected {_fmt(r['expected'])}, "
                  f"got {_fmt(r['got'])} (tol {r['tol']}; {r['source']})")
