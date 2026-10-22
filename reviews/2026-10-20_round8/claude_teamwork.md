<!-- landed: reviewer=claude · model=claude-opus-5-5 · channel=scripts/review_claude.py --ping · generated_utc=2026-10-20T10:54:33Z · source=/tmp/r8_teamwork_2026-10-20/claude/ping.json · run_id=teamwork-20261020T105433Z-2b3358 · landed_utc=2026-10-20T10:56:03Z · finish=end_turn -->

# Claude's cross-review for Round 8: Kimi, DeepSeek, Grok and Claude Code

**I couldn't confirm any rig facts myself.** I asked Claude Code to check a few rig facts before scoring. My question to him came back `pending_human`, and my `request_info` with scope `rig` came back `budget_stop`. So when replies disagree about the rig, I rely on what Claude Code says he read, with file and line references.

DeepSeek also says it ran a live rig check, but its reply shows no result from one. Some of its facts match files Claude Code read: `gate1.py` exists, it marks matched items `gate1_unverifiable`, and the predictions hash is locked in `run.json`. Two of its facts don't match anything he read: what `ledger_score.py` does, and the `{model}_teamwork.md` files. I treat those two as unconfirmed.

## Scores

| Reply | Score (/10) | Main reason |
|---|---|---|
| **Claude Code** | **8.0** | Grounded in the rig code, with the strongest rules for closing disagreements. But he uses several cutoffs his own first answer doesn't allow. |
| **Kimi** | **8.0** | Fully checks itself against its own first answer and is highly checkable. But any model can close a disagreement, and the reply puts earlier positions back into the brief, which clashes with the clean start. |
| **Grok** | **7.5** | Follows its own first answer most strictly, and disagreements stay open until there's evidence. But it ties the prediction lock to the wrong point in the run, and that rule leaves its falsification tests with no comparison against a baseline. |
| **DeepSeek** | **6.5** | Its rig plan is mostly confirmed by Claude Code's reading. But a missing dependency list doesn't hold dependent items, any model can close a disagreement as `dropped`, and "dominated" is a cutoff with no named parameter. |

---

## Claude Code: 8.0

**Strengths**
- **He is the only reply that read the rig, and it changes the picture.** He found:
  - truncated lines in `round_config.py:70-74` and in the `handoff.py` rules list;
  - that the ledger can't record him as a reviewer (`ledger_lib.py:31`);
  - that `deferred` and `superseded` count as decided (`ledger_lib.py:30`). That gives disagreements a way to disappear quietly that no other reply could have seen.
- I weight these findings heavily, as the source-of-record rule asks.
- **His Q4 has the best closure rule of the four.** An entry closes only by withdrawal by the model holding the position, or by a human decision. A script checks the `decided_by` field. Moving an entry to `deferred` is refused.
- **His Q4 also handles the clean-start problem well.** The harness keeps the register, and an entry reaches a brief only if the human puts it there.
- **His Q7 point 5 is the cheapest real safeguard any reply offers.** Re-run the deterministic `gate1.py` and compare the output byte for byte.
- The Q6 check (every item lands in exactly one of delivered, held or gaps) and the Q2 rule (undeclared dependencies count as dependent) are both checkable and fail safe.

**Number rule (against his own first answer, which requires named parameters)**
- **Q5 test 3:** "a high rate" has no parameter.
- **Q5 test 4:** "most close through rewording" is an unnamed majority cutoff.
- **Q5 summary:** he says any result that crosses "its named parameter" falsifies the approach, but tests 2–4 have no named parameter.
- **Standing observation 1:** "within named bands" names no bands, and the text-overlap check has no parameter.
- That makes four breaches, more than any other reply has. This is the main deduction.

**Smaller point:** his Q5 overturn test measures what gate 2 does. That doesn't define gate 2, but it comes close to the boundary.

---

## Kimi: 8.0

**Strengths**
- **It checks itself against its own first answer.** It keeps a full registry of its parameters, every value is reserved for the human, and an unset value fails closed with a visible list of what's missing. I found no bare cutoff anywhere.
- **Q2 is good.** The hold scope is item plus dependents, every hold needs a reason code, and held items go to the human in a separate list, so they're never deleted.
- **Q8 targets the right risk.** Its seeded-defect classes include a dropped disagreement and a checker who is also the author. Its "Own-Goal Audit" (checking a round where your own recommendation failed) tests self-serving bias directly.
- **Q7 is properly conditional.** It says exactly which facts are missing instead of guessing.

**Weaknesses**
- **Q4: any model can close a disagreement.** Any replying model can file `close-with-reason`, and nothing limits that to the model holding the position. A majority could close out a dissent this way. On how well disagreements carry forward, this is the main gap.
- **Q4: `defer-with-reason` can repeat forever.** It does keep the entry visible, so this is minor.
- **Q4 sends positions back to the models.** It injects a manifest into the next brief with each model's structured positions, and replies must respond to each entry. That gives models attributed earlier positions, which is close to what the clean start forbids. Kimi says it carries data, not conversation, but it doesn't solve the clash the way Claude Code does.
- **Q3:** it says a mechanised rule on score values "collapses back into gate 1". That moves the veto to the peers without naming who decides.
- **Number rule:** `P_HOLD_SCOPE` comes with a proposed default value. That's a small breach of its own "reserved for the human" rule. It's categorical rather than numeric, so I deduct little.
- **Q1's linter scans only "rule-bearing sentences".** Deciding which sentences those are takes some judgement.

---

## Grok: 7.5

**Strengths**
- **It is the most consistent with its own first answer.** It bans named parameters too, and then uses no count anywhere. It even turns down requiring agreement between two checkers because that would be a count.
- **Q4 keeps dissent visible.** Disagreements close only by a resolution event that a script can evaluate. A closure filed by the author of the disputed claim doesn't count. Leaving an entry out of a later round fails a set-equality check. Nothing can close by vote or by silence.
- **Q6 is strong.** It requires that the checker isn't the author, and that every withheld item is listed with the check it failed.
- **It applies the glossary carefully,** for example by not using **hold** for a single item.

**Weaknesses**
- **Q5 ties the seal to the wrong event.** It treats "result exists" as the moment `land_review_reply.py` writes the reply. But the reply *contains* the recommendation; the result comes later. As written, the seal would come before the recommendation it is meant to test.
- **Q2 can't be enforced as written.** "An item that needs the blocked item but does not declare the edge is itself a hard block" can't be detected by a script. An undeclared need is invisible.
- **It uses a new term without flagging it.** It says it isn't coining a term, then uses "freeze/frozen" as one throughout.
- **Its strict rule costs it a test.** Banning every parameter means Q5 can't compare predictions against a baseline or check calibration. It only finds integrity breaches, not "no better than chance". That's internally consistent, but weaker as a way to falsify the approach.
- **Q3 contradicts itself in passing:** "not part of gate 1 either". In practice it treats scores as evidence only, which makes sense.

---

## DeepSeek: 6.5

**Strengths**
- **Q7 is concrete.** Most of it is confirmed by what Claude Code read, and it names the three missing pieces clearly: nothing writes predictions, there is no comparison step, and peer scores aren't structured.
- **Q4's traceability check makes a missing open entry a gate-1 refusal.** That is checkable.
- **The "constitution snapshot" hash** (standing observation 1) is a good mechanical drift check, and it separates resetting content from changing the rules.

**Weaknesses**
- **Q2 fails open.** A missing `depends_on` holds only that item, so an item that actually depends on the blocked one, but leaves the field out, goes through. Leaving the field out becomes a way to escape a hold. This is the opposite of the fail-safe default in Claude Code's reply and mine.
- **Q4's `dropped` status lets any model close a dissent with a reason,** and nothing says who may file it. That is an approved way to drop dissent quietly.
- **Number rule:** Q5 says the loop fails if unfalsifiable predictions are "dominating the record", and says so twice. That's a majority cutoff with no named parameter, which breaks its own Q1.
- **Q5's baseline is unclear.** "Predict whatever the recommendation itself asserts" doesn't make sense as a baseline for predictions that are about the recommendation.
- **Q7's "similarity/negation" comparison for prose relies on judgement,** and Q8 has no baseline and no repeat trials.
- **Unconfirmed rig claims:** what `ledger_score.py` does, and the teamwork files.

---

## Points that apply across all four

- **Who can close a disagreement is what most separates the replies.**
  - Safe: Claude Code (holder or human only) and Grok (evidence only, and not by the author).
  - Unsafe: Kimi and DeepSeek both leave closure open to any model.
- **Claude Code's finding that `deferred`/`superseded` count as decided in `ledger_lib.py:30` affects every reply's Q4.** Any register built on the existing ledger statuses would inherit that way of dropping dissent unless the statuses are changed.
- **The truncation in `round_config.py` and `handoff.py` needs a parse check on the live repo** before anyone treats the existing gate-1 setup as working. None of the three non-rig replies could have known this.

I haven't scored myself, and I've used nothing from earlier rounds.
