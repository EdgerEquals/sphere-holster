# Round 7 kickoff — conversation design (inter-model protocol)

**Branch:** `holster-loop-2026-10-19`  
**Do not push** unless the caller says so. This file is documentation only — it does not run tests or a sweep.

**Round 7 scope:** design how the four models (**Kimi, DeepSeek, Claude, Grok**) talk to each other — cross-review flow, peer scoring in practice, where the automated gate sits inside the conversation, and how feedback fan-out works. **No amplitude sweep in this round. No solver runs. No Claude Code sweep work.**

**Round 6 (done / in flight):** threshold debate — measure + value, sequencing recommendations, peer scoring into the ledger, two-gate rules. Round 7 assumes that loop shape and does not re-open the threshold definition itself (unless Edger_Equals reopens it).

**Round 8 (not this kickoff):** the **4 W** (`drive_W=1`) amplitude sweep on the rarefied core. **Round-8 hold:** the sweep is kicked off **only after** round 7’s protocol is designed, written up, and **approved by the human gate (Edger_Equals)**. See §2 and the deliverable note in §6.

Core geometry remains locked for later rounds (do not re-open here): bubble **0.57295 mm**, wall **1.43463 mm**, tourbillon **9.12441 µm**, fill **0.1044 × ambient** (HHO 2:1), window **1 Hz–50 MHz**.

---

## 1. Why this round exists

Round 6 locked *what* the loop decides (threshold first) and *that* there are two gates. Round 7 locks *how the four models converse* before anyone pays for a sweep or lets Claude Code execute recommendation checks at scale.

Without an explicit protocol:

- Paid models may each re-read the full shared context four times.
- Cross-review can become four pairwise full reads instead of a cheap compiled pass.
- Claude Code’s automated gate can sit “outside” the conversation or, worse, rubber-stamp recommendations that include its own Claude-side voice without a clear peer path.
- The human gate may receive an unstructured dump instead of a prediction-versus-result package.

Round 7’s job is to design that protocol **before** round 8.

---

## 2. Round 8 hold — 4 W amplitude sweep (deferred)

**Round 7 has no sweep work.** Do not run `drive_W=1` sweeps, single-point drive smokes for kickoff, or write `drive_4W_*.json` / `geometry_drive_4W_sweep_v0.json` as round-7 deliverables.

The **4 W** (`drive_W=1`; 1 W × four domains) amplitude sweep is **round 8**. It starts **only after**:

1. Round 6’s threshold (measure + value) is settled or explicitly waived by **Edger_Equals**,  
2. Round 7’s **protocol document** exists and is **approved by the human gate (Edger_Equals)**, and  
3. A separate `reviews/…_round8/` kickoff (or addendum) carries launch commands and artifact paths.

Until then, treat any sweep instructions in older drafts or in prior prompts as **deferred to round 8**.

---

## 3. Sequencing reminder (unchanged from round 6)

| Step | Round | What |
|---|---|---|
| 1 | **6** | Threshold debate (measure + value), sequencing asks, peer scores → human gate settles threshold |
| 2 | **7** | **This kickoff** — conversation / protocol design (economics required) → human gate approves protocol |
| 3 | **8** | **Only then** — 4 W (`drive_W=1`) amplitude sweep on the rarefied core |

Two gates from round 6 still apply to any later feedback loop (**automated Claude Code → human Edger_Equals → only then feedback**). Round 7 designs *how conversation and fan-out sit around those gates*; it does not invent a third gate or remove either existing one.

---

## 4. Design questions (team must answer)

Give **every** model the same brief for this round. Scope override: **conversation design / protocol first; no sweep.**

The team (**Kimi, DeepSeek, Claude, Grok**) should propose and debate concrete answers to:

1. **Sharing findings** — Do models reply **directly** to each other (threaded / pairwise), or do they write into a **compiled summary** that others read? When is each mode allowed?
2. **Cross-review order** — Who reviews whom, in what order, and after which artifacts exist? Can cheap filters finish before paid models start cross-review?
3. **Peer scoring in practice** — How are scores collected (axes, format, where filed)? How do peer scores of threshold proposals (and later of protocol proposals) land in the ledger without each model scoring itself?
4. **Automated gate inside the conversation** — How does **Claude Code**’s automated gate (prediction check + threshold TBD from round 6) sit *inside* the loop so it does **not** check its own recommendations unchecked? What peer or human path covers Claude-side recommendations before feedback fans out?
5. **Human gate packaging** — Exactly what does **Edger_Equals** receive as the **prediction-versus-result package** (fields, files, one-pager vs full dumps)? What is held until sign-off?

Capture replies under this folder (e.g. `reviews/2026-10-19_round7/{kimi,deepseek,claude,grok}.md` and/or a shared debate note). The human gate decides what becomes protocol.

---

## 5. Economics — requirements, not afterthoughts

These are **design constraints**. A protocol that ignores them is incomplete for round 7.

| Requirement | Meaning |
|---|---|
| **Tiered work** | **Kimi** and **DeepSeek** act as **cheap filters** first. Escalate **only interesting findings** to **Claude** and **Grok**. Paid models should not be the first pass for rote consistency / units / retired-item scans when a cheap filter can do it. |
| **Cached shared context** | Brief, `DESIGN_STATE`, and solver summary (when one exists) are paid **once**, then reused — **not** re-injected and re-billed four times as four independent full contexts. |
| **Batched cross-reviews** | Prefer a **compiled summary** of cheap findings for paid cross-review, instead of each paid model reading all three other full replies separately. |

The protocol doc must say how each requirement is enforced (who compiles, when cache is refreshed, escalate criteria for “interesting”).

---

## 6. Deliverable — protocol document (round 8 depends on it)

**Round 7’s deliverable** is a protocol document, e.g.:

`reviews/2026-10-19_round7/protocol.md`

That file (once drafted from the team debate and **approved by Edger_Equals**) is what **round 8’s sweep kickoff depends on**. Do **not** create `protocol.md` in this kickoff commit — only design and debate toward it. Round-8 kickoff should not launch until the protocol exists and the human gate has signed off.

Suggested protocol sections (team may refine): sharing mode, cross-review order, peer-scoring procedure, automated-gate placement + anti-self-check rule, human-gate package schema, economics enforcement, launch/fan-out commands for later rounds.

---

## 7. Four-model role assignment (this round)

| Model | Role this round | How to reach (typical) |
|---|---|---|
| **Kimi** | Cheap rote + protocol proposals: consistency vs DESIGN_STATE / this kickoff; flag expensive patterns | `python scripts/review_kimi.py` with round-7 brief / kickoff scope |
| **DeepSeek** | Same cheap filter as Kimi (independent); escalate only interesting protocol risks | `python scripts/review_deepseek.py` with round-7 brief / kickoff scope |
| **Claude (chat)** | Paid / read-only method review of the **conversation design**; cross-reviews others’ protocol proposals; never runs solver or commits | Holster Claude channel / Messages API (see prior `reviews/2026-10-19_round5/claude_run.py` pattern) |
| **Grok** | Paid claim / process cross-check against DESIGN_STATE + kickoff + economics requirements; cross-reviews the other three | `python scripts/review_grok.py` with prompt context |
| **Claude Code CLI** (executor, not a fifth “review voice”) | May stage docs / local commits for round-7 protocol drafts; **self-check** before every commit; **does not start the round-8 sweep**; does not invent process that contradicts round-6 two-gate rules | Box CLI (`claude`); **do not push** without caller |

Suggested order for **round 7:** suite green (if any docs change requires it) → fan-out design questions → cheap filters first → escalate interesting protocol proposals to Claude/Grok → peer scores on protocol proposals → draft `protocol.md` → **human gate approves** → **then** round 8 may be drafted.

---

## 8. Where outputs land

| Artifact | Path |
|---|---|
| This kickoff | `reviews/2026-10-19_round7/kickoff.md` |
| Per-model replies | `reviews/2026-10-19_round7/{kimi,deepseek,claude,grok}.md` |
| Teamwork / peer scores | `reviews/2026-10-19_round7/*_teamwork.md` or ledger staging |
| **Protocol (deliverable)** | `reviews/2026-10-19_round7/protocol.md` — **after** debate; not created by this kickoff alone |
| Ledger staging | `ledger/pending/*.jsonl` when filing protocol findings / peer scores |
| Sweep / amplitude JSON (**round 8 only**) | repo root `drive_4W_*.json` / `geometry_drive_4W_sweep_v0.json` — **not** round-7 deliverables |

---

## 9. Two gates (reference — unchanged from round 6)

There are **two gates** in the loop. Claude Code’s gate is **automated**; the human gate **sits above it**. **Nothing reaches the team as feedback without passing both.**

| Gate | Who | Role |
|---|---|---|
| **(1) Automated gate** | **Claude Code** | Runs each recommendation against the model **with a prediction**; holds the **threshold** (deviation vs confidence — from round 6 / human approval). Packages the prediction-versus-result gap. |
| **(2) Human gate** | **Edger_Equals** | Eyeballs that gap **before** any feedback feeds back to the team. Also approves round 7’s **protocol** before round 8. |

Round 7 must specify how gate (1) is placed so Claude Code is **not** the sole unchecked reviewer of Claude-side recommendations, and how gate (2) receives a clear package. Skipping either gate remains a no-go.

---

## 10. Go / no-go checklist (declare “round 7 started” only if all GO)

| # | Check | GO if… |
|---|---|---|
| 1 | Branch | On `holster-loop-2026-10-19` with this kickoff present |
| 2 | Scope | Conversation design only; **no** 4 W sweep, no solver amplitude work |
| 3 | Round situating | Round 6 = threshold; round 7 = protocol; round 8 = sweep — understood |
| 4 | Round-8 hold | Sweep waits on protocol design **and** human-gate approval of that protocol |
| 5 | Design questions | §4 questions ready to fan out identically to all four models |
| 6 | Economics | Tiered work, cached shared context, batched cross-reviews treated as **requirements** |
| 7 | Two gates | Automated (Claude Code) then human (Edger_Equals); no third gate invented; no gate removed |
| 8 | Deliverable path | Team knows deliverable is `reviews/2026-10-19_round7/protocol.md` (draft after debate) |
| 9 | Models | Kimi, DeepSeek, Claude (chat), Grok each have the **same** round-7 scope (no sweep) |
| 10 | Outputs | Round-7 paths in §8 agreed; no push without caller |
| 11 | Retired | No electrodes / retired items reintroduced in protocol proposals |
| 12 | Four pings (when launching) | If caller says “send it” / “launch round 7,” all four pings fire as one job |

**NO-GO:** starting the round-8 4 W sweep before protocol approval; treating economics as optional; skipping the human gate on the protocol; inventing process that contradicts round-6 two-gate order.

When rows 1–11 are GO for **starting** the design debate (12 = pings fired when launched), the coordinator may declare: **Round 7 started** — models design the inter-model conversation protocol; **round 8 sweep waits** on `protocol.md` + Edger_Equals approval.
