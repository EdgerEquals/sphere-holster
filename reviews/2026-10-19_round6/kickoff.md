# Round 6 kickoff — 4 W amplitude sweep (drive_W=1)

**Branch:** `holster-loop-2026-10-19`  
**Team brief (verbatim):** [`prompt.md`](prompt.md)  
**Bundle on origin:** `da37b3c`  
**Do not push** unless the caller says so. This file is documentation only — it does not run tests or the sweep.

Core locked for this run (do not re-open): bubble **0.57295 mm**, wall **1.43463 mm**, tourbillon **9.12441 µm**, fill **0.1044 × ambient** (HHO 2:1), window **1 Hz–50 MHz**, drive **`drive_W=1`** (= 1 W × 4 domains = **4 W total**).

---

## 1. Pre-flight — full test suite (required)

Per `prompt.md` §5, Claude Code (executor) must confirm the suite is green **before** any sweep commit or ledger entry. Coordinator / caller should run the same check before declaring the run started.

From the repo root (use the project venv if present; otherwise one that has the test deps):

```bash
cd /path/to/sphere-holster
git checkout holster-loop-2026-10-19
git rev-parse --short HEAD   # expect da37b3c or a descendant that still carries round-6

# Full suite
python -m pytest -q --tb=line
# or, if using the box venv from earlier sessions:
# /tmp/fx2/venv/bin/pytest -q --tb=line
```

**Pass criterion:** last line reports all green, e.g. `178 passed in …` (count may rise if new tests land; record the **actual** pass/fail + count in every ledger entry).

**No-go if:** any failure, collection error, or missing deps. Fix first; do not start the sweep.

Optional drive smoke (does not replace the full suite):

```bash
python -m pytest -q tests/test_drive_1W.py --tb=short
```

---

## 2. Launch the 4 W (drive_W=1) amplitude sweep

There is **no** dedicated `drive_4W_*.py` harness in tree yet. Geometry sweeps (`geometry_sweep_v0.py`, `geometry_fill_sweep_v0.py`) are **no-source** lock searches. Round 6 **creates** the first driven amplitude artifact.

### 2a. Single-point smoke on the rarefied core (executor first step)

```bash
python - <<'PY'
import json
import solver_v0 as S

pre = next(p for p in S.PRESETS if p["id"] == "base5")
# base5 must already be the rarefied winner (0.57295 / 1.43463 / 9.12441 µm @ 0.1044×)
run = S.run_case(pre, {}, drive_W=1.0)
d = run["drive"]
out = {
    "drive_W": d["drive_W"],
    "n_modes_driven": d["n_modes_driven"],
    "P_src_per_mode_W": d["P_src_per_mode_W"],
    "f_Hz_first_last": [d["f_Hz"][0], d["f_Hz"][-1]] if d.get("f_Hz") else None,
    "W_ac_sum_J": d.get("W_ac_sum_J", run.get("W_ac")),
    "P_gas": run["P_gas"],
    "Tss_min_max": [float(min(run["Tss"])), float(max(run["Tss"]))],
    "geometry": {
        "a_mm": pre.get("a") or pre.get("a_mm"),
        "w_mm": pre.get("w") or pre.get("w_mm"),
        "t2_um": pre.get("t2") or pre.get("t2_um"),
        "p_factor": getattr(S, "CORE_P_FACTOR", None) or pre.get("p_factor"),
    },
}
print(json.dumps(out, indent=2))
PY
```

Expect `drive_W == 1.0`, `P_gas == 1.0`, `n_modes_driven > 0`, frequencies inside **1 Hz–50 MHz**.

### 2b. Team sweep deliverable (write new artifact)

Per `prompt.md` Task 1, the team/executor:

1. Agrees the grid (geometry + mix fixed; optional fully-rarefied pressure or envelope grid only).
2. Runs `run_case(..., drive_W=1.0)` (or a thin wrapper script they add) at each point.
3. Writes results to the repo root (or this folder), suggested names:
   - `drive_4W_amplitude_v0.json`, or
   - `geometry_drive_4W_sweep_v0.json`
4. Records best locks, amplitudes / energies, frequencies, pressures, tree commit hash, and exact `drive_W` / acoustic split.
5. Re-runs the **full suite** (§1); only then stages a local commit / ledger entry with `N passed` in the body.

Claude Code CLI is the intended executor for steps 2b–5; chat Claude does **not** run the solver.

---

## 3. Four-model role assignment

Give **every** model the same verbatim text from [`prompt.md`](prompt.md). Roles below match that brief:

| Model | Role this round | How to reach (typical) |
|---|---|---|
| **Kimi** | Cheap rote: units, power bookkeeping (1+1+1+1=4), retired-item scan, DESIGN_STATE consistency, JSON completeness | `python scripts/review_kimi.py --ping "$(cat reviews/2026-10-19_round6/prompt.md)"` (or holster `/kimi-check` / workflow ping with the prompt) |
| **DeepSeek** | Same cheap filter as Kimi (independent) | `python scripts/review_deepseek.py --ping "$(cat reviews/2026-10-19_round6/prompt.md)"` |
| **Claude (chat)** | Paid / read-only physics + method review; **cross-reviews the other three**; never runs solver or commits | Holster Claude channel / Messages API (see prior `reviews/2026-10-19_round5/claude_run.py` pattern); findings → ledger |
| **Grok** | Paid source / claim cross-check against `solver_v0.py` + DESIGN_STATE; **cross-reviews the other three** | `python scripts/review_grok.py` with prompt context, or round runner; Tavily pre-search opt-in only if needed |
| **Claude Code CLI** (executor, not a fifth “review voice”) | Runs suite, sweep, local commits; **self-check** before every commit/ledger line | Box CLI (`claude`); output gated by caller; **do not push** |

Suggested order: suite green → executor smoke (2a) → cheap Kimi/DeepSeek plan check → executor full sweep artifact → Claude + Grok review numbers → all four cross-review + teamwork + recommendations.

---

## 4. Where outputs land

| Artifact | Path |
|---|---|
| Team brief | `reviews/2026-10-19_round6/prompt.md` |
| This kickoff | `reviews/2026-10-19_round6/kickoff.md` |
| Sweep / amplitude JSON | repo root `drive_4W_amplitude_v0.json` or `geometry_drive_4W_sweep_v0.json` (name as team agrees); short human summary also under this folder |
| Per-model replies | `reviews/2026-10-19_round6/{kimi,deepseek,claude,grok}.md` |
| Teamwork scores | `reviews/2026-10-19_round6/*_teamwork.md` |
| Process recommendations | `reviews/2026-10-19_round6/recommendations.md` (seed for DESIGN_STATE; caller locks) |
| Ledger staging | `ledger/pending/*.jsonl` (CI ingest); never hand-edit `ledger/findings.jsonl` on main outside documented tools |
| Ledger mirror | labelled GitHub issues (`ledger`, `model:<x>`, `sev:<x>`, …) when dial/dispatch allows |

Every Claude Code ledger line must include suite **pass/fail + count**.

---

## 5. Two gates (automated → human → then feedback)

There are **two gates** in the loop. Claude Code’s gate is **automated**; the human gate **sits above it**. **Nothing reaches the team without passing both.**

| Gate | Who | Role |
|---|---|---|
| **(1) Automated gate** | **Claude Code** | Runs each recommendation against the model **with a prediction**; holds the **threshold** (deviation from prediction vs confidence score — **TBD**). Packages the prediction-versus-result gap. |
| **(2) Human gate** | **Edger_Equals** | Eyeballs that gap **before** any feedback feeds back to the team. Independent second pair of eyes. |

Order is fixed: fan-out → recommendations → **automated gate** → **human gate** → only then feedback (or surface/stop). Skipping either gate is a no-go.

**Loop shape for round 6:**

1. A kickoff command fans out the same brief to all four models (**Kimi, DeepSeek, Claude, Grok**).
2. Their recommendations come back.
3. **Automated gate — Claude Code:** runs each recommendation against the model **with a prediction**, applies the threshold (**TBD**), and produces the prediction-versus-result package.
4. **Human gate — Edger_Equals:** eyeballs that package **before** any feedback round goes back down to the team.
5. Only after **both** gates pass does feedback fan out (or the result is surfaced upward / stopped per Danny).

### Automated gate (Claude Code)

- Runs the prediction check; holds the threshold dial (deviation vs confidence — see TBD below).
- Claude Code is treated as **one of the four models** in the loop (the Claude side that executes and predicts), so it can be **checking recommendations that include its own**. Passing the automated gate alone is **not** enough to close the loop.

### Human gate (Edger_Equals — required)

After the automated gate, the **prediction-versus-result gap** is presented to **Edger_Equals** for eyeballing **before** any feedback goes back to the team.

- **Nothing feeds back automatically.** No auto-reloop, no silent “team, try again” without Danny’s look.
- Until Edger_Equals signs off (or explicitly chooses “surface only / stop”), the coordinator holds the gap report and does not dispatch a feedback fan-out.
- The human gate is the **independent second pair of eyes** above Claude Code’s automated check.

### Threshold (automated gate) — **TBD** · **first open question for round 6**

Automated-gate escalate criteria are **not locked yet**. This is the team’s **first open question** for the round-6 four-model run (**Kimi, DeepSeek, Claude, Grok**):

- The models should **propose and debate** what the threshold should **measure** (e.g. deviation from prediction, confidence score, or a combo) and what **value** it should take.
- The **human gate (Edger_Equals)** makes the **final call** on any definition the team advances.
- Until that call, treat the dial as unset: **every** prediction-versus-result package still goes to Edger_Equals. **Both gates required** before any team feedback.

Placeholder options to debate:

| Option (TBD) | Idea |
|---|---|
| Deviation from prediction | e.g. relative or absolute gap between predicted and measured lock / amplitude / score exceeds a cut |
| Confidence score | e.g. model-stated confidence below a floor forces surface-to-user even if the gap is small |
| Combo | both: large gap **or** low confidence → must escalate; small gap + high confidence → still must clear the human gate this round until a threshold is chosen |

**Status:** threshold definition = **TBD** (team proposes → human gate approves).


---

## 5b. Sequencing (threshold first — sweep is not first)

**Order of operations for round 6** (fixed unless the human gate reorders it):

1. **Threshold debate first.** The team (**Kimi, DeepSeek, Claude, Grok**) debates and proposes the automated-gate threshold (**measure + value**) as their **first open question** (see §5).
2. **Human gate settles the threshold.** **Edger_Equals** makes the **final call** on that definition.
3. **Only then** run the **4 W** (`drive_W=1`) amplitude sweep on the rarefied core.
4. Prediction checks, both gates, and any feedback fan-out follow the two-gate rules in §5.

The **4 W amplitude sweep is NOT the first step.** Do not start §2 sweep work until the threshold is settled (or Edger_Equals explicitly waives that hold).

### Team ask — recommendations on this sequencing

Each of the four models should **recommend** whether this order is the next best step:

- Agree with **threshold-debate → human approval → then sweep**, with brief reasoning; or
- Propose a **different order**, with brief reasoning (what moves, what waits, and why).

Capture replies under this folder (e.g. in each model’s `.md` or a shared `sequencing.md`). The human gate decides whether to keep or change the order.

### Peer scoring of threshold proposals

After the four models (**Kimi, DeepSeek, Claude, Grok**) propose threshold **measures and values**:

1. Each model **scores the other models’ proposals** — **not its own**.
2. Suggested score axes (adjust if the team agrees): **clarity**, **falsifiability**, and **practicality** (can Claude Code automate the check?).
3. Peer scores are filed into the **existing GitHub review ledger** the same way other findings are scored (append-only JSONL / staging under `ledger/pending/`, labelled issues when mirroring allows; domain `information`).
4. The **human gate (Edger_Equals)** makes the **final call** on the threshold using both the **proposals** and the **peer scores**.


---

## 6. Go / no-go checklist (declare “run started” only if all GO)

| # | Check | GO if… |
|---|---|---|
| 1 | Branch | On `holster-loop-2026-10-19` with round-6 files present (`prompt.md`, this kickoff) |
| 2 | Core geometry | `base5` / CORE_* match rarefied winner (0.57295 / 1.43463 / 9.12441 µm @ 0.1044× HHO 2:1) |
| 3 | Window | `FMIN_HZ=1`, `FMAX_HZ=50e6` in solver |
| 4 | Full suite | Green; record exact `N passed` |
| 5 | Drive API | `run_case(..., drive_W=1)` available; `tests/test_drive_1W.py` part of the green suite |
| 6 | Prompt §5 | Self-check rule understood; executor will not commit on red suite |
| 7 | Models | Kimi, DeepSeek, Claude (chat), Grok each have the **same** `prompt.md` text ready |
| 8 | Outputs | Target paths in §4 agreed; no push planned without caller |
| 9 | Retired | No electrodes / retired items in the planned sweep |
| 10 | Ledger | Staging path `ledger/pending/` known; schema / labels understood |
| 11 | Two gates | Automated (Claude Code + threshold TBD) then human (Edger_Equals); both required before team feedback |
| 12 | Threshold | Defined by the team (first open question), **approved by the human gate** (Edger_Equals) |
| 13 | Sequencing | Team recommendations on threshold-first vs alternate order **received** |
| 14 | Peer scores | Peer scores on threshold proposals **recorded in the ledger** |

**NO-GO:** suite red, wrong geometry, missing `drive_W`, prompt not shared identically, or intent to push without caller.

When all rows are GO, the coordinator may declare: **Round 6 started** — executor begins §2, models stand by for cross-review of verified artifacts.
