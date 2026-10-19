# Round 4: Claude (claude-sonnet-5-5)

max_tokens 16000, started 2026-10-19T06:14:05+00:00 UTC, 10.0 s. Tokens in 1539 (cached 0), out 957 (reasoning 0), 458 words. Cost $0.0126. Retired-item hits: 0.

Prompt: `prompt_paid.md` (same + labelled Kimi/DeepSeek SOLUTION lines).

Raw reply, verbatim:

---

SOLUTION: Require a CI-written execution receipt in the ledger before any paid review of a harness component, and label reviews of unbuilt components as "spec-review," a separate, cheaper class.

**What it is**
Each review trigger checks the ledger for a receipt: commit sha, component name, test or smoke result, and the artifact digest. The receipt is written by CI, not by Cursor or a reviewer.

- If a receipt exists, the review runs as a normal "code-review." Its findings can go to issues, and its scores count toward reviewer scorecards.
- If no receipt exists, the review is tagged "spec-review." It audits the Drive spec against DESIGN_STATE and the retired list. It is free of any claim that code exists, and it is excluded from precision/recall scoring against code.

The ledger schema gets one new field, `review_class`, plus a `receipt_sha` link. The schema is versioned, so this is a minor bump.

**Why**
The gap is mainly a labeling and trust problem, not a sequencing one. Auditing a spec is legitimate. The danger is a finding on "the coordinator" that reads as if the coordinator exists, which pollutes the ledger and the cost rollup. A receipt makes "built" mean "CI proved it ran," and it reuses machinery that already exists: the ledger, the smoke tests, and the locked-value suite.

I partly disagree with Kimi's stub approach. Stubs with locked I/O schemas are useful, but they invite reviewers to audit hollow code, and a passing stub could be mistaken for a built harness. Stubs are worth adding later as the way a component earns its first receipt, once the schema is settled. They are not the gate.

**Cost**
- About one small workflow step and one schema field.
- A few hours of Cursor work.
- No new paid calls. Spec-reviews can run through the cheap /kimi-check and /deepseek-check channels first, so paid spend should go down.
- The monthly rollup can split spend by review class, with October at about $0.87 as the baseline.

**Risks**
- Receipts can be gamed by a trivial smoke test. Mitigation: the receipt must reference a named test in the locked suite, and the planted-mistake fixture should include a "fake receipt" case.
- Spec-reviews may stagnate into repeated findings. The sha256 dedup limits this, and a cap on spec-review rounds per component would also help.
- Reviewers may ignore the class label. The prompt must state the class, and the scorecard must exclude cross-class findings.
- The receipt check could block legitimate cross-cutting reviews, such as reviews of DESIGN_STATE. Allow an explicit `spec-review` dispatch input to cover those.

Sequencing rule going forward: a harness component moves from spec-review to code-review only when its first receipt lands. Until then, nothing downstream is described as built.
