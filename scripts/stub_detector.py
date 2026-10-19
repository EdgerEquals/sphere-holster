#!/usr/bin/env python3
"""Stub detector for execution receipts (anti-stub rule, round 4). Stdlib only.

A receipt may only be issued for an entrypoint that does real work. This flags, by AST:
  - functions whose body (after an optional docstring) is only `pass`, `...`, string expressions,
    `raise NotImplementedError[...]` / `raise NotImplemented`, or a single `return <literal>` (constants,
    None/True/False, or tuples/lists/dicts/sets made only of constants) -- including combinations of these;
  - functions that just return one of their own parameters unchanged (identity shims);
  - module entrypoints (`path.py` with no function) whose top-level code, after the docstring and imports, is
    empty or stub-only.
Entry spec: "path/to/file.py:function" or "path/to/file.py:Class.method" or "path/to/file.py" (module).
Usage: python scripts/stub_detector.py <entry> [<entry> ...]   -> JSON report, exit 1 if any stub.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _is_literal(node) -> bool:
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Name) and node.id in ("None", "True", "False"):
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(_is_literal(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return all(k is None or _is_literal(k) for k in node.keys) and all(_is_literal(v) for v in node.values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return _is_literal(node.operand)
    return False


def _is_notimpl(node) -> bool:
    if not isinstance(node, ast.Raise) or node.exc is None:
        return False
    e = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
    return isinstance(e, ast.Name) and e.id in ("NotImplementedError", "NotImplemented")


def _strip_docstring(body):
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        return body[1:]
    return body


def _trivial_stmt(s) -> bool:
    if isinstance(s, ast.Pass):
        return True
    if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant):      # ... or a bare string
        return True
    if _is_notimpl(s):
        return True
    if isinstance(s, ast.Return) and (s.value is None or _is_literal(s.value)):
        return True
    return False


def function_stub_reason(fn: ast.AST) -> str | None:
    body = _strip_docstring(list(fn.body))
    if not body:
        return "empty body"
    if all(_trivial_stmt(s) for s in body):
        kinds = sorted({type(s).__name__ if not _is_notimpl(s) else "NotImplementedError" for s in body})
        return "stub-only body (" + ", ".join(kinds) + ")"
    params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
    if len(body) == 1 and isinstance(body[0], ast.Return) and isinstance(body[0].value, ast.Name) and body[0].value.id in params:
        return f"identity shim (returns parameter {body[0].value.id!r} unchanged)"
    return None


def module_stub_reason(tree: ast.Module) -> str | None:
    body = [s for s in _strip_docstring(list(tree.body)) if not isinstance(s, (ast.Import, ast.ImportFrom))]
    if not body:
        return "module has no code after imports"
    if all(_trivial_stmt(s) for s in body):
        return "module top level is stub-only"
    return None


def find_function(tree: ast.Module, qual: str):
    node = tree
    for part in qual.split("."):
        node = next((n for n in getattr(node, "body", []) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                     and n.name == part), None)
        if node is None:
            return None
    return node if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else None


def body_lines(fn) -> list[int]:
    """Source lines of the executable body (excluding def line and docstring), for trace coverage."""
    body = _strip_docstring(list(fn.body))
    lines = set()
    for s in body:
        for n in ast.walk(s):
            if hasattr(n, "lineno") and isinstance(n, ast.stmt):
                lines.add(n.lineno)
    return sorted(lines)


def module_lines(tree: ast.Module) -> list[int]:
    lines = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.stmt) and not isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
            lines.add(n.lineno)
    return sorted(lines)


def check_entry(entry: str, root: Path = ROOT, source: str | None = None) -> dict:
    path, _, qual = entry.partition(":")
    src = source if source is not None else (root / path).read_text(encoding="utf-8")
    tree = ast.parse(src)
    if qual:
        fn = find_function(tree, qual)
        if fn is None:
            return {"entry": entry, "stub": True, "reason": "entrypoint not found", "lines": []}
        reason = function_stub_reason(fn)
        return {"entry": entry, "stub": reason is not None, "reason": reason, "lines": body_lines(fn)}
    reason = module_stub_reason(tree)
    return {"entry": entry, "stub": reason is not None, "reason": reason, "lines": module_lines(tree)}


def main(argv=None):
    entries = (argv if argv is not None else sys.argv[1:])
    rep = [check_entry(e) for e in entries]
    print(json.dumps([{k: v for k, v in r.items() if k != "lines"} for r in rep], indent=2))
    sys.exit(1 if any(r["stub"] for r in rep) else 0)


if __name__ == "__main__":
    main()
