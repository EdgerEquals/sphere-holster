# DESIGN_STATE split copies (read-only mirrors)

`DESIGN_STATE.md` at the repo root is the master and the single source of truth. The files here are read-only copies of it, split at `##` section boundaries so that each file stays under 50 KB. Do not edit them; any change goes into the master.

Taken 2026-10-22 AWST from the working copy of `DESIGN_STATE.md` on branch `holster-loop-2026-10-19` (81 207 bytes, sha256 `65fa5c51c73684085f07fe30b28f4b44c9696f1d6c428c0cd0fd3fa57c3e9ab9`). Each copy opens with a two-line mirror note; the rest is the master's text unchanged. If the master has changed since, the master wins.

| File | Master lines | Covers | Size |
|---|---|---|---|
| [DESIGN_STATE_2026-10-19_part1.md](DESIGN_STATE_2026-10-19_part1.md) | 1–285 | Header, Locked, Open, Retired (never reintroduce), information layer and harness architecture, simulation stack, Danny's round-5 decisions, intended model behaviour, and dated sections of 2026-10-19 up to "Note: boundary pairs" | ~30 KB |
| [DESIGN_STATE_2026-10-19_part2.md](DESIGN_STATE_2026-10-19_part2.md) | 286–558 | Sections dated 2026-10-19 from "Future item: EMF build: E-B coupling" to "Decision: Claude in two roles" | ~37 KB |
| [DESIGN_STATE_2026-10-21.md](DESIGN_STATE_2026-10-21.md) | 559–623 | Sections dated 2026-10-21, from "Decision: joint-step wording approved" to "Decision: gate 1 release" | ~14 KB |

Part 1 holds the Locked, Open and Retired lists. Read it first.
