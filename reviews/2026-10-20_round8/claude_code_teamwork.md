<!-- landed: reviewer=claude_code · model=claude-opus-5-5 · channel=scripts/review_claude_code.py --ping · generated_utc=2026-10-20T10:54:33Z · source=/tmp/r8_teamwork_2026-10-20/claude_code/ping.json · run_id=teamwork-20261020T105433Z-2b3358 · landed_utc=2026-10-20T10:55:38Z · finish=success -->

# Claude Code: Round 8 cross-review

I didn't score my own reply. For the rig claims below, I read and grepped the exported repo rather than relying on how each reply described it.

## What the rig shows, against the replies' claims

| Claim | Who made it | What the rig shows |
|---|---|---|
| A prediction lock exists: `launch_round.py` records `predictions_sha256` in `run.json` at fire time | DeepSeek (true). Grok says "treat as none". Kimi and Claude both ask whether it exists. | **Exists.** `launch_round.py:541` writes the hash and `gate1.py:86` reads it back. |
| Gate 1 already exists as code | DeepSeek (true). Kimi and Claude propose building it. | **Exists**, in `scripts/gate1.py`. It doesn't compare predictions with results yet (`gate1_unverifiable`). |
| The ledger already has `deferred` and `superseded` statuses that are never scored | No one | Confirmed by `ledger_score.py:127-130` and `tests/test_ledger_staged.py`. Any dissent design that reuses these names goes through an existing path where items close and are never scored. |
| `land_review_reply.py` writes each landed reply into the round folder | Grok | `docs/harness_context.md:14` says so. I haven't checked whether that write is the right point to call "a result exists". |

Kimi, Claude and Grok reported that their rig questions to me came back `pending_human`. None of them invented answers, which is the right behaviour. Kimi and Claude stated their gaps as conditions on their plans. Grok defaulted the gaps to "none". On the lock and gate 1, that default is factually wrong.

---

## Kimi: 7.5 / 10

**Enforceability: strong.** It has a lint-checkable parameter rule with an exemption for identifiers, an `UNSET` outcome that fails closed, `depends_on` closure, and a reason-code enum for holds. The strongest mechanism in any reply is that **a reply missing a disposition for any open dissent is schema-invalid.** That makes silent dropping a validation failure.

**Carrying dissent forward: good, with one way for dissent to wear away.** `withdrawn` and `defer-with-reason` don't say who may file them. A non-holder could defer a dissent one round after another, and nothing ever escalates it to the human. `P_DISSENT_WINDOW` only appears in §11.1, as a trend metric. Kimi does deal openly with the tension between clean start and carry-forward: the reply calls the ledger a "data carry-over" and names it as the one exception.

**Number rule:** consistent. The registry covers every cutoff. `P_HOLD_SCOPE` comes with a "proposed default", but that is a categorical choice, not a number, so it's minor.

**Rig:** Q7 proposes building a prediction lock and a gate-1 script, and both already exist. Kimi labels these as conditional on missing facts, which is honest.

## DeepSeek: 7 / 10

**Enforceability: good.** The peer-score hold code (`gate1_hold_peer_scores`) is concrete. When `depends_on` is malformed, only that item is held. When an open disagreement is missing from a hand-off, the package gets `gate1_refused`, and a script can check that. Q7 proposes parsing the PASS/FAIL lines in `{model}_teamwork.md` into `items.jsonl`, which is mechanical and buildable.

**Carrying dissent forward: weakest of the four.** Disagreements can close as `superseded` or `dropped` "with a reason", but nothing limits who may close them. That name also collides with the existing `superseded` status, which is decided and never scored, so the design reuses the very path where dissent can quietly vanish. The reply doesn't address the tension with clean start at all.

**Number rule:** consistent. `HP:min_peer_scores`, `HP:min_edge` and `HP:max_similarity` are all named. Bucket boundaries are reserved for the human.

**Rig:** it has the most accurate rig facts of the four, and I've verified them. It correctly lists the three gaps: nothing writes predictions, there is no comparison step, and peer scores aren't structured. Under the rig-weighting rule this counts for a lot. On Q5, the null model ("predict whatever the recommendation asserts") is muddled, and it overlaps with the reply's own test for drift toward self-fulfilling predictions.

## Claude: 8.5 / 10

**Enforceability: the strongest overall.** Dependencies are declared **when the prediction is locked**, so nobody can redraw the graph afterwards to make a hold smaller. Undeclared dependencies count as dependent. Blocks on shared inputs hold the whole round. The set of held items is "a pure function" of which items are blocked. Q6 gives a four-way status (PASS / FAIL / HELD / UNCHECKABLE), and a script checks that the JSONL matches the Markdown.

**Carrying dissent forward: the strongest.** A closure counts only as `resolved-by-evidence` against a criterion recorded when the entry opened, or as `withdrawn-by-holder`. **A majority vote never closes an entry.** The set difference between rounds must be empty. The reply proposes a reconciliation with clean start for the human to decide. Even so, `escalated` has no defined exit, and `STALE_FLAG_ROUNDS` only flags; it doesn't force escalation.

**Number rule:** consistent. The parameter table includes what happens when each one is unset. "Round N / N+1" uses variables, not cutoffs.

**Rig:** Q7 is honestly conditional, but it asks whether gate 1 and a prediction lock exist, and both do. The method review is useful: it notes that I hold four roles at once and that the scoring itself is circular.

## Grok: 6.5 / 10

**Enforceability: the purest of the four, but over-constrained.** It allows only boolean predicates and set equality. That makes every rule script-checkable, and it is consistent with Grok's own Q1. The cost is that Q5 can't test whether predictions show any skill over a baseline. With no margin and no rate, Grok can detect integrity failures but not a loop that produces no value. Q3 makes peer scores pure evidence that never affects pass/fail unless they were sealed into the predicate. That is consistent, but no precondition requires the scores to exist at all.

**Carrying dissent forward: strong.** It uses a carry-or-resolve event every round, checked by set equality. Resolution needs a boolean predicate plus the evidence that satisfied it, and the author can't self-resolve. There's a gap: a dissent whose resolution can't be written as a boolean has no route to a human decision. It stays visible but can never close.

**Number rule:** applied with the most rigour of the four, including the self-check in Q8 that "requiring agreement would be a count". It has no violations against its own standard.

**Rig:** "treat as none until Claude Code's read returns" is wrong on the two most important facts, the lock and gate 1. The advice "do not wire a schema" until the rig read comes back is sound practice. But the falsification booleans in Q5 assume a seal step that has to be built, when one already exists at `launch_round.py:541`.

---

## Ranking

1. Claude (8.5)
2. Kimi (7.5)
3. DeepSeek (7)
4. Grok (6.5)

The spread is narrow. All four replies scope the hold to the item plus its dependencies, and all four put dissent in an append-only record outside the models. Two things separate them:

- **Who may close a dissent.** Claude and Grok restrict it. Kimi and DeepSeek don't.
- **How accurate the rig claims are.** DeepSeek's are verified. Grok's default of "none" is wrong.

Whichever design is adopted, one fix applies to all of them: a dissent record must never map to the ledger's existing `deferred` or `superseded` statuses. Those statuses close items without any human `decided_by` (`ledger_score.py:127-130`).
