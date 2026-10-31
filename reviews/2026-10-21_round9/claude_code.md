<!-- landed: reviewer=claude_code · model=claude-opus-5-5 · channel=scripts/review_claude_code.py --ping · generated_utc=2026-10-21T05:04:39Z · source=/workspace/ensemble-round8/Current/round9/run_2026-10-21_primary/claude_code/ping.json · run_id=primary-20261021T050438Z-7c9a22 · landed_utc=2026-10-21T05:06:42Z · finish=success -->

# Claude Code

## 1. Verdict

**Not ready.** I found four problems in the code as it stands. Nothing can run the case or write `drive_4W_*.json`. The electric watt never reaches the heat balance. The electric field it creates is physically impossible. And the 1 Hz thermal envelope is never applied.

## 2. What's missing

**Blockers**

1. **No runner and no output.** Nothing in the code folder writes `drive_4W_*.json`. The command line has no option for `drive_W` (`solver_v0.py:1421-1428`). `main` calls `run_case(pre, ref)` with the default `drive_W=0` (`solver_v0.py:1412`, `:1452`). So the "4 W sweep" can't be run without new code. The output also has no defined format, and the raw `run_case` result holds a `Thermal` object and numpy arrays (`:1090`), so it can't be written to JSON as is.
2. **The sweep has no defined axis.** §2 of the brief fixes everything: `drive_W=1`, preset `base5`, one pressure, one gas. As set up, this is one run, not a sweep. Someone has to say what is being varied, if anything.
3. **The electric watt is never turned into heat.** `J_drive` is passed to `el.step` (`:1061`, `:1073`). But the heat sent to the thermal solver is only `qo + q_ac + q_mag + P_gas + ec_heat` (`:1055-1062`, `:1071-1074`). There is no ohmic term (J·E). So the thermal solver sees about 3 W from the drive, not 4 W.
4. **The electric field is impossible.** `drive_J_src_for_power` (`:836`) sizes J so that J²/σ·V = 1 W. The BTO conductivity is σ = 1e-10 S/m (`:252`). For `base5` the BTO film volume is about 1.0e-10 m³ (inner radius about 2.017 mm, 2 µm thick). The steady field is then E = √(P/σV) ≈ **1e10 V/m**. That is about 240 times the code's own `E_WORK = 42e6` (`:224`) and far above any breakdown field. The electrocaloric heat (`ec_heat`) at that field also feeds into the temperature result. *(This number is my hand calculation, not solver output.)*
5. **The 1 Hz thermal envelope is not implemented.** `DRIVE_THERMAL_ENVELOPE_Hz` (`:809`) appears only as a constant and in a test (`test_drive_1W.py:39`). It never touches the drives, which are steady (DC) throughout. Either implement it, or the run has to be described as a steady drive.
6. **"Heat into the gas core" actually goes into the quartz wall.** `make_grid` (`:434-442`) has no gas cells, so `q[0] += P_gas` (`:1056`) heats the innermost quartz cell. The gas temperature is worked out afterwards by `gas_T_profile` (`:1082`), and nothing feeds it back into the thermal solve. The inline comment at `:1019` already says "inner wall", so the labels disagree with each other.
7. **`DESIGN_STATE.md` is not in the code folder.** I could not check the "Opt-in 1 W domain drive plumbing" or "Core geometry replaced…" sections the brief cites.

**Nice-to-have**

8. **No test checks the totals.** Nothing checks that the heat sums to 4 W, that the electric watt is actually delivered (σE²V = 1 W), or that E stays below a breakdown limit. `test_drive_1W.py:56` can never fail: its `or … == 1.0` repeats line 55.
9. **The mode searches use different grids.** `vac_modes` uses 4 000 points (`:968`, df ≈ 12.5 kHz). `l0_modes` uses 20 000 (`:609`, df = 2.5 kHz). The 1 % shell/gas split (`:978`) can then drop or misfile modes. Roots that sit close together can be missed between sign checks. No grid-convergence check exists.
10. **Gas Q plays no part in this run.** `gas_Q`, `gas_Q_terms` and `gas_linewidth` are never called in `run_case`. Gas-cavity modes are not driven, and the gas modes from the bonded stack are thrown away (`m_bond, _`, `:982`). Gas Q is correct at its source, but the 4 W result says nothing about it.
11. **The fill pressure doesn't quite match its label.** 0.1044 × 101 325 = 10 578.3 Pa, but the code uses 10 577.3 Pa, which is a factor of 0.104390 (`:65-67`). The solver also fixes ambient at 101 325 Pa. Only `geometry_fill_sweep_v0.py` takes a local ambient (`--p-ambient`).
12. **Shared global state.** The global `GAS` dict is changed inside `run_case` (`:956`, `:1084`, `:1088`). Running several cases in parallel in one process is not safe.

## 3. What would make a sweep result invalid

- **Energy accounting.** As above, about 3 W reaches the thermal solver, not 4 W, so any "4 W" temperature is mislabelled. On top of that, electrocaloric heat at about 1e10 V/m could add a large or garbage term.
- **The electric channel has no physical meaning.** A field about 100 times past breakdown means the BTO would fail, and the piezo, pyro and electrocaloric outputs are not physical. The design has no electrodes, so the source current has nothing physical behind it (it's a stub marked [est]).
- **The magnetic channel is just heat.** B = 0 by symmetry, so "magnetic 1 W" is ferrite heating. The run is really heat sources at three radii plus acoustic mode energies. It is not a coupled four-channel result.
- **Acoustic power depends on the window.** P_src,n = 1 W/N, and N is set by the arbitrary 1 Hz–50 MHz window and grid. Changing the window changes every mode's energy. The total acoustic loss does come to 1 W, because Σ share/Q = 1/Q_eff. Per-mode energy W_n assumes the drive sits exactly on each mode.
- **No detune after heating.** The drive frequencies are the cold (293 K) bonded modes. Hot modes are recomputed only for the isolated stack (`:1085`), and only for the record. Nothing retunes the drive or reduces W for detune.
- **The outer boundary sets the temperature.** The full stack holds the ferrite outer surface at 293 K (`:29`, `:940`), which is a perfect heat sink. Absolute temperatures are set by that boundary choice. The 3000 K clamp (`:943`, `:498`) can hide a runaway.
- **Gas chemistry is off.** `chem_state(..., 0.0)` (`:1022`) gives no dissociation and no heat release. My rough estimate for 1 W in this core is a gas centre near 700 K, plus the wall's own rise. At about 10 kPa that may be near the H₂/O₂ explosion limits. The model would not show an ignition. *(The 700 K figure is my hand calculation, not solver output.)*
- **Settings can be overridden silently.** `pre.get("drive_W", drive_W)` (`:953`) lets a preset dict override the argument. A custom preset falls back to `--p-atm` default 1.0 (`:1424`), which breaks the rarefied-only rule.
- **The numbers rest on estimates.** Material values tagged [est], such as BTO σ, ferrite σ, layer-two Q and CALORIVAC properties, drive the outputs directly. The result is an estimate from a paper model, not a prediction.
- **Spurious or missing modes** from the grid mismatch (item 9) would change N, and so every per-mode number.

## 4. What to read first in the sweep output

1. **`drive.drive_W`, `n_modes_driven`, `f_Hz`, `P_src_per_mode_W`.** Confirms the drive is on, shows the mode count N, and shows that the frequencies are computed and inside the window.
2. **Heat balance: `heat_by_layer` total vs. 4 W.** Today I expect about 3 W plus the electrocaloric term. A gap shows the missing ohmic heat. A large excess shows electrocaloric garbage.
3. **`E_ss` maximum in the BTO film, and σE²V there.** Compare E with `E_WORK` (42 MV/m) and check whether the delivered power is 1 W. Anything near 1e10 V/m means the electric result is invalid.
4. **`Tss`, especially `Tss[0]` and the BTO temperature vs. `T_CURIE` (393 K), plus `gas_hot.T_gas` and `T_centre`.** These show whether temperature-dependent switches flipped (piezo on/off, Curie point, quartz k(T)). Also check for the 3000 K clamp.
5. **`W_ac`, and per-mode `W`, `Q_eff`, `tau_ac` in `ac_bond.modes`.** Check that W_n = P_n·Q/ω, and look for any single mode that dominates.
6. **`gas_hot.shell` vs. the cold `m_iso`.** Shows how far the modes shift when hot, which is the detune the drive ignores.
7. **The zero run (`drive_W=0`) next to it.** Every field should be exactly zero at 293 K. Any difference in the driven run that also shows up in the zero run is an artefact.

**Ethics note:** this is a paper model of an explosive gas mix with no chemistry switched on. A 4 W result must not be read as showing that a hardware fill is safe.

I'm not asking for more lookups. The blockers are clear from the code, and more reading wouldn't change the verdict.
