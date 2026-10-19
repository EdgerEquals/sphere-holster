<!-- landed: reviewer=claude · model=claude-sonnet-5-5 · channel=ad-hoc /tmp/round6-run/claude_run.py (Messages API; round-5 claude_run.py pattern) · generated_utc=2026-10-19T14:50:50Z · source=/tmp/round6-run/claude/reply.md -->

# Round 6 reply (Claude, chat reviewer, read-only)

I did not read `DESIGN_STATE.md`, the repo, or the solver in this session. Everything below comes from the two pasted documents. All numeric cut values are labelled **[est]** proposals. They are not derived from solver tolerances and need the calibration step in §1.5. I do not use any amplitude, frequency, or lock-count numbers beyond those in the brief, and I did not run a sweep.

---

## 1. Threshold proposal (measure + value)

### 1.1 Principle
The threshold decides **how a package is labelled and what Claude Code recommends** (reloop, surface, or stop). It does **not** let anything skip the human gate. Under §5, every package goes to Edger_Equals regardless. A "green" label means "routine, low priority", never "auto-pass".

### 1.2 Measure: sealed-prediction gap, three classes
A prediction is **sealed** (committed or hashed with a timestamp) before the run. Each prediction carries its observable, a point value, and a stated **80% interval**.

| Class | Observable | Measure | Escalate (RED) if |
|---|---|---|---|
| **A: invariants (binary)** | Power bookkeeping (1+1+1+1 = 4 W), mode count N equals predicted, retired-item scan clean, suite green | Pass/fail | Any fail → **STOP**, not just escalate |
| **B: continuous** | Mode frequencies, W_n, Q_eff, Tss span | z = \|ln(meas/pred)\| / s_i | max z_i > 1 |
| **C: discrete** | Lock-pair set, sharp vs density-guaranteed label per mode | Set or label mismatch | Any mismatch |

Per-observable scales s_i **[est]**:
- Frequency: s = 0.01 (1%).
- Q_eff: s = 0.20.
- W_n: s = ln 2 (a factor of 2).
- Tss span: s = 0.20.

Amber is 0.5 < max z ≤ 1.

### 1.3 Confidence: one-directional only
- A **miss** is a measured value outside the predictor's own stated 80% interval.
- Stated confidence can only **raise** a label, never lower it:
  - Confidence < 0.5 → at least AMBER.
  - A miss at stated confidence ≥ 0.9 → RED.
  - ≥ 2 misses in one package → RED.
- Reason: self-reported confidence from LLMs is poorly calibrated and easy to game. High confidence must never buy a pass.

### 1.4 Combo rule
RED = any Class A fail, any Class C mismatch, max z > 1, or a confidence trigger. AMBER = 0.5 < z ≤ 1, or low confidence. GREEN = everything else.

### 1.5 Calibration and falsifiability (the part that makes it testable)
1. **Backtest before the human gate locks the values.** Run the gate on existing zero-source artifacts. The brief confirms these exist (`geometry_rarefied_hho_sweep_v0.json`, best sharp/mode 0.4127 at 0.1044×). This is a gate dry-run and not a `drive_W=1` sweep, so it is in scope.
2. **Canary test.** Take known-correct predictions and deliberately corrupt them: 2× on W_n, 5% on frequency, a flipped lock label. The gate must flag **100% of the corrupted ones RED** and keep **≥ 90% of the true ones GREEN**. If it fails either, the s_i values are wrong and get revised before approval. This is the explicit falsification criterion for the threshold itself.
3. **Freeze.** Once approved, the s_i values are frozen by commit hash. They cannot be retuned after seeing round-7 results. Any change needs a new human approval.

### 1.6 Independence
The brief says Claude Code may check recommendations that include its own. I recommend an extra rule: **the predictor must not be the model whose recommendation is being tested**, and Claude Code as executor does not author predictions for its own recommendations. Otherwise gate 1 is self-grading and adds little over gate 2.

### 1.7 Practicality
Everything above is computable from the result JSON plus a sealed prediction JSON, with no judgement calls. Claude Code only needs ln(), a set comparison, and an interval check. The output is a fixed-schema gap table that the human reads in one screen.

---

## 2. Sequencing recommendation

**Agree: threshold → human approval → round-7 sweep**, with four amendments:

1. **The threshold is provisional at round 7.** The first sweep doubles as a calibration data point. After it, the human gate may revise the s_i values once, explicitly.
2. **Run the §1.5 backtest and canary tests before approval, not after.** They need only existing artifacts, so this does not violate the "no sweep" hold. It means Edger_Equals approves a threshold with a measured false-flag rate rather than an untested one.
3. **Seal round-7 predictions at the round-7 kickoff**, before the executor runs anything. Prediction-writing is cheap and can be drafted late in round 6, but it must not be revisable after results exist.
4. **Do not reorder to run the sweep first.** The gate exists to judge the sweep. Running it first produces results with no agreed standard for "surprising", and thresholds chosen after seeing data are tuned to the data.

---

## 3. Peer scoring (pending)

I have not seen the other three models' threshold proposals, so there is nothing to score yet. I will not score my own. This is the rubric I will apply:

| Axis | 1 (poor) | 3 (ok) | 5 (strong) |
|---|---|---|---|
| **Clarity** | Measure or value vague ("large gap") | Measure defined, value implicit | Measure, units, and value stated unambiguously |
| **Falsifiability** | No way to show it is wrong | Can be checked after the fact | Stated pass/fail test that could fail the threshold itself (e.g. a canary) |
| **Practicality** | Needs human judgement to compute | Automatable with extra inputs | Claude Code can compute it from existing JSON with no new inputs |

Each score will carry a one-line reason and the domain `information`. I have not verified the ledger schema in `ledger/schema/`, so the staging file format is unconfirmed. I will stage only to `ledger/pending/`, never `findings.jsonl`. Any Claude Code entry must carry the suite result (pass/fail + count).

---

## 4. Issues in the brief (for Kimi/DeepSeek rote check)

| # | Issue | Proposed severity | Domain |
|---|---|---|---|
| 1 | `prompt.md` Tasks 1–4 and the answer shape still demand a sweep, a teamwork score, and a full cross-review, while the kickoff says "no sweep". The kickoff resolves this, but only the pasted scope override makes it unambiguous, so a model reading `prompt.md` alone could run a sweep. | low | information |
| 2 | Role ambiguity: `prompt.md` makes chat Claude read-only and Claude Code the executor. The kickoff §5 calls Claude Code "one of the four models" and the one that predicts. The two-role split (`ea97f75`) should state whether Claude Code authors predictions, and I recommend it does not (§1.6). | medium | information |
| 3 | Checklist rows 11–13 can only be GO after the round runs, while "Round 6 started" requires only rows 1–10. This is internally consistent but worth stating explicitly. | note | information |
| 4 | The threshold TBD names "confidence score" as a measure without defining its source (self-reported vs derived). That is the main way a confidence gate can be gamed (§1.3). | medium | information |

---

## 5. Process recommendations (brief)

1. Add a `predictions/` sealed-file convention (JSON with observable, point value, 80% interval, author model, timestamp or hash) committed before any run.
2. Gate-package schema: one fixed table (observable, predicted, measured, z, class, label) so the human gate reads the same layout every time.
3. Cheap models (Kimi, DeepSeek) own Class A invariant checks. Paid models never redo them.
4. Record every human override (human label differs from automated label) as a ledger `note`. That feeds the s_i recalibration.
5. CI job for the canary test, so threshold regressions are caught automatically after approval.

**Requested from the caller:** the other three proposals, so I can complete peer scoring.
