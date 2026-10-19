# Kimi — review round 1 (2026-10-19)

**Settings:** kimi-k2.6, api.moonshot.ai chat completions, thinking on (default), max_tokens 6000 then retry 12000 (incl. reasoning), streamed

**Prompt:** [`prompt.md`](prompt.md) (identical for all four models; DESIGN_STATE.md at commit ccbd86c).

- Attempt 1: started 2026-10-19T04:55:35+00:00 UTC, max_tokens 6000, input 2191 (cached 0), output 6000 (reasoning 5999), stop `length`, 125.5 s, cost $0.02608 — **empty reply (all tokens spent on reasoning), retried**
- Attempt 2: started 2026-10-19T04:57:40+00:00 UTC, max_tokens 12000, input 2191 (cached 2048), output 5964 (reasoning 5557), stop `stop`, 122.9 s, cost $0.02432

## Raw reply (verbatim)

VERDICT: FAIL

Layer 1 locks that “nothing outside the quartz is modelled yet,” while Layer 2 locks that the “first φ step starts at its outer edge”—a direct scope contradiction because the BTO outer edge lies outside the quartz. The electrode block is also self-contradictory: a continuous metal film on the inner wall “screens the gas,” which would block an external field from penetrating to ionise the HHO, yet “external field” is listed as a viable ionisation path alongside a central DBD electrode. Additionally, the 3.236 MHz “thickness mode” is inconsistently documented; the viewer notes it matches a spherical-shell 1S0 mode with cL 5900 m/s, whereas the slab formula implied by the label would require ~6110 m/s, and the original derivation was never recorded.

Top three risks or gaps:
1. Thermal collapse: The BTO Curie point is locked at about 10 W, while the quartz shell is rated for ~7.5 kW. With no defined heat path (Open #2, #3) and HHO autoignition reached at 1 W in still air, the stack has no credible thermal architecture.
2. Electrode–optical deadlock: Ti/Pt blocks light, which is the main heat source, but electrode placement (central, inner-wall film, or Layer 4) remains open. This couples discharge viability directly to thermal runaway risk.
3. Unverified acoustic foundations: Breathing and thickness modes are paper estimates with undocumented formulas; viewer caveats flag order-of-magnitude uncertainties in discharge thresholds and EM resonance limits that could invalidate the drive scheme.

One improvement suggestion:
Explicitly lock the electrode geometry—either a central DBD wire with the inner metal film as ground, or an external field with no continuous inner metal screen—and retire the inconsistent option, then document the exact acoustic model (slab vs. spherical shell) used for each locked resonance.
