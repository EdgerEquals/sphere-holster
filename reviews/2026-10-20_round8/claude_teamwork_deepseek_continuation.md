<!-- continuation: reviewer=claude · model=claude-opus-5-5 · channel=scripts/review_claude.py tool loop (scratch runner) · run_id=teamwork-continuation-20261020T142019Z-claude-deepseek · generated_utc=2026-10-20T14:20:19Z · finish=end_turn · source=/tmp/r8_claude_deepseek_cont/claude/ping.json -->

# Claude's cross-review, continued: the DeepSeek section

**What came back:** I asked Claude Code (`ask_claude_code`) again and this time he answered, with file and line references. My `request_info` (scope `rig`) is still `pending_human`. Everything below rests on what Claude Code read.

## DeepSeek's rig claims, checked

| DeepSeek's claim | Result | Evidence (Claude Code) |
|---|---|---|
| `scripts/ledger_score.py` scores reviewers against planted mistakes | **Confirmed** | It puts a planted-mistake fixture (`ledger/planted/v1/`) into a throwaway commit and runs the normal review scripts against it. It then scores catch rate and accuracy into `ledger/scorecards.*` (`ledger_score.py:2-12`, `:60-81`, `:187-206`, `:175-179`). |
| Each model's cross-review lands as `{model}_teamwork.md` | **Confirmed** | `launch_round.py:315-330` sets the land stem to `{m}_teamwork`. `land_review_reply.py:251-299` writes `<round-dir>/{stem}.md`. |
| In those files, each model gives peers PASS/FAIL with a one-line reason | **Wrong for this round** | Only the old brief format asks for PASS/FAIL (`launch_round.py:98-126`, `:119-123`). From round 8, briefs come from `round_config.json` and the cross-review brief has no PASS/FAIL section (`launch_round.py:74-89`, `:207-211`, `:233-252`). In both formats it's a request in the prompt, not something checked on the landed file. |
| `gate1.py` reads `<round-dir>/predictions.jsonl` and writes `gate1/{summary.md,items.jsonl,gaps.jsonl}` | **Confirmed, with a limit** | It reads the file only to hash it and never parses the contents (`gate1.py:38-39`, `:78-80`, `:83-93`). The outputs are written via `write_new`, which archives older versions (`gate1.py:188-203`). |
| `launch_round.py` locks `predictions_sha256` into `run.json` when the round fires | **Confirmed, with conditions** | The lock happens only in config rounds, and only if the predictions file exists (`launch_round.py:537-549`, `land_review_reply.py:157-173`). Otherwise nothing is locked. |
| Today gate 1 only checks the hash and marks items `gate1_unverifiable` | **Confirmed** | `gate1.py:93` |
| No code writes predictions | **Confirmed** | `predictions.jsonl` is only mentioned or hashed (`gate1.py:38`, `launch_round.py:538-541`, `handoff.py:30-31`). |
| Peer scores have no structured link to items | **Confirmed** | The teamwork files are free text. `items.jsonl` and `handoff_log.jsonl` don't parse peer verdicts (`gate1.py:171-173`, `handoff.py:44-48`). The only verdict parser in `ledger_lib.py:300-311` reads a reply's own `VERDICT:` line, not scores given to peers. |

**Two more rig facts that affect DeepSeek's design:**
- **`ledger_score.py` already ignores deferred and superseded findings** (`:122-124`, `:130-132`). DeepSeek's disagreement index has its own `superseded` and `dropped` closures. If that index ever uses the existing ledger statuses, it inherits the same way of dropping dissent quietly.
- **The rig uses "gate 2" for a presence check.** `launch_round.py:571-575` calls the check that every `*_teamwork.md` file is present and current "gate 2". That clashes with the brief, where gate 2 is the human gate. It's worth a vocabulary check, and it matters for any Q3 answer (DeepSeek's included) that places peer-score checks inside gate 1.

## DeepSeek: 7.0 (up from 6.5)

**Strengths**
- **Its Q7 is the most accurate rig plan among the replies that didn't read the code.** Nearly every fact holds up. It also found `ledger_score.py` and the teamwork files, which Claude Code's own reply didn't cover. Its list of what's missing (nothing writes predictions, no comparison step, no structured peer scores) is confirmed point by point.
- **Q4's traceability check is enforceable.** If an open entry is missing from a later hand-off, gate 1 refuses the round.
- **The "constitution snapshot" hash** (standing observation 1) is a good mechanical drift check.

**Weaknesses (unchanged except the last)**
- **Q2 fails open.** A missing `depends_on` holds only that item, so leaving the field out lets a dependent item escape the hold.
- **Q4's `dropped` closure has no limit on who can file it.** Any model can close a dissent with a reason.
- **Number rule:** "dominating the record" in Q5, said twice, is a majority cutoff with no named parameter. That breaks its own Q1.
- **Q5's null model** ("predict whatever the recommendation asserts") is unclear as a baseline. Q7's "similarity/negation" comparison for prose relies on judgement. Q8 has no baseline and no repeat trials.
- **Q7 step 3 would fail on this round's files.** It parses PASS/FAIL lines from `{model}_teamwork.md`, but from round 8 the brief doesn't ask for them and nothing enforces them. The plan needs a structured score format before that step can work. This replaces my earlier "unconfirmed rig claims" deduction.

**Why the score changed:** I had deducted for two rig claims I couldn't confirm. One is now fully confirmed, and the other is right about the files but wrong about what's in them this round. That error is small, and the rest of DeepSeek's rig grounding proved better than I'd assumed. So I raised the score by half a point. It stays below Grok because the weaknesses that cost the most are unchanged: an item can escape a hold by leaving out `depends_on`, any model can close a dissent as `dropped`, and Q5 has an unnamed cutoff. Those weigh more than rig accuracy under the scoring guidance.

**Updated table row:** DeepSeek | **7.0** | Its rig plan is mostly confirmed (one round-8 error on PASS/FAIL), but leaving out `depends_on` lets dependent items escape a hold, any model can close a dissent as `dropped`, and "dominating" is a cutoff with no named parameter.