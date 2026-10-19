"""Shared result reporting for sim-stack smoke tests.

Each check prints expected vs got, appends a markdown row to
sim/<tool>/out/summary.md (the workflow copies that into
$GITHUB_STEP_SUMMARY), and the script exits non-zero if any check fails.
"""
import os
import sys


class Report:
    def __init__(self, tool, outdir):
        self.tool = tool
        self.outdir = outdir
        os.makedirs(outdir, exist_ok=True)
        self.rows = []
        self.failed = 0

    def check(self, name, expected, got, rel_tol=None, abs_tol=None, ok=None, note=""):
        if ok is None:
            err = abs(got - expected)
            lim = 0.0
            if rel_tol is not None:
                lim = max(lim, rel_tol * abs(expected))
            if abs_tol is not None:
                lim = max(lim, abs_tol)
            ok = err <= lim
            tol = f"|err| {err:.3e} <= {lim:.3e}"
        else:
            tol = note
        status = "PASS" if ok else "FAIL"
        if not ok:
            self.failed += 1
        line = f"[{status}] {self.tool}: {name}: expected {expected!r}, got {got!r} ({tol})"
        print(line, flush=True)
        self.rows.append(f"| {name} | {expected} | {got} | {tol} | **{status}** |")
        return ok

    def finish(self):
        with open(os.path.join(self.outdir, "summary.md"), "w") as f:
            f.write(f"### {self.tool} smoke test\n\n")
            f.write("| check | expected | got | tolerance | status |\n|---|---|---|---|---|\n")
            f.write("\n".join(self.rows) + "\n\n")
            f.write(f"**{self.tool}: {'FAIL' if self.failed else 'PASS'}** "
                    f"({len(self.rows) - self.failed}/{len(self.rows)} checks passed)\n")
        if self.failed:
            print(f"{self.tool}: {self.failed} check(s) FAILED", file=sys.stderr)
            sys.exit(1)
        print(f"{self.tool}: all {len(self.rows)} checks passed")
