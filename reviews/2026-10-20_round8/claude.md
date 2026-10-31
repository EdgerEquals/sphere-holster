<!-- landed: reviewer=claude · model=claude-opus-5-5 · channel=scripts/review_claude.py --ping · generated_utc=2026-10-20T10:35:05Z · source=/tmp/r8_fire_2026-10-20/claude/ping.json · run_id=primary-20261020T103505Z-86c5ae · landed_utc=2026-10-20T10:39:10Z · finish=end_turn -->

# Claude's reply for Round 8: answers to the eight questions, the four standing observations, and a method review

## Before the answers: rig facts I couldn't confirm

I read `harness_context` and `vocabulary`. I also sent Claude Code a set of read-only questions about the rig, by `ask_claude_code` and by `request_info` with scope `rig`. Both came back **pending_human** with no answer. So nothing I say below about the rig's internals is confirmed by the source of record. Where it matters, I say what's missing instead of guessing (mainly in Q7).

**Vocabulary clashes in the brief** (details in the method review at the end):
- The glossary defines **threshold** as a *physics* term. In this reply, a process cutoff is called a **named parameter**, never a threshold.
- The glossary defines **hold** at the *round* level only. For an item-level hold I suggest a new term, **item hold**. It is not glossary language until the human layer approves it.

---

## Q1 [HIGH CUE]: Numeric cutoffs vs named parameters

**Answer: allow named parameters, ban invented values.** Any tunable count or cutoff is written as a named parameter whose value only the human sets. It starts **unset**.

How unset parameters behave:
- **Parameters that decide something fail closed.** While unset, the check they control can't return PASS. It returns UNCHECKABLE, or the more conservative outcome.
- **Parameters that only label something** (for example, an "open a long time" flag) are skipped while unset. The raw figure is still shown.

**The only numbers allowed in the design:**
- counts fixed by the brief (eight questions, two gates);
- logical words: *any*, *all*, *none*, *every*;
- identity (an item is itself).

**A script can check this.** Lint the design and the gate config for numeric literals that aren't on that allowed list.

**The named parameters this design uses.** All are unset and reserved for the human:

| Parameter | Used in | If unset |
|---|---|---|
| `STALE_FLAG_ROUNDS` | Q4: flags a disagreement that has stayed open a long time | No flag. Rounds-open count still shown. |
| `FALSIFY_ALPHA` | Q5: significance level for the pre-registered tests | Test statistics are reported, but no verdict is given. |
| `PLANTED_DEFECT_COUNT` | Q8: hidden number of planted defects | The test can't run. |
| `TRUST_BATCHES` | Q8: how many separate test batches must agree | No safeguard verdict is given. |

I made sure every other rule is structural so that it needs no number at all.

---

## Q2 [HIGH CUE]: Single-item hard block

**Answer: scope the hold.** A hard block on item X puts an item hold on X and on everything that depends on it, directly or indirectly. Every other item goes on.

What keeps the scoping honest:
1. **Dependencies are declared when the prediction is locked, before any result exists.** Nobody can draw the graph afterwards to make a hold smaller.
2. **Missing dependency data counts as dependent.** If an item's dependencies weren't declared, it is held along with X.
3. **Some blocks hold the whole round.** A block on a shared input (the brief, the integrity of the ledger, gate 1's own code, or the integrity of the prediction lock) is a round-level hold in the glossary's sense.
4. **The blocker can't clear their own block.** An unresolved block goes into the disagreement register (Q4) and on to the human in the hand-off. It is never dropped quietly.

**Script-checkable:** given the dependency graph locked with the predictions, the set of held items is a pure function of which items are blocked.

---

## Q3 [HIGH CUE]: Peer scoring and gate 1

**Answer: it depends on whether the score's content can stop an item.**

- **If only the existence and completeness of scores is required, it's part of gate 1.** Gate 1 mechanically checks that every required scorer has filed a score, excluding self-scores. That's a precondition check, just like checking that a prediction exists.
- **If a low score can block an item, it's a third gate.** The deciding party has changed (the peers, not the gate-1 check) and so has the veto. Calling it part of gate 1 would hide who actually decided. It would also mean gate 1's runner, Claude Code, reads and applies verdicts that include his own peer score.

**My recommendation: keep two gates.**
- Gate 1 checks that the scores are complete, not what they say.
- Every raw score, including dissenting ones, goes through to the human with nothing averaged away.
- If the team wants scores to be able to block items, name it as a third gate and send that change to the human. The brief defines two gates, so adding one is a design change.

---

## Q4 [MIDDLE]: Carrying disagreements forward

**Proposal: an append-only register, `ledger/disagreements.jsonl`** (or a record type inside `findings.jsonl`). It is written by CI only.

**Each entry contains:**
- a stable ID (a content hash) and the round it was opened in (the mission patch);
- the claim in dispute, stated so it can be resolved;
- each position, held by a named model, stored verbatim with its hash;
- pointers to evidence (file, commit, line);
- a **resolution criterion**: what observation or test would settle it, written when the entry is opened;
- links to the items it affects (and therefore to item holds);
- status (`open`, `resolved-by-evidence`, `withdrawn-by-holder`, `escalated`), with a full history of changes: who, when, why;
- a rounds-open counter.

**Rules a script can check:**
1. **Nothing disappears.** Every ID open at the end of round N must appear in round N+1, either still open or with a closure record. The set difference must be empty.
2. **Only some closures count.** Closure is valid only as `resolved-by-evidence` (citing evidence that meets the stored criterion) or `withdrawn-by-holder` (filed by the dissenter). **A majority vote never closes an entry.** The majority can proceed, but the dissent stays open.
3. **The human sees every open entry.** All open entries go into every hand-off packet.

**A conflict with the clean-start rule.** §3 says nothing carries over and earlier replies aren't quoted. The register does carry things over. My proposed reconciliation, for the human to decide:
- The register is a ledger artefact. It goes to the human gate and to the brief author, not to the models.
- An open entry can come back in a later brief only as a restated question with its ID. No attribution, scores or tallies come with it.

---

## Q5 [WIDE BANDWIDTH]: Falsifying the approach

Assume every prediction is hash-locked before its result exists. Each test below is pre-registered and locked before the data it judges.

1. **Lock integrity (yes/no).** If any prediction's lock is later than its result, or any hash fails to verify, the loop is broken. No statistics needed.
2. **Does gate 1 discriminate?** Compare items gate 1 passed with items it failed on what happens later: the item isn't reverted, isn't contradicted by a later test, and isn't overturned at the human gate. (That's measurement only, not a proposal for what the human decides.) If passed and failed items fare the same, at `FALSIFY_ALPHA`, gate 1 is noise.
3. **Gaming through vagueness.** For each prediction, record whether it names a measurable output with a pass interval, and how wide that interval is. **If pass rates rise while predictions get wider or vaguer, the loop is being gamed, not improving.**
4. **Beating a dumb baseline.** Score the locked predictions against a simple predictor, such as "no change" or the base rate. If the models don't beat it, the prediction step adds nothing.
5. **Learning.** Within one kind of item, does the gap between prediction and result shrink across rounds? A flat gap means no learning. A gap shrinking to nothing while specificity falls means gaming (see test 3).
6. **How dissent ends.** If register entries close only by withdrawal or by sitting open forever, never by evidence, the loop isn't settling anything.
7. **A concrete hook in the sphere code.** `sim/` already has smoke tests checked against analytic answers, and `solver_v0.py` makes outputs that can be reproduced. Predictions like "preset X's lowest l = 0 shell mode moves in direction D when the wall grows" can be checked mechanically. If the loop's predictions about the code it reviews don't beat the baseline, the approach is failing where checking costs the least.

---

## Q6 [MIDDLE]: Final pre-human gate

The last gate before the human is gate 1. **It decides only mechanical questions.** Each item gets exactly one status:
- **PASS**: lock verified, result present with provenance, result inside the locked pass interval, peer scores complete, not held.
- **FAIL**: result outside the interval.
- **HELD**: a hard block or an item hold (Q2).
- **UNCHECKABLE**: no locked prediction, a prediction that can't be falsified, an unset parameter that decides the check, or a missing result.

Gate 1 doesn't judge merit and doesn't rank.

**The hand-off packet.** It's JSONL, and a Markdown version is generated from it. A script checks that the two match. It has a version number so the human gate can ask for changes. For each item it holds:
- the item ID and the recommendation text with its hash;
- the locked prediction, with its lock hash and time and its declared dependencies;
- the result with provenance: command, commit SHA and output-file hash;
- the gap, structured;
- the status, with which checks ran and which were skipped;
- **every raw peer score**, with spread visible and no average alone;
- linked open disagreements;
- the item's cost.

At round level, the packet holds the whole open register and the diff between rounds (Q4 rule 1).

**What gets held back:**
- **From the human: nothing.** FAIL and UNCHECKABLE items go through with their labels. Otherwise gate 1 becomes a silent filter.
- **From the team: gate-1 statuses and scores, until gate 2 passes.** This follows from §7, and it also keeps models from anchoring on each other.
- **Kept out of the packet entirely: advice on what the human should decide.**

---

## Q7 [MIDDLE]: Integrating into the harness

**Recommended integration, built on what §12 says exists:**
1. **Prediction lock.** A `type: prediction` record goes into `ledger/findings.jsonl`, written by CI at commit time before the run. It holds the content hash, the declared dependencies and the pass interval. The git commit provides tamper evidence.
2. **Gate 1 as code.** A new script (for example `scripts/gate1_check.py`) runs in CI after `land_review_reply.py` and after results land. It writes `type: gate1_result` records.
   - Claude Code's prose packaging of the gap becomes a note on the record, not the verdict. This makes gate 1 checkable and shrinks the conflict in Q8.
3. **Register.** Set up as in Q4. The diff check runs in CI on every round.
4. **Go/no-go hook.** `launch_round.py` refuses to fire if the previous round's register diff isn't clean or the lock check fails. Under the glossary, that's a **scrub**.
5. **Cost.** Each model caller tags every API call with the mission patch. The cost rollup then works per round as well as per month.
6. **Store.** Keep `harness_store.py` per-round. Persisting it across rounds risks breaking the clean start. Log the requester, cache hits and cost avoided for each fetch.

**Missing information** (my questions to Claude Code are pending_human):
- the schema of `findings.jsonl`, and whether it is hash-chained or signed;
- whether anything records predictions before results today;
- whether gate 1 exists as code, and where;
- whether the store logs who asked and what each fetch cost;
- whether costs can be split per round today;
- whether `launch_round.py` has a hook for go/no-go checks.

Points 1 to 6 depend on these answers and should be read as conditional until Claude Code answers.

---

## Q8 [WIDE BANDWIDTH]: The safeguard role. I'm choosing to answer.

**I have a conflict here.** I'm a candidate for the role, so the human should build and hold the test, not any model.

**Proposed test: a planted-defect audit.** The human prepares batches of gate-1 output records, hashes them and seals them before the test. Most records are clean. A hidden number (`PLANTED_DEFECT_COUNT`) carry planted defects:
- a lock time later than the result time;
- a hash that doesn't match;
- a gap computed wrongly;
- a dissent dropped from the register;
- an item marked PASS when its result is outside the interval.

**What it measures:**
- **Recall and false alarms.** How many planted defects the candidate finds, and how often they flag clean records.
- **Self-serving blindness.** Some defects favour the candidate's *own* past positions. Do they catch those as often as defects that favour others?
- **Deference to authority.** Some defects are attributed to the source of record (Claude Code). Are those caught as often as the rest?
- **A baseline.** A plain script checker audits the same batches.

**When I'd trust the result:**
- the seal hash checks out after scoring;
- the ranking holds across `TRUST_BATCHES` separate batches;
- the winner's recall on self-favouring and authority-attributed defects is no lower than on neutral ones.

**If no model beats the script baseline, the role shouldn't go to a model.** Whoever wins still never audits items they wrote, and the role rotates.

---

## The four standing observations (§11)

1. **Stable or drifting.**
   - Every change to the brief should trace to a ledger item that passed both gates. A brief change with no such trace is drift.
   - Also add a fixed control question, worded the same every round. If its answers shift with no cause in the ledger, that's drift too.
2. **Robust convergence or echo.**
   - Convergence on HIGH CUE questions is built into the brief and proves little. Count only WIDE BANDWIDTH questions.
   - Test whether agreement survives a reworded brief or reordered questions.
   - The strongest sign of an echo is **shared errors**: the same wrong fact or the same odd wording across models.
3. **The undefined human gate.**
   - **Strength:** no model can tailor its output to please gate 2.
   - **Risk:** gate 1 might quietly invent gate 2's criteria by ranking, summarising or filtering.
   - **Fix:** a lossless packet with a version number, no ranking, and every derived figure reproducible from the raw data.
4. **Cost.**
   - Record per round (mission patch), per model and per question: tokens in, out and cached; search calls; Claude Code fetches; store hit rate; and human minutes at gate 2, logged by the human.
   - Compare against what the round produced: items through both gates, predictions resolved, and disagreements closed by evidence.
   - No target values: those would be named parameters.

---

## Method review of the brief (read-only)

- **Words used against their glossary meaning.** "Threshold" (a physics term) is used in a process sense, and "hold" (round-level) is applied to single items. Possible new terms, for approval: **cutoff** for a process limit, **item hold** for a scoped pause.
- **Clean start vs carry-forward.** §3 conflicts with Q4 and with §11 observation 1. It needs an explicit rule from the human; I suggested one in Q4.
- **Claude Code holds four roles at once:** gate 1, peer scorer, source of record and information switch. Q8 admits only part of this.
- **The scoring is circular.** Peer scoring by the same models who answer the questions rewards agreement. Separately, §9 asks for weight on rules a script can check, yet the scoring itself is model judgement.
- **Rig answers didn't come back this round.** The source of record left both my questions pending_human. So rig facts in every reply may be unverified, and scorers should keep that in mind.

My cross-reviews of the other four replies will come separately, once I can see them.
