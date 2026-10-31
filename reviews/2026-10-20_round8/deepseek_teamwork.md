<!-- landed: reviewer=deepseek · model=deepseek-v4-pro · channel=scripts/review_deepseek.py --ping · generated_utc=2026-10-20T10:54:33Z · source=/tmp/r8_teamwork_2026-10-20/deepseek/ping.json · run_id=teamwork-20261020T105433Z-2b3358 · landed_utc=2026-10-20T10:57:22Z · finish=stop -->

# DeepSeek — Cross-review scores (Round 8)

I score the four peer replies only. My own reply is context and is not scored. No earlier-round material is used.

## Scoring method

Weights, per the brief:

- **Enforceability — 40%** (script-checkable rules over judgement-reliant rules)
- **Dissent carry-forward — 25%** (visibility/traceability, no quiet drop)
- **Q1 number-rule self-consistency — 20%** (every process count checked against that reply's own Q1 answer)
- **Rig grounding / honesty about what is missing — 15%** (Claude Code's rig items weighted on his code access, not just prose)

Each criterion is 0–10; totals are weighted to a 10-point scale.

---

## Kimi — 9.0 / 10

**Q1 self-consistency.** Kimi allows named parameters with `RESERVED-HUMAN` values and exempts identifiers/gate numbers. I checked the process counts in the reply: `six facts/questions`, `one external search slot`, `three games`, `two gates`, `one pipeline stage/executor/log entry` — all descriptive, structural, or identifier-exempt. The registry collects every parameter. One small tension: `P_HOLD_SCOPE` is given a "proposed default: item+closure" while Q1 says only the human may set values. It is explicitly a proposal, not an operational default, so I treat it as a minor ding, not a violation.

**Enforceability (9.0).** Very high. The Q1 linter is grep-class; dependency closure is graph traversal; dissent dispositions are schema-validated; Q5 skill audit uses script-computable scoring/calibration/specificity measures. Some Q5 diagnostics (specificity, hindsight drift) are only partly mechanical, but the core is scripted.

**Dissent carry-forward (9.5).** Strongest feature. The brief fails to build without the dissent manifest; every reply must file a disposition per open entry or be schema-invalid; status history is append-only; closure requires cause. Silent dropping is structurally impossible, not merely discouraged.

**Rig honesty (8.5).** Uses only the parked harness-context doc and is explicit that six requested facts are `pending_human`; Q7 is parameterised on those facts rather than guessed. Correct behaviour under the question's own "state what is missing" rule.

---

## Claude — 8.6 / 10

**Q1 self-consistency.** Claude allows named parameters, bans invented values, and permits only brief-fixed counts, logical words, and identity. Checked: `eight questions/two gates` (brief-fixed), `seven tests` (enumeration), `one control question` (structural), `rounds-open counter` (measured data, not a cutoff), and all cutoffs are `STALE_FLAG_ROUNDS`, `FALSIFY_ALPHA`, `PLANTED_DEFECT_COUNT`, `TRUST_BATCHES`. Consistent; no bare invented threshold found.

**Enforceability (8.5).** Strong mechanical core: dependencies locked with predictions before results exist, missing dependency data treated as dependent, set-difference-empty check on the register, packet/Markdown match check. Slightly below Kimi because Q5's "gaming through vagueness" leans partly on judging vagueness, and some Q5 tests depend on human-gate outcomes that are deliberately undefined.

**Dissent carry-forward (9.0).** Excellent. Append-only register, "nothing disappears" set-difference rule, closure only by evidence or holder withdrawal, majority vote never closes, all open entries go to the human. The clean-start reconciliation (register goes to human/brief author, not models) is honest and keeps the boundary clean. Slightly below Kimi only because it lacks the schema-level per-reply disposition that makes silence invalid.

**Rig honesty (8.0).** Both rig channels returned `pending_human`; Q7 is conditional and lists exactly what is missing. No overclaiming.

---

## Grok — 9.4 / 10

**Q1 self-consistency.** Grok takes the strictest line: ban invented thresholds entirely, including unset named parameters; only booleans, set equality, and brief-fixed counts. I checked every process count in the reply. `two gates`, `§8 questions`, `the roster` (brief-fixed); `one object per event`, `one JSON object per line`, `one undecidable seal fails` (structural/universal); `more than one candidate` (a logical condition, not a pass line); no quorum, expiry window, score floor, retry limit, or reserved default appears. The reply is unusually clean against its own rule.

**Enforceability (9.5).** The most mechanical design of the four. Falsification is a list of booleans over sealed records, not rates; carry-forward is set equality; holds are transitive closure over declared edges; Q8 measures are all booleans. One small ding: "an item that needs the blocked item but does not declare the edge" requires semantic detection of an undeclared need, which is not a pure graph function. The core scoping rule remains scriptable.

**Dissent carry-forward (9.5).** Append-only event stream with carry events and resolution events; resolution requires a script-evaluable predicate plus evidence, and a resolution by the disputed claim's author without a separate checker does not resolve. Pointers to verbatim text (path + hash), not paraphrase. Traceability is near-total.

**Rig honesty (8.5).** Confines Q7 to what `harness_context` states, names the missing schema/function/attribution facts, and refuses to guess field names. Correct discipline.

---

## Claude Code — 8.7 / 10

**Q1 self-consistency.** Named parameters, values human-reserved, unset fails closed, bare numbers banned, `two gates` structural. Checked: `{dissent_escalate_rounds}`, `{falsify_window_rounds}`, `{min_skill_margin}`, `{safeguard_trial_rounds}`, `{max_self_leniency}` are all unvalued parameters; `exactly one of delivered/held/gaps` is a partition; file/line citations are identifiers, not thresholds. Consistent.

**Enforceability (8.5).** Grounded in actual code: `gate1.py` tamper lock works but comparison is missing; `handoff.py` rule-text coverage is broken; `ledger_lib.py` lacks a Claude Code reviewer identity. Proposed checks (parse check, `RULES`-coverage test, deterministic re-run of `gate1.py` to byte-identical output, set-partition invariant) are all scriptable. Slightly below the top only because Q5's overturn/cost-per-value tests depend on downstream data and named bands rather than pure booleans.

**Dissent carry-forward (8.5).** `dissent.jsonl` with content-hash IDs, positions with file quotes and sha256, `settling_test` (empty allowed as a signal), and scriptable rules: every open ID appears in the next hand-off; no closure without a human or holder `decided_by`; refusal to map to ledger `deferred`/`superseded`. Strong, though it does not force a per-round disposition the way Kimi's schema does.

**Rig grounding (9.5).** As source of record on rig items, his file/line findings carry evidentiary weight, and he is careful to label unread files and open questions. His Q7 is the most concrete of the four because it names the actual scripts and the exact gaps to fix.

---

## Final ranking

| Rank | Reply | Score |
|---|---|---|
| 1 | Grok | **9.4** |
| 2 | Kimi | **9.0** |
| 3 | Claude Code | **8.7** |
| 4 | Claude | **8.6** |

**Basis for the ranking.** Grok tops because the design is almost entirely boolean/set-equality and therefore the most mechanically checkable, while its dissent record is the most traceable. Kimi is close behind on the strength of schema-enforced dissent dispositions and a comprehensive parameter registry. Claude Code places third largely on the evidentiary weight of his rig access and concrete integration gaps. Claude is fourth on the same rubric but remains a strong, internally consistent design; his Q3 and Q8 are among the clearest in the round.
