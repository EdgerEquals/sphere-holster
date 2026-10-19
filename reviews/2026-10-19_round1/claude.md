# Claude — review round 1 (2026-10-19)

**Settings:** claude-sonnet-5-5, Anthropic Messages API, output_config.effort=medium, max_tokens 6000 (incl. thinking), streamed

**Prompt:** [`prompt.md`](prompt.md) (identical for all four models; DESIGN_STATE.md at commit ccbd86c).

- Attempt 1: started 2026-10-19T04:55:01+00:00 UTC, max_tokens 6000, input 3418 (cached 0), output 1082 (reasoning 0), stop `end_turn`, 9.2 s, cost $0.01766

## Raw reply (verbatim)

VERDICT: FAIL

Reasons: the locked items contradict each other, the open list, and the viewer caveats in several places.

- **Open vs Locked on the quartz shell.** The lock shell is "Locked" but Open #1 asks which shell to use. The shape is "a sphere unless Danny says tube" while Open #1 also asks sphere or tube. The Alternative and Test shell are also still live.
- **Locked values that Open also reopens.**
  - The electrode scheme is locked as needing a central electrode or an external field, while Open #8 asks which one.
  - The fill amount is "open" inside Locked and again as Open #7.
  - The BTO thickness is "set by heat transfer" while Open #3 leaves it undecided.
  - The tourmaline thickness is locked at about 5 µm while Open #4 trades it against scattering.
- **3.236 MHz is unsupported.**
  - The viewer says the formula and sound speed were never recorded.
  - A slab cL/2t would need cL of about 6110 m/s, whereas the cited VRH value is 6048 m/s and Danny's is 5900 m/s.
  - It matches the spherical 1S0 mode only with 5900 m/s, so it is locked on an unverified basis.
  - The 7.5 kW cap and the 48 MPa figure inherit that uncertainty.
- **1.87 MHz vs 1.855 MHz.** The viewer's VRH calculation gives 1.855 MHz, so the locked "about 1.87" depends on which sound speed is chosen. The sound-speed choice itself is not locked.
- **Golden-ratio shift.** The boundary is "HHO into the quartz", yet the BTO's "first φ step starts at its outer edge" and nothing outside the quartz is modelled. These are inconsistent in scope.
- **Curie point.** It is "crossed at about 10 W" while the heat path is open, and BTO tuning relies on capacitance that changes across the Curie point.
- **Electrode and heat statements.** Locked says the inner-wall metal film screens the gas, while Open #5 says Ti/Pt electrodes are the main heat source and block light. The layer in which the electrodes sit is undecided.
- **Minor.** The Information layer says "12 knee harnesses" but the knee harness details are open. The 6.78 mm φ size "stays under 48 MPa at 10 kW" is also unsupported, since its own frequency is not given.

Top three risks:
1. The foundational 3.236 MHz and 7.5 kW values lack provenance, and everything downstream (power, stress, drive) depends on them.
2. Locked and Open overlap, so tools will not know which items are binding.
3. The thermal path is unresolved, and the test shell exceeds HHO autoignition at 1 W. This threatens the Curie, phosphor-saturation and safety claims. The discharge thresholds also rest on placeholder drift speeds.

Improvement: Split "Locked" into "Locked" and "Provisional/default", and move every item that also appears in Open into the latter. Record the derivation (formula, cL, source) for each frequency. Lock one sound-speed set and quote every mode frequency to a stated precision derived from it.
