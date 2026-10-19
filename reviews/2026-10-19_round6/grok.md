<!-- landed: reviewer=grok · model=grok-4.3 · channel=ad-hoc /tmp/round6-run/grok_run.py (/responses) · generated_utc=2026-10-19T14:50:01Z · source=/tmp/round6-run/grok/reply.md -->

**1. Threshold proposal (automated gate)**

Measure: relative deviation on the primary lock metric the solver reports for the geometry (sharp vs density-guaranteed lock sharpness or highest per-mode energy W_n).  
Value: escalate if |predicted − observed| / predicted > 0.15 **or** model-stated on that prediction < 0.60.  
Both conditions are evaluated by Claude Code against the prediction package before the human gate sees it. This is a single numeric gate that can be coded directly from solver JSON output.

**2. Sequencing recommendation**

Agree with the proposed order:  
threshold definition + peer scoring → human gate (Edger_Equals) approval → only then round-7 4 W sweep.  
Reason: the automated gate cannot be run or validated until the threshold exists; running the sweep first would create un-gateable artifacts and waste executor cycles. No alternate order is needed.

**3. Peer-scoring axes (ready for other models)**

I will score the other three proposals on:  
- Clarity (one unambiguous numeric rule)  
- Falsifiability (exact comparison the solver already emits)  
- Practicality (Claude Code can implement without new solver changes)

**4. Teamwork score (initial)**

Converge (so far). The kickoff has already removed the round-6 sweep task and stated the two-gate rule clearly; no model has re-opened locked geometry or retired items.

**5. Process recommendations (next round seed)**

- Hand-off rule: every model must include its exact threshold expression (measure + numeric value) in its first reply; no prose-only proposals.  
- Task split: Kimi/DeepSeek do the retired-item and units scan on any new JSON; Claude/Grok only review physics and ledger entries.  
- Automation: add a one-line CI job that runs the chosen threshold expression against a dummy prediction package and writes pass/fail + count to `ledger/pending/`.  
- Receipt: no ledger staging file accepted unless it contains the string “suite: N passed”.  
- Human-gate packet: always include the raw prediction JSON, the computed deviation, and the value so Edger_Equals sees numbers, not summaries.
