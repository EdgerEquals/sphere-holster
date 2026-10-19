#!/usr/bin/env python3
"""Run a Python script or module and record which lines of chosen files actually executed (stdlib only).
Used by CI receipt jobs to prove an entrypoint was really called (anti-stub rule).

  python scripts/exec_trace.py --files a.py,b.py --out trace.json [--root DIR] -- script.py [args...]
  python scripts/exec_trace.py --files a.py --out trace.json -- -m pytest -q

Writes {"files": {relpath: [lines]}, "exceptions": {relpath: [ExceptionName, ...]}, "exit_code": n}. The exit
code of the traced program is passed through. Only frames in the chosen files are traced (cheap elsewhere).
"""
from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
import threading
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    root = Path(a.root).resolve()
    targets = {str((root / f).resolve()): f for f in a.files.split(",") if f}
    lines: dict[str, set] = {f: set() for f in targets.values()}
    excs: dict[str, list] = {f: [] for f in targets.values()}

    def local(frame, event, arg):
        rel = targets.get(frame.f_code.co_filename)
        if rel is None:
            return None
        if event == "line":
            lines[rel].add(frame.f_lineno)
        elif event == "exception":
            excs[rel].append(arg[0].__name__)
        return local

    def glob(frame, event, arg):
        if event == "call" and frame.f_code.co_filename in targets:
            return local(frame, event, arg)
        return None

    def write(code):
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps({"files": {k: sorted(v) for k, v in lines.items()},
                                           "exceptions": {k: sorted(set(v)) for k, v in excs.items()},
                                           "exit_code": code}, indent=1))

    code = 0
    sys.settrace(glob); threading.settrace(glob)
    try:
        if cmd[0] == "-m":
            sys.argv = [cmd[1], *cmd[2:]]
            runpy.run_module(cmd[1], run_name="__main__", alter_sys=True)
        else:
            sys.argv = cmd
            script = str(Path(cmd[0]).resolve())
            sys.path.insert(0, str(Path(script).parent))
            runpy.run_path(script, run_name="__main__")
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except BaseException:  # noqa: BLE001
        code = 1
        sys.settrace(None)
        write(code)
        raise
    finally:
        sys.settrace(None); threading.settrace(None)
    write(code)
    sys.exit(code)


if __name__ == "__main__":
    main()
