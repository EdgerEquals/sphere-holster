<!-- landed: reviewer=grok · model=grok-4.7 · channel=scripts/review_grok.py --ping · generated_utc=2026-10-20T10:54:33Z · source=/tmp/r8_teamwork_2026-10-20/grok/ping.json · run_id=teamwork-20261020T105433Z-2b3358 · landed_utc=2026-10-20T10:59:47Z · finish=completed -->

Cross-review only. I am not scoring my own reply. These are review scores, not an adoption, not a gate, and not a loop parameter. Nothing below is taken from any earlier round.

Review weights, applied the same way to all four: enforceability 50% (a script can check it, or it cannot), dissent carry-forward 30% (visible and traceable, or quiet-droppable), number-rule self-consistency 20% (every process count checked against that reply’s own Q1). Claude Code is the source of record on rig items. Where a rig claim conflicts with him, his read wins. Outline numbers, brief-fixed “two gates,” and file:line citations are not cutoffs for anyone.

## Scores

| Reply | Enforceability | Dissent | Own Q1 | Weighted |
|---|---:|---:|---:|---:|
| Claude Code | 8 | 9 | 6 | 7.9 |
| Claude | 8 | 8 | 7 | 7.8 |
| Kimi | 7 | 8 | 7 | 7.3 |
| DeepSeek | 7 | 6 | 6 | 6.5 |

## Claude Code — 7.9

Rig-related answers are the strongest of the four because they are tied to files he read, not to a guessed schema. `gate1.py` already fail-closes to `gate1_unverifiable` and refuses a broken predictions hash. `round_config.py` already refuses a missing parameter instead of inventing one. `ledger_lib.py` can move a disagreement to `deferred` or `superseded` with no human `decided_by`, and those statuses are not mirrored. That is a real quiet-drop path. His Q4 refuses that mapping, allows closure only by the holder or a human, and requires every open `dissent_id` in the next packet. A script can check those three. The Q6 invariant (every item in exactly one of delivered, `held/`, or `gaps.jsonl`, and every hold reason has non-empty rule text) is also a script check, and he notes the export copy currently fails it. The safeguard check is the most mechanical of the four: re-run `gate1.py` on the same inputs and require a byte-identical `items.jsonl`. He excludes himself from the role, which matches the author-versus-checker conflict.

Dissent is not quite Kimi’s forced model disposition. Models do not see the register unless a human puts it in a brief. That is the right clean-start split, and the packet check still stops a silent drop. Empty `settling_test` is allowed. That is honest, and it does not by itself close the record.

Number-rule misses, against his own rule that every count, window, or rate is a `{named_parameter}` with no value:

- Q5 overturn test uses a written decision line, “a rate of zero.”
- Q5 dissent test uses “most” as an unnamed rate.
- Standing observation 1 says stability is “named bands” and never names them.

Those are the same class of slip I am charging below. They are why he does not pull further ahead of Claude.

He uses item-level “hold” without flagging the glossary, which binds **hold** to the round. The rig already says `held/` and `HOLD_ORDER`, so this is a glossary-versus-code clash he should have named, not a reason to discard the scoped-hold rule. `flow_report.py` is in his unread list, then standing observation 2 leans on `flow_log` traces. Small, and labelled enough that I am not treating it as a schema guess.

## Claude — 7.8

Best mechanical design among the replies that did not get a rig read. He says what is missing and does not invent `gate1.py` paths. The held set is a pure function of a dependency graph locked before results. Missing dependency data counts as dependent, so the graph cannot be drawn after the fact to shrink a block. Shared-input failures (brief, ledger, gate-1 code, prediction lock) are the only round-wide case, and that matches the glossary’s round-level **hold**. He proposes **item hold** as a new term and does not pretend it is already approved. That is the only reply that keeps the glossary check scriptable.

Peer scores: presence and completeness inside gate 1, excluding self-scores; values cannot stop an item. No hidden quorum. Raw scores go through with no average. Q4 is set equality: every open id in round N appears in N+1, still open or with a valid closure. A majority vote never closes. Only `resolved-by-evidence` or `withdrawn-by-holder`. Stale-flagging is a named parameter that, while unset, shows the count and closes nothing. The hand-off pushes FAIL and UNCHECKABLE through, so gate 1 cannot become a silent filter. The safeguard test has a script baseline, sealed batches, and separate recall on self-favouring and authority-attributed defects. He states his own conflict and does not appoint himself.

Dissent is a half-step under Claude Code because the resolution criterion is not required to be script-decidable. “Citing evidence that meets the stored criterion” can still be a prose judgement. He also could not see the `deferred`/`superseded` drop, so he did not close it. That is missing information, not a guess.

Number-rule misses, against his own rule that any tunable cutoff is a named parameter, unset, fail-closed:

- Q5 “if the models don’t beat it” is a zero skill margin with no name. DeepSeek named the same margin. Claude did not.
- Q8 “if no model beats the script baseline” is the same unnamed zero.

His linter spec is looser than Kimi’s: “numeric literals not on the allowed list” would flag outline numbers unless scan scope is narrowed. That is a spec gap, not a pile of violations for list markers. I am not charging those against him, and I am not charging them against anyone else.

Q7 is correctly conditional. Points 1–6 should not be wired until the pending read returns. I am not treating his `scripts/gate1_check.py` name as a claim that the file exists.

## Kimi — 7.3

Strongest audit surface on paper. The registry is complete, values are `RESERVED-HUMAN`, and unset becomes `UNSET` rather than a silent default. A numeral linter restricted to conditional or comparative sentences is a real grep, not a vibe. `depends_on` closure is graph traversal. The dissent manifest is a launch blocker. A reply with no disposition for an open entry is schema-invalid, so silence fails the build. That is the best anti-drop rule aimed at model replies. Closure needs a reason and a ledger reference. Status history is append-only. Coined terms are marked as not in the glossary.

The carry-forward hole: he never says only the holder may withdraw, and `close-with-reason` can be a reply disposition. A non-holder can end someone else’s dissent if a reason string is present. A script can check that a reason field is non-empty. It cannot check that the reason is the holder’s. `defer-with-reason` stays visible, which is good, but `P_DISSENT_REACK` can later make deferral the steady state. Until that parameter is set he fail-closes, so this is not a quiet drop today. It is a reserved drop later.

Q3 leaves a trapdoor. Presence-only is inside gate 1. Then `P_SCORE_AGG_RULE` can still let a score value stop an item, and he calls that gate 1 because one script runs it. A veto executed by gate 1’s script is still a veto. Claude and Claude Code refuse that. I weight their version higher.

Q5 and Q8 are the enforceability cost. Skill, calibration, specificity, drift, and echo all wait on reserved parameters, and several need an unspecified similarity function. Game 2 (“softened framing”) and Game 3 (“expedite”) are model judgements. Seeded defect classes (a)–(f) can be script-scored. The rest cannot. A design that cannot return a falsification verdict until a long human registry is filled is mechanically shaped and operationally idle. That is better than an invented number. It is worse than a boolean a script can evaluate now.

Number rule: no bare decision numeral in a process position, and the registry matches the parameters he uses. One evasion of his own first sentence: “no positive skill over the baseline” is a zero margin written in words so the numeral linter will not see it. Changing that zero changes the falsify outcome. It is the same miss as Claude’s unnamed baseline margin, caught under his stated rule rather than under his grep. I am not charging “one executor” or “six questions.” Those are definitional or descriptive, and I am not charging the same class against the others.

Q7 is honest about `pending_human`. He does not invent a findings schema. That is the correct use of the source-of-record rule.

## DeepSeek — 6.5

The disagreement index check is genuinely mechanical: content-addressed id, full open index in every hand-off, absence without a close record marks the package `gate1_refused`. Hash-before-result is a boolean. `depends_on` missing holds that item only, which keeps blast radius from becoming a judgement call. `HP:min_edge` is the one baseline margin in this set that is actually named. Peer-score count is a named parameter, and unset does not get a default. Q6’s release-versus-hold split does not decide merit.

Dissent is the weak axis. Close reasons include `dropped` and `superseded`. He says the drop is not silent because a citation is required. Traceable deletion is still deletion, and he never says who may write the close record. The author of the disputed claim can drop it. Claude Code found that `superseded` is already a non-open, non-mirrored status with no human `decided_by`. DeepSeek’s design keeps that shape and adds `dropped`. Against “can it quietly drop,” this is the worst of the four, even though the absence check itself is good.

Number rule, against his own sentence that every decision cutoff is a named parameter, not only bare numerals:

- “Dominated by” unfalsifiable predictions is a cutoff with no name.
- Calibration “bucket boundaries are human-reserved parameters” and are never given symbols.
- “Systematic miscalibration” falsifies with no named band.
- No registry, so a later reader cannot audit the set the way Kimi’s table can be audited.

I am not charging “two gates” or “three gaps.” I am not charging outline numbers.

Q7 is the other deduction. He asserts a live rig check and then names artifacts the source of record does not confirm. Claude Code: comparison is not built; `ledger_score.py` was not read; peer-score collection is unknown; the hand-off surface he did read is `packet.md`, `gaps.jsonl`, `held/`, and `handoff_log.jsonl`. DeepSeek: `gate1/{summary.md,items.jsonl,gaps.jsonl}`, `{model}_teamwork.md` as the peer-score channel, and `ledger_score.py` already scoring planted mistakes. The hash lock and `gate1_unverifiable` match Claude Code. The output paths and the teamwork file do not. I am weighting the source of record, not the denser prose. An integration plan aimed at the wrong files is not yet a script.

Q8 measures self-exemption, which is the right conflict, but “spin” is not a script check, and the operational rule never says the safeguard flags rather than passes. Kimi and Claude Code both close that.

## Separations I am not smoothing over

Shared conclusions are not one design. All four scope a hard block to a declared dependency closure and refuse to call peer-score values a third gate unless those values can stop an item. That is four derivations from the same brief clauses. The rejected alternatives differ: Kimi keeps a parameterised score-aggregation veto inside gate 1; DeepSeek holds on a reserved minimum count of scores; Claude and Claude Code keep values as evidence only. Those are not echoes of each other.

Glossary: **hold** is a round paused mid-flight. **threshold** is a physics term. Claude is the only one who both renames the item-level pause and keeps the round-level word for shared-input failure. Kimi coins “scoped hold” and labels it unapproved, then uses it as the working term anyway. DeepSeek and Claude Code use item-level hold with no glossary flag. A script checking `docs/vocabulary.md` would fail the last two today.

Clean start versus carry-forward is unresolved in all four, and each says so differently. Kimi injects the manifest into the next brief. Claude and Claude Code keep it off the model side unless a human restates it. DeepSeek puts the open index in the hand-off and does not say whether the next brief sees it. Forcing model disposition (Kimi) and forbidding non-holder closure (Claude, Claude Code) are both needed. None of the four has both.

I would trust a later mechanical check of Claude Code’s packet invariant and dissent-status refusal first, because those are checks against code he read. I would not treat any of these four as adopted, and I would not fill `RESERVED-HUMAN`, `HP:*`, or `{named_parameter}` from this review.
