# Round 6 kickoff — threshold debate, sequencing, peer scoring

**Branch:** `holster-loop-2026-10-19`  
**Team brief (verbatim):** [`prompt.md`](prompt.md)  
**Bundle on origin:** `da37b3c` (docs have advanced since; use current HEAD)  
**Do not push** unless the caller says so. This file is documentation only — it does not run tests or a sweep.

**Round 6 scope:** threshold measure + value (first open question), sequencing recommendations, peer scoring into the ledger, two-gate rules. **No amplitude sweep in this round.**

**Round 7 (not this kickoff):** next milestone after round 6; **purpose TBD** (defined when round 7 is drafted). Sits between the threshold debate and the amplitude sweep.

**Round 8 (not this kickoff):** the **4 W** (`drive_W=1`) amplitude sweep on the rarefied core is kicked off **only after** the threshold is defined by the team and **approved by the human gate (Edger_Equals)**, and after round 7. See §2.

Core geometry remains locked for later rounds (do not re-open here): bubble **0.57295 mm**, wall **1.43463 mm**, tourbillon **9.12441 µm**, fill **0.1044 × ambient** (HHO 2:1), window **1 Hz–50 MHz**.

---

## 1. Pre-flight — full test suite (required)

Per `prompt.md` §5, Claude Code (executor) must confirm the suite is green **before** any ledger entry or local commit for this round. Coordinator / caller should run the same check before declaring round 6 started.

From the repo root (use the project venv if present; otherwise one that has the test deps):

```bash
cd /path/to/sphere-holster
git checkout holster-loop-2026-10-19
git rev-parse --short HEAD   # expect a tip that carries round-6 docs

# Full suite
python -m pytest -q --tb=line
# or, if using the box venv from earlier sessions:
# /tmp/fx2/venv/bin/pytest -q --tb=line
```

**Pass criterion:** last line reports all green, e.g. `178 passed in …` (count may rise if new tests land; record the **actual** pass/fail + count in every ledger entry).

**No-go if:** any failure, collection error, or missing deps. Fix first; do not declare round 6 started.


---

## 1b. Launch — fire the four pings as one job

When the caller says **"send it"** or **"launch round 6,"** the coordinator fires **all four model pings as one job** (same brief, round-6 scope override: threshold / sequencing / peer scoring / gates first; **no sweep**).

**One command (preferred):**

```bash
python scripts/launch_round.py --round-dir reviews/2026-10-19_round6 \
  --prompt reviews/2026-10-19_round6/prompt.md --scope-file <scope-override.txt> --run-dir /tmp/round6-run
```

It writes the shared user text once, fires the four channels below in parallel, and each channel **lands its own reply** in the round folder. With the default `--stage all` it then runs the cross-review stage and closes the round (sequence below). Exit 0 = `ROUND CLOSED` (both gates pass); exit 1 = a gate is `NOT COMPLETE`. `--stage primary` stops after gate 1.

| Model | Channel (each takes `--ping-file F --out <run-dir>/<model> --land-dir reviews/2026-10-19_round6`) |
|---|---|
| **Kimi** | `python scripts/review_kimi.py --ping-file …` |
| **DeepSeek** | `python scripts/review_deepseek.py --ping-file …` |
| **Grok** | `python scripts/review_grok.py --ping-file …` (replaces the ad-hoc `/tmp` `/responses` runner) |
| **Claude** | `python scripts/review_claude.py --ping-file …` (Messages API; replaces the ad-hoc `/tmp` copy of the round-5 `claude_run.py` pattern) |

Prepend the round-6 scope override to the shared user text: **threshold / sequencing / peer scoring / gates first; no sweep this round.**

**Land step (automatic, part of every ping):** with `--land-dir` (or env `REVIEW_LAND_DIR`), each channel writes its reply to `reviews/2026-10-19_round6/{kimi,deepseek,claude,grok}.md` via `scripts/land_review_reply.py` as soon as the ping succeeds (a one-line `<!-- landed: … -->` provenance comment, then the reply verbatim). `ping.json` / stdout / stderr stay in the `/tmp` run dir. A ping whose reply cannot be landed exits non-zero.

**Done = landed.** The run is **not complete** while any reply exists only in `/tmp`. Verify with `python scripts/land_review_reply.py --round-dir reviews/2026-10-19_round6 --check`; to recover an older run without re-firing any API call, use `python scripts/launch_round.py --round-dir reviews/2026-10-19_round6 --run-dir /tmp/round6-run --land-only`. The coordinator **reports back only when all four replies have landed** (checklist item 16).

### Round sequence — four stages, two gates (cannot be skipped)

`scripts/launch_round.py` (default `--stage all`) runs the round in this fixed order:

| Step | Stage | Exit / gate |
|---|---|---|
| (a) | **Fire** — four pings as one job, same brief, each with the current primary `run_id` | — |
| (b) | **Land** — each reply auto-writes `reviews/2026-10-19_round6/{model}.md`, stamped `run_id=… · landed_utc=…` | **Gate 1 — replies landed (COMPLETE):** all four `{model}.md` present **and** stamped with the current primary run (none predates the run start) |
| (c) | **Cross-review** — refuses to start unless gate 1 passes; each model receives the other three current-run replies (with their run ids) and scores them pass/fail | **Gate 2 — cross-review (COMPLETE):** all four `{model}_teamwork.md` present, stamped with the current teamwork run, and that run scored the **current** primary run |
| (d) | **Close** — `launch_round.py --stage close` (also run at the end of `--stage all`) | Round **closes only when gate 1 and gate 2 both pass**; recorded under `closed` in `run.json` |

**Stale-reply guard:** every stage run is recorded in `reviews/2026-10-19_round6/run.json` (`run_id`, `started_utc`; teamwork also records the `primary_run_id` it scored). Landing refuses a reply from another run, one generated before the run started, or one with no stamp/timestamp. `land_review_reply.py --check` (and `--check --suffix _teamwork`) fails with `STALE` for any file that predates the current run. A primary re-fire clears the teamwork run and the close record, so old cross-reviews can never close a re-fired round — re-run `--stage teamwork`, then `--stage close`.

Single stages for recovery: `--stage primary`, `--stage teamwork`, `--stage close`; `--land-only` re-lands from a scratch dir under the same freshness rules.

*Why the guard exists:* tonight's re-fire overwrote `kimi.md`, but the cross-review brief still carried a hand-written note that `kimi.md` was the first-land (round-7) version, so all three peers flagged a discrepancy that the files no longer had. Cross-review now reads freshness from the stamps, not from prose.

*Why this step exists:* the first round-6 launch wrote replies only to `/tmp/round6-run/<model>/` (`--ping` wrote just `ping.json` + the job summary; Grok/Claude ran from ad-hoc `/tmp` scripts writing `reply.md`). Copying into this folder was a manual step, so only `deepseek.md` landed; `kimi.md`, `claude.md`, `grok.md` were landed afterwards from those artifacts. Do not start round 7, the round-8 sweep, or any sweep from this launch.


---

## 2. Round 8 note — 4 W amplitude sweep (deferred)

**Round 6 has no sweep work.** Do not run `drive_W=1` sweeps, single-point drive smokes for kickoff, or write `drive_4W_*.json` / `geometry_drive_4W_sweep_v0.json` as round-6 deliverables.

**Round 7** is the next milestone after round 6 (between threshold debate and the sweep). Its **purpose is TBD** — to be defined when round 7 is drafted. It is **not** the 4 W amplitude sweep.

The **4 W** (`drive_W=1`; 1 W × four domains) amplitude sweep on the rarefied core is **round 8**. It is kicked off **only after**:

1. The team has proposed and peer-scored the automated-gate threshold (measure + value),  
2. The **human gate (Edger_Equals)** has **approved** that threshold, and  
3. Round 7 (purpose TBD) has run or been explicitly waived by Edger_Equals.

Round-8 launch commands, smoke scripts, and sweep artifact paths belong in a future `reviews/…_round8/` kickoff (or an addendum after threshold lock / round 7). Until then, treat any sweep instructions in older drafts of this file or in `prompt.md` Task 1 as **deferred to round 8**.

---

## 3. Four-model role assignment

Give **every** model the same verbatim text from [`prompt.md`](prompt.md), with the round-6 scope override above: **threshold / sequencing / peer scoring / gates first; no sweep this round.** Roles:

| Model | Role this round | How to reach (typical) |
|---|---|---|
| **Kimi** | Cheap rote: units, consistency vs DESIGN_STATE / this kickoff, retired-item scan, JSON / ledger completeness | `python scripts/review_kimi.py --ping "$(cat reviews/2026-10-19_round6/prompt.md)"` (or holster `/kimi-check` / workflow ping) |
| **DeepSeek** | Same cheap filter as Kimi (independent) | `python scripts/review_deepseek.py --ping "$(cat reviews/2026-10-19_round6/prompt.md)"` |
| **Claude (chat)** | Paid / read-only method review; **cross-reviews the other three**; never runs solver or commits | Holster Claude channel / Messages API (see prior `reviews/2026-10-19_round5/claude_run.py` pattern); findings → ledger |
| **Grok** | Paid source / claim cross-check against DESIGN_STATE + kickoff; **cross-reviews the other three** | `python scripts/review_grok.py` with prompt context, or round runner; Tavily pre-search opt-in only if needed |
| **Claude Code CLI** (executor, not a fifth “review voice”) | Runs suite, stages ledger / local commits for round-6 docs; **self-check** before every commit/ledger line; **does not start the round-8 sweep** | Box CLI (`claude`); output gated by caller; **do not push** |

Suggested order for **round 6:** suite green → fan-out threshold + sequencing asks → proposals → peer scores into ledger → human gate settles threshold → **then** round 7 (purpose TBD) → **then** round 8 may start the 4 W sweep.

---

## 4. Where outputs land

| Artifact | Path |
|---|---|
| Team brief | `reviews/2026-10-19_round6/prompt.md` |
| This kickoff | `reviews/2026-10-19_round6/kickoff.md` |
| Per-model replies | `reviews/2026-10-19_round6/{kimi,deepseek,claude,grok}.md` |
| Teamwork scores | `reviews/2026-10-19_round6/*_teamwork.md` |
| Sequencing / threshold debate | e.g. `reviews/2026-10-19_round6/sequencing.md` and/or per-model sections |
| Process recommendations | `reviews/2026-10-19_round6/recommendations.md` (seed for DESIGN_STATE; caller locks) |
| Ledger staging | `ledger/pending/*.jsonl` (CI ingest); never hand-edit `ledger/findings.jsonl` on main outside documented tools |
| Ledger mirror | labelled GitHub issues (`ledger`, `model:<x>`, `sev:<x>`, …) when dial/dispatch allows |
| Sweep / amplitude JSON (**round 8 only**) | repo root `drive_4W_amplitude_v0.json` or `geometry_drive_4W_sweep_v0.json` — **not** round-6 deliverables |

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
2. Their recommendations come back (threshold, sequencing, peer scores).
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

**Status:** threshold definition = **TBD** (team proposes → human gate approves). Round **7** (purpose TBD) and the round **8** sweep wait on that approval.

---

## 5b. Sequencing (threshold first — round 8 sweep is not first)

**Order of operations** (fixed unless the human gate reorders it):

1. **Round 6 — threshold debate.** The team (**Kimi, DeepSeek, Claude, Grok**) debates and proposes the automated-gate threshold (**measure + value**) as their **first open question** (see §5), with peer scoring (§5b below).
2. **Human gate settles the threshold.** **Edger_Equals** makes the **final call** on that definition.
3. **Round 7 — next milestone** after round 6 (between threshold debate and the sweep). **Purpose TBD**; defined when round 7 is drafted.
4. **Round 8 — only then** run the **4 W** (`drive_W=1`) amplitude sweep on the rarefied core (separate kickoff).
5. Prediction checks, both gates, and any feedback fan-out follow the two-gate rules in §5.

The **4 W amplitude sweep is NOT part of round 6** and is **NOT the first step**. Do not start round-8 sweep work until the threshold is settled (or Edger_Equals explicitly waives that hold). Round 7 is a milestone with purpose TBD, not the sweep.

### Team ask — recommendations on this sequencing

Each of the four models should **recommend** whether this order is the next best step:

- Agree with **threshold-debate → human approval → round 7 (TBD) → then round-8 sweep**, with brief reasoning; or
- Propose a **different order**, with brief reasoning (what moves, what waits, and why).

Capture replies under this folder (e.g. in each model’s `.md` or a shared `sequencing.md`). The human gate decides whether to keep or change the order.

### Peer scoring of threshold proposals

After the four models (**Kimi, DeepSeek, Claude, Grok**) propose threshold **measures and values**:

1. Each model **scores the other models’ proposals** — **not its own**.
2. Suggested score axes (adjust if the team agrees): **clarity**, **falsifiability**, and **practicality** (can Claude Code automate the check?).
3. Peer scores are filed into the **existing GitHub review ledger** the same way other findings are scored (append-only JSONL / staging under `ledger/pending/`, labelled issues when mirroring allows; domain `information`).
4. The **human gate (Edger_Equals)** makes the **final call** on the threshold using both the **proposals** and the **peer scores**.

---

## 6. Go / no-go checklist (declare “round 6 started” only if all GO)

| # | Check | GO if… |
|---|---|---|
| 1 | Branch | On `holster-loop-2026-10-19` with round-6 files present (`prompt.md`, this kickoff) |
| 2 | Core geometry | Locked rarefied winner known for later rounds (0.57295 / 1.43463 / 9.12441 µm @ 0.1044× HHO 2:1) — not re-opened in round 6 |
| 3 | Window | `FMIN_HZ=1`, `FMAX_HZ=50e6` recorded for round 8; not a round-6 sweep prerequisite |
| 4 | Full suite | Green; record exact `N passed` |
| 5 | Prompt §5 / self-check | Understood; executor will not commit on red suite |
| 6 | Models | Kimi, DeepSeek, Claude (chat), Grok each have the **same** brief ready (round-6 scope: no sweep) |
| 7 | Outputs | Round-6 paths in §4 agreed; sweep JSON deferred to round 8; no push without caller |
| 8 | Retired | No electrodes / retired items reintroduced in proposals |
| 9 | Ledger | Staging path `ledger/pending/` known; schema / labels understood |
| 10 | Two gates | Automated (Claude Code + threshold TBD) then human (Edger_Equals); both required before team feedback |
| 11 | Threshold | Defined by the team (first open question), **approved by the human gate** (Edger_Equals) |
| 12 | Sequencing | Team recommendations on threshold-first vs alternate order **received** |
| 13 | Peer scores | Peer scores on threshold proposals **recorded in the ledger** |
| 14 | Four pings fired | Kimi, DeepSeek, Claude, Grok pings launched as one job ("send it" / "launch round 6") |
| 15 | Round 8 hold | No 4 W sweep started until threshold is settled; round 7 purpose TBD |
| 16 | Replies landed | All four replies present in this folder: `kimi.md`, `deepseek.md`, `claude.md`, `grok.md` (`land_review_reply.py --check` exits 0). A run **cannot** be marked done with replies only in `/tmp` |
| 17 | Cross-review complete | Gate 2 passes: all four `{model}_teamwork.md` present and stamped with the current teamwork run, which scored the **current** primary run (`land_review_reply.py --check --suffix _teamwork` exits 0); round closes only via `launch_round.py --stage close` with both gates passing. No reply in this folder predates the current run (`--check` reports no `STALE`) |

**NO-GO:** suite red, prompt not shared identically, intent to push without caller, starting the round-8 4 W sweep before threshold approval, declaring the ping run done while any reply is only in `/tmp`, skipping cross-review, scoring or closing on a stale (pre-current-run) reply, or closing the round before both gates pass.

When all rows are GO for **starting** the debate (items 1–10 at minimum; 11–13 complete as the round finishes; 14 = pings fired; 15 held through the round; 16 = all four replies landed before the run counts as done; 17 = cross-review complete before the round closes), the coordinator may declare: **Round 6 started** — models debate threshold / sequencing / peer scores; **round 7 purpose TBD**; **round 8 sweep waits**.
