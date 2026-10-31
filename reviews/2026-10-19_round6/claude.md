<!-- landed: reviewer=claude · model=claude-sonnet-5-5 · channel=scripts/review_claude.py --ping · generated_utc=2026-10-19T15:11:41Z · source=/tmp/round6-refire/claude/ping.json -->

**Scope note:** The Round 6 override applies: threshold, sequencing, peer scoring and gates only. I run no drive_W=1 sweep and produce no `drive_4W_*` artifacts. The amplitude sweep moves to Round 8. This reply is chat-only and read-only. I have not seen the repo, and I cite only what the brief states.

## 1. Sweep

**Blocked by scope override. No sweep run, no numbers produced.** Locked inputs from the brief that I can restate but not verify against files:

| Item | Value | Cited source |
|---|---|---|
| Bubble / wall / tourbillon | 0.57295 mm / 1.43463 mm / 9.12441 µm | `ea694ce`, `2b63111` |
| Fill | 0.1044× ambient, 10 577.3 Pa, HHO 2:1 | `ea694ce` |
| Window | 1 Hz to 50 MHz, N=20000 | `8907777` |
| Prior lock result | best sharp/mode 0.4127 at 0.1044× (zero-source) | `geometry_rarefied_hho_sweep_v0.json` |

Gates to define now so Round 8 can run cleanly:

- **Threshold gate (what counts as a lock under drive):** Fix the definition before the run. The "sharp vs density-guaranteed" criterion and the Q_eff cutoff must be stated up front and taken from `solver_v0.py`. Nobody should tune them after seeing results. I cannot verify the current values, so the executor must quote them from the file.
- **Power gate:** Domain bookkeeping must show 1+1+1+1 = 4 W within a stated tolerance. Acoustic `P_src,n = 1/N` must sum to 1 W across the N bonded l=0 modes, with N reported.
- **Rarefaction gate:** Every pressure factor must be strictly below 1.0× ambient, HHO-only, and logged.
- **Retired-item gate:** No electrodes, so the electric channel stays volumetric ohmic in the BTO film. Gas Q must be derived, not a constant. No single-mode selection.
- **Receipt gate:** Any code touch without a valid CI receipt makes the review a spec review.

## 2. Cross-review

No Kimi, DeepSeek or Grok outputs were included in this prompt, so I have nothing to review. I will not invent findings. Pre-registered review checks, to be applied when their material arrives:

| Target | Check | Proposed domain | Severity if failed |
|---|---|---|---|
| Kimi / DeepSeek (rote) | Power sum = 4 W; retired-item scan; JSON schema complete | information | medium |
| Grok | Claims match `solver_v0.py` and DESIGN_STATE | information, acoustic | high if a lock count is unsupported |
| Executor (Claude Code) | Full test suite pass/fail and count in every ledger entry | information | high if missing |

## 3. Teamwork score

**Partial (provisional).** The structure is sound, with locked inputs, clear roles and a push gate. But this round's override changes the deliverable, and the original brief still asks for sweep artifacts. That conflict is a sequencing hazard. There is nothing yet to credit to any model for catching anything.

## 4. Recommendations

1. **Single-source scope:** When an override supersedes the brief, the coordinator issues a one-line amended deliverables checklist. Here, the `drive_4W_*.json` row should be struck.
2. **Pre-registered thresholds:** Lock criteria and tolerances are written to a file before any driven run, then hashed or committed.
3. **Result JSON ownership:** The executor owns the JSON. Cheap models validate against the schema before paid models review.
4. **Cheap-first sequencing:** Run units, bookkeeping and retired-item scans first. Paid reviewers must not redo them.
5. **Automate a `drive_W=1` smoke test in CI.** It checks that the four channels sum to 4 W and that N modes are carried. It is a smoke test only, not the sweep.
6. **Round 8 grid proposal, to be fixed in advance:** Pressure factors strictly below 1.0 and logged, plus an envelope-frequency grid. Grid points should be set by the team before execution.
7. **Ledger discipline:** Stage findings in `ledger/pending/` only, and include the test count in each entry.
