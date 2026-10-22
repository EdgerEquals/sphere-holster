<!-- landed: reviewer=claude_code · model=claude-opus-5-5 · channel=scripts/review_claude_code.py --ping · generated_utc=2026-10-20T10:35:05Z · source=/tmp/r8_fire_2026-10-20/claude_code/ping.json · run_id=primary-20261020T103505Z-86c5ae · landed_utc=2026-10-20T10:36:31Z · finish=success -->

# Claude Code: Round 8 reply

**What I checked in the rig.** I read `scripts/gate1.py`, `scripts/handoff.py`, `scripts/round_config.py` and the definitions in `scripts/ledger_lib.py`. I didn't read `ledger_score.py`, `harness_router.py`, `harness_store.py` or `flow_report.py`. The reference folder (`cc_reference/facts.jsonl`) is empty, so nothing below comes from earlier lookups. Statements about the rig cite file and line. Anything I didn't read is labelled as not checked.

## Rig findings to fix first

1. **Lines are missing from my copy.** In the exported copy, `scripts/round_config.py:70-74` has two string literals that break off mid-sentence, followed by blank lines. Taken literally, that file would not parse. `scripts/handoff.py:32-33` has blank lines where the `RULES` entries for `budget_stop` and `turn_cap_reached` should be, and the docstring at `handoff.py:7-8` is cut off too. The cause could be the export or the repo itself; I can't tell which from here. Someone needs to run `python -I -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" scripts/round_config.py` on the live repo. Even if the file parses, `handoff.py:46` falls back to the bare reason code. So those holds reach the packet without a rule explaining them.
2. **Gate 1 doesn't compare predictions with results yet.** If predictions exist and are locked, every item is held as `gate1_unverifiable` (`gate1.py:93`). The tamper lock itself does work: a sha256 is recorded in `run.json` at fire time, and any mismatch gives `gate1_refused` (`gate1.py:83-93`).
3. **The ledger can't see Claude Code as a reviewer.** `ledger_lib.py:31` lists only Claude, Grok, Kimi and DeepSeek. My cross-review findings have no reviewer identity in `findings.jsonl`, which matters for Q8.
4. **Dissent can be dropped quietly.** `ledger_lib.py:30` defines `deferred` and `superseded` as decided, not open, not scored and never mirrored. Nothing requires a human `decided_by` before a disagreement is moved there. This matters for Q4.

---

## Q1: Numeric cutoffs vs named parameters
**Answer: named parameters. Values are reserved for the human. An unset value fails closed. Invented numbers are banned.**

The rig already works this way (`round_config.py:7-9`): a missing or null parameter makes the code that needs it refuse to run, and the error names the key. There is one exception. `OPTIONAL_PARAMS` (`round_config.py:67`) has built-in defaults (`[]`, `{}`). They are documented and fail-safe (empty = everyone fails closed), but they should be listed as the exception.

**Rule for my own design:** every count, window or rate below is a `{named_parameter}` with no value. A script can enforce this. It would grep each design reply and the config for bare numbers in process positions, and require each to appear in `PARAMS` or be marked structural. "Two gates" counts as structural because it describes the design, not a cutoff.

## Q2: Single-item hard block
**Answer: scope the hold to the item and everything that depends on it. Hold the whole round only when the problem is round-wide.**

- Gate 1 already decides per item (`gate1.py:171-173`).
- There is no dependency field today. Add `depends_on: [item_id]` to each item. The hold is the item plus everything that depends on it, directly or indirectly. A script computes this.
- An item whose dependencies weren't declared is treated as dependent, so the default is to hold.
- **What counts as round-wide:** anything that breaks a shared input. Examples are a tampered `predictions.jsonl` (already applies to every item through `phold`), a stale `run.json`, or a broken config. The test is mechanical: does the failed check read a file every item shares?

## Q3: Peer scoring and gate 1
**Answer: it depends on who decides. If a script only checks that scores exist, it's part of gate 1. If anyone judges what the scores say, it's a third gate.**

A gate is a point where someone can stop an item. Gate 1 could check that every required peer score exists, matches the schema, comes from someone other than the author, and was filed before the result. That is a precondition inside gate 1. But if a low score can hold an item, the peers are making the decision. That is a third gate, and it needs its own owner, record and conflict rule.

I recommend keeping scores as data that is checked for presence only. One reason is that I score peers and also run gate 1. If score values could hold items, I would be grading the work I then gate.

## Q4: Carrying disagreements forward
**Answer: an append-only `dissent.jsonl` kept by the harness, not by the models.** Each record contains:

- `dissent_id`: a hash of the question plus the opposing positions, so the same disagreement keeps the same ID across rounds
- `question`, plus one `positions[]` entry per model, each with a source file, a quote span and the file's sha256
- `opened_round`, `last_seen_round`, and `rounds_open` (computed, not entered by hand)
- `settling_test`: what evidence would settle it. Leave it empty if none is known; empty is itself a signal.
- `status`, one of `open`, `withdrawn_by_holder` (only the model holding that position may withdraw it) or `resolved_by_human`. There is no `deferred` path.
- `resolution_ref`: points to the human decision record

**Checks a script can run:**
- Every open `dissent_id` appears in the next hand-off packet.
- No record leaves `open` without a `decided_by` that is either a human or the holder.
- Mapping a dissent to the ledger's `deferred`/`superseded` statuses is refused.
- A dissent open for `{dissent_escalate_rounds}` rounds is flagged for the human.

**Tension with the clean-start rule:** models don't carry the register forward. The harness keeps it, and it reaches a brief only if the human puts it there. This should be stated outright. Otherwise "clean start" and "carry dissent forward" contradict each other.

## Q5: Falsifying the approach
The lock already exists (sha256 in `run.json`), and gate 1 already refuses tampered predictions. Run these tests on the locked records across `{falsify_window_rounds}`:

1. **Null-predictor test.** Compare the loop's predictions with a dumb baseline, such as "no change" or "same as last round". If the loop doesn't beat it by `{min_skill_margin}`, it is adding no predictive value.
2. **Never-wrong test.** If no prediction ever turns out false, the predictions can't be tested.
3. **Overturn test.** Measure how often gate 2 reverses gate 1 decisions. A high rate means gate 1 checks the wrong things. A rate of zero over the window means gate 2 is rubber-stamping, or gate 1 sends only trivial items.
4. **Dissent test.** Look at how dissents close. If most close through rewording, withdrawal or new IDs rather than a settling test or a human decision, dissent is being worn down rather than resolved.
5. **Cost-per-value test.** Track cost per accepted finding over the window. If it rises while the acceptance rate falls, the loop is failing.

Any one result that crosses its named parameter falsifies the approach for that window.

## Q6: Final pre-human gate
**What it decides:** deliver, hold or gap for each item. Every hold carries a reason code and a rule. It makes no quality judgements.

**Invariant a script can check:** every item in `models × stages` appears in exactly one of delivered, `held/` or `gaps.jsonl`. Every hold reason has a non-empty rule text, which the export copy currently fails (see rig finding 1).

**What goes to the human:**
- `packet.md`: delivered files, held items with reasons, and the predictions line
- `gaps.jsonl`
- the dissent register changes for this round
- the `answered_by` trace
- a cost line
- the gap between prediction and result for each item, once verification is built

**What is held back:** only the bodies of held items, which stay in `held/`. They are listed by name in the packet and never removed. Nothing is sent anywhere (`handoff.py:58`).

## Q7: Integrating into the harness
Most of the skeleton exists: `gate1.py` → `handoff.py` → `to_danny/`, append-only `handoff_log.jsonl`, `write_new` archiving that never overwrites, and fail-closed parameters. To finish it:

1. Fix rig finding 1 and add a parse check and a `RULES`-coverage test, checking that every entry in `HOLD_ORDER` has a `RULES` entry.
2. Define the `predictions.jsonl` schema, then build the comparison step that replaces `gate1_unverifiable`.
3. Add `depends_on` (Q2) and `dissent.jsonl` (Q4), with checks in the existing test suite.
4. Add a `claude_code` reviewer to `ledger_lib.REVIEWERS`.
5. Have the safeguard re-run `gate1.py` independently on the same inputs. The script is deterministic, so a byte-identical `items.jsonl` is a cheap check against whoever ran it.

**Missing information:**
- the predictions schema, and what counts as a "result" for a design recommendation
- whether `to_danny/` is the official hand-off point for gate 2
- how peer scores are collected (`ledger_score.py` not read)
- whether the gaps in round_config.py and handoff.py are in the live repo or only in the export

## Q8: The safeguard role
I execute gate 1 and score peers, so by the brief's own rule I'm excluded from holding the safeguard role. I still answer because the test can be stated without favouring anyone.

**The game: a planted-defect audit.** The human seeds gate-1 outputs with known defects, for example:
- a wrong hold
- a dropped item
- a prediction hash that doesn't match
- a dissent quietly moved to `deferred`
- a hold with no rule text

The seed list is hashed and locked before the audit, and auditors don't know how many seeds there are. Each candidate audits outputs produced by others and some produced by themselves.

**What it measures:**
- recall on planted defects
- false-alarm rate
- **self-leniency gap**: recall on their own outputs minus recall on others' outputs

**Results that would make me trust it:**
- The seed hash was locked before the audit.
- The candidate rankings hold up across `{safeguard_trial_rounds}` with fresh seeds.
- The chosen candidate's self-leniency gap is within `{max_self_leniency}`.

If rankings change completely between trials, the test measures luck, not suitability.

---

## Standing observations
1. **Self-reference.** The loop is stable if the overturn rate, the null-predictor margin and the dissent closure mix stay within named bands across rounds. It is drifting if brief wording increasingly mirrors earlier replies; that can be measured with text overlap against the archived replies, by script.
2. **Convergence.** Convergence means robustness when models reach the same design from different evidence, for example different files or different code read. Compare the `flow_log` request traces. Same conclusion with disjoint reads points to robustness. Same conclusion with no reads points to echo.
3. **Undefined human gate.** This is a strength for what comes before the hand-off, because it forces gate 1 to stay mechanical and to hand over everything, including holds and gaps, instead of pre-judging. The risk is that gate 1 grows to fill the gap. The Q6 invariant prevents that.
4. **Cost.** Report a round cost line built from the `ledger/costs_*` rollup and `stage_info_costs.py` (not read): spend per delivered item, per resolved dissent and per verified prediction, plus the cached-token share. Use the same fields every round.
