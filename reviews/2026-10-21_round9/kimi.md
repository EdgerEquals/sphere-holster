<!-- landed: reviewer=kimi · model=kimi-k3 · channel=scripts/review_kimi.py --ping · generated_utc=2026-10-21T05:23:09Z · source=/workspace/ensemble-round8/Current/round9/run_2026-10-21_kimi_rerun/kimi/ping.json · run_id=primary-20261021T050438Z-7c9a22 · landed_utc=2026-10-21T05:28:03Z · finish=stop -->

# Kimi

Read this round: `MAP.md`, `solver_v0.py` (drive block, `run_case`, thermal/electric march, packaging, `main`), `tests/test_drive_1W.py`, `DESIGN_STATE.md` (drive + core sections), `docs/harness_context.md`, `solver_v0_output.txt`. Vocabulary doc read first as instructed.

## [HIGH CUE] Verdict

**ready with fixes** — the physics plumbing (`run_case(pre, ref, drive_W=1)`) exists and is unit-tested, but nothing in the code runs it or writes `drive_4W_*.json`, the packager would mislabel a driven run as "no source", and the electric 1 W is never deposited as heat (the run is thermally a 3 W run).

## [MIDDLE] What's missing

1. **Blocker — no sweep entrypoint or output writer.** `main()` only ever calls `run_case(pre, ref)` with the default `drive_W=0` (solver_v0.py:1452); there is no `--drive` argument, and the string `drive_4W` appears nowhere in the repo. The planned output files have no code path that produces them.
2. **Blocker — packaging mislabels a driven run.** `package()` hardcodes `source="none: no drive mechanism defined; nothing is injected into any domain"` (solver_v0.py:1314), the `state` dict (1313–1356) carries no `drive` block even though `run["drive"]` is built (1026–1033), and the JSON meta scenario (1461–1463) hardcodes "No source". A 4 W JSON written today would read as a zero run. (The raw `run_case` return is not JSON-serialisable either — it holds the `Thermal` object and numpy arrays — so the writer must go through `package()` or a new serialiser.)
3. **Blocker (or an explicit pre-run decision) — electric channel is not energy-conserving.** `drive_J_src_for_power` sizes J so the *implied* ohmic power ΣJ²/σ·V = 1 W (836–852), but no Joule-heating term ever enters the thermal solve: the heat vector is only `qo + q_ac + q_mag`, `q[0] += P_gas`, plus electrocaloric (1055–1062, 1071–1075). Steady deposited heat is ≈ 3 W, not the 4 W that DESIGN_STATE.md:535 states ("deposits 1 W into each of the four domains"). Consequence in the field: with σ_BTO = 1e-10 S/m (252), steady E ≈ J/σ ≈ 1e10 V/m in the film — ~240× the film's own `E_WORK` 42e6 V/m (224) — and no over-voltage/breakdown flag exists in the drive path (`E_WORK` is only used in the retired tank model at 775).
4. **Nice-to-have — the 1 Hz envelope is not wired.** `DRIVE_THERMAL_ENVELOPE_Hz` (809) is defined and never referenced again; the drives are constant in time. DESIGN_STATE.md:537 and the brief describe it as "a slow envelope modulating the drives". Either implement the modulation or fix the doc before the sweep is described as having it.
5. **Nice-to-have — no packaging-level test for the drive.** `tests/test_drive_1W.py` covers `run_case` well (split rule, per-mode W identity, 1 W per channel, window constants); nothing tests that drive metadata survives into output JSON, and nothing tests total deposited power.

## [WIDE BANDWIDTH] What would make a sweep result invalid

- **The missing electric watt (above).** Any reader summing "4 W in" against the temperatures is misled by construction; the thermal steady state is a 3 W state.
- **The ~10 GV/m BTO field.** At that field the film breaks down in any real device; the linear-σ march gives an E-field number that is physically meaningless and currently unflagged. Piezo/pyro/EC couplings computed on top of it inherit the unreality.
- **Cold-tuned drive against a hot core.** Drive frequencies and `Q_eff` come from the 293 K mode list (981–1003). At ~3 W the gas heats (the hot-gas recompute at 1085–1086 reports shifted modes but never feeds them back), c ∝ √T, so the true resonances move while the model keeps `W_n = P_src·Q_n/ω_n` at the cold frequencies — a built-in detune the result never shows.
- **Instant steady state.** `steady_mode_W` (829–833) assumes ring-up complete; fine while drives are constant (τ = Q/πf ~ ms), but silently wrong for slow modes if the 1 Hz envelope is ever applied, and it erases all transient information by construction.
- **Mode-list fragility changes the split.** Roots come from sign changes on a 20 000-point grid (df = 2.5 kHz, 604–619); the shell/gas classification uses a separate 4 000-point vacuum scan (df = 12.5 kHz, 967–972) and a 1 %-of-vacuum rule (973–980); `brentq` uses `xtol=1.0` Hz. A missed near-degenerate pair or a misclassified root changes N — and with equal split, every per-mode power and the whole acoustic result. base5 currently carries 129 bonded modes (`solver_v0_output.txt:4`), so 1/N ≈ 7.8 mW per mode.
- **Q_eff is material-Q only.** `mode_energy_stats` (648–666) uses MAT Q (quartz 2100 down to calorivac 20, phos_out 10); no radiation into the gas, no thermoelastic loss. Stored energies scale linearly with this Q, so an overestimated Q inflates W_n one-for-one.
- **Boundary and cap artefacts.** Full stack holds the outer surface at exactly 293 K (922, 940) — an ideal infinite sink no hardware has; both thermal solves clip at 3000 K (943, 498) and only the flag at 1311 tells you it happened.
- **Continuum gas conduction at the rarefied fill.** `gas_T_profile` (490–498) assumes continuum (comment cites Kn ~ 0.01 at 10 Torr); the fill is 79 Torr cold, but a ~700–800 K hot core raises the mean free path several-fold, pushing toward slip — gas-centre temperature could be materially off.
- **Chemistry is deliberately inert.** `chem_state` is called with `P_gas=0.0` (1022) so no conversion heat — correct today, but if anyone ever routes the thermal watt through chemistry, it double-counts against `P_gas`.
- **Fragile index mapping.** `Ws_for` maps per-mode power via `sorted(drive_freqs).index(f)` on exact float equality (999) — safe only because the same list is reused.
- **The standing caveat.** Meta status says it plainly: "v0 PROTOTYPE - ESTIMATED PHYSICS - not validated - paper model, nothing measured" (1460). A nominal sweep is an estimate, not a result about hardware.

## [MIDDLE] What to read first in the sweep output

1. **The drive block** (once it is actually packaged): `drive_W` = 1.0, `n_modes_driven` (expect ~129, matching `m_bond`), every `f_Hz` inside 1 Hz–50 MHz, `P_src_per_mode_W` ≈ 1/N. Confirms the split is the geometry's own mode list.
2. **`thermal.total_heat_W` and `heat_by_layer`.** Expect ≈ 3 W (1 thermal + 1 acoustic loss + 1 magnetic placeholder), *not* 4 W. This single number exposes the electric gap; if it ever reads 4 W before the channel is fixed, something double-counted.
3. **`acoustic.bonded.W_mJ` and per-mode `W_mJ` vs `P_n·Q_eff/2πf`, plus `loss_W`.** The identity should hold mode by mode (the test enforces it), and total bonded `loss_W` should equal 1.0 W — the acoustic channel's own energy-conservation check.
4. **`electric.march.E_max_V_m`.** Expect ~1e10 V/m. Reading this first tells you the electric channel is reporting a field beyond breakdown — the number to quote when deciding whether the electric stub is acceptable for this sweep.
5. **`flags`.** Watch for: BTO above Curie 393 K (piezo off), Gd-Dy above ~260 K (MCE knee missed), gas-centre approaching/in the HHO autoignition range 723–773 K, and the 3000 K solver cap. These mark where the 4 W operating point crosses the model's own validity lines. (My rough estimate: ~35 K/W stack resistance × 3 W puts the inner wall near 400 K and the gas centre near 770 K — so several of these flags likely fire; treat as an estimate, not a prediction.)
6. **`gas`: `T_gas_K`, `T_centre_K`, `p_hot_Pa`, `gas_modes_hot` vs the cold `drive.f_Hz`.** The gap between the hot mode list and the driven list is the unmodelled detune, made visible.
7. **`thermal.T_quartz_in`, `dT_wall`, and the quartz stress flag** (thermal + summed acoustic + fill stress vs 48 MPa) — the mechanical safety line for the core.
8. **The labels: `state.source` and meta scenario.** If they still say "no source / nothing is injected", the file is mislabelled regardless of its numbers (fix #2 above).

Note: I did not need the information switch or external lookups this round; all findings are from the code folder as it stands.
