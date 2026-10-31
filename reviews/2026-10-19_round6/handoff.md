## Approved (unanimous — all four models)
- sweep blocked to round 8; round 6 is gates/sequencing/peer-scoring only
- no invented thresholds — lock categories later (mode retention, W_n, Q_eff, lock pairs, sharp vs density-guaranteed, Tss, 1+1+1+1=4 W)
- power bookkeeping as hard invariant: 1+1+1+1 = 4 W within a stated tolerance
- CI receipt gate before any driven run
- no push; commit-message bans; DESIGN_STATE-first retired set

## Approved by 3 of 4 (contested — Claude Code may push back)
- Claude's drive_W=1 smoke in CI (bookkeeping only, not the sweep)
- Grok's sequencing table with exit criteria and peer-score pass/fail rubric

## Kimi's numeric tripwires — concept approved, numbers NOT approved
Kimi proposed escalate if: sharp relative error > 0.10; lowest driven ℓ=0 freq drift > 0.05; power bookkeeping vs 4 W > 1×10⁻⁶; confidence not "high".

Caller concern: this model's amplification can be in the millions, so relative-error gates at fixed fractions can fire on noise that doesn't matter or pass small absolute errors that matter enormously at that scale. Rework required: make tripwires scale-aware — gate on absolute error in physical units, or on log-space (fractional) error in log(gain) — so a threshold means the same thing whether the number is 0.001 or 10^6. Keep Kimi's instinct (numeric gates, not vibes); replace the specific scalars.

## Cost-saving option — adopted for round 7+ (caller folded in)
Cross-review pings historically sent each model the other three's full replies as context, which dominates input tokens (round-6 re-fire: Kimi $0.0194, DeepSeek $0.0024, Grok $0.0186, Claude ~$0.026 est; recorded K+D+G $0.0405, ~$0.066 with Claude).

**Adopted default for round 7 protocol design and later rounds:** cross-review context = each peer's **conclusions/scores only**, not full peer replies. Round 6's live launcher (`scripts/launch_round.py`) still injects full replies for e2e continuity; round 7's `protocol.md` (and a future `--teamwork-summary` mode) will specify conclusions-only. See `reviews/2026-10-19_round7/kickoff.md` §4–§5.

## Aim check + improvements (adopted for round 7+)
When the team is asked (round 7 primary replies and later), each model must: (1) state in their own words what they think **our aim** is; (2) recommend any other improvements/suggestions against that aim. Wired into `reviews/2026-10-19_round7/kickoff.md` §4 items 7–8 and checklist item 15.
