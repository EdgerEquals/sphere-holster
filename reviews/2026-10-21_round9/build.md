<!-- landed: reviewer=build · model=grok-build-0.1 · channel=scripts/review_build.py --ping · generated_utc=2026-10-21T05:11:58Z · source=/workspace/ensemble-round8/Current/round9/run_2026-10-21_build_rerun/build/ping.json · run_id=primary-20261021T050438Z-7c9a22 · landed_utc=2026-10-21T05:12:58Z · finish=completed -->

# Build

## 1. [HIGH CUE] Verdict
**not ready** to run the 4 W sweep. The solver supports `run_case(..., drive_W=1)` for base5 and the tests exercise it, but three core blockers (missing electric heat deposition, unimplemented 1 Hz envelope, no drive packaging or sweep runner) mean a result would not match the described set-up or be worth having.

## 2. [MIDDLE] What's missing
**blocker** (solver_v0.py:1055): electric drive power (from `drive_J_src_for_power` and `J_drive`) is sized for 1 W ohmic but never added to the thermal `q` array passed to `th.step`; only `qo + q_ac + q_mag + P_gas[0]` is used.  
**blocker** (solver_v0.py:809 and run_case ~1051): `DRIVE_THERMAL_ENVELOPE_Hz = 1.0` is defined and documented as a slow modulating envelope on the drives, but the time loop and `q` are constant with no 1 Hz variation applied.  
**blocker** (solver_v0.py:1452, 1314, package function ~1313): `main()` always calls `run_case(pre, ref)` (drive_W defaults to 0); `package` hard-codes `state["source"] = "none: no drive mechanism defined..."` and never copies `run["drive"]`, `J_drive`, `q_mag`, `P_gas` or `W_ac` into the JSON; no code exists to write `drive_4W_*.json`.  
**nice-to-have** (solver_v0.py:1419 main()): no `--drive-w` or equivalent argument to select drive_W=1 and emit a driven case.  
**nice-to-have** (solver_v0.py:1026 drive_info): the per-run dict is populated correctly when drive_W>0, but nothing downstream consumes it.

## 3. [WIDE BANDWIDTH] What would make a sweep result invalid
- Electric 1 W never appears as heat, so total deposited power is ~3 W instead of 4 W and temperature rise is under-stated.  
- No 1 Hz envelope exists, so the "slow envelope modulating the drives" described in DESIGN_STATE.md and the brief never occurs; all drives are steady DC.  
- Acoustic drive frequencies, `P_src_list`, `W_n` and `Q_eff` are computed once on the cold (293 K) `m_bond` / `m_iso` list before any heating; later `gas_hot` recomputes modes at the new T but the driven energies stay fixed from the cold calculation, creating inconsistency once Tss rises.  
- Packaged JSON (if used for the sweep) would report `source="none"` and omit all drive fields, making the output meaningless for a 4 W case.  
- `drive_heat_on_material` for magnetic and `q_ac` for acoustic assume uniform distribution over the target material volume; any mismatch between `th.V` cells and actual loss locations would mis-localise the 1 W.  
- `l0_modes` uses a 20 000-point linear grid to find roots; if the rarefied base5 geometry produces very few (or zero) bonded l=0 modes in 1 Hz–50 MHz, `n_modes_driven=0` and acoustic drive collapses to zero even with drive_W=1.  
- Gas state after drive uses `p = p_seal * Tg / T_REF` (rarefied factor preserved) and solver `gas_Q`, but the initial mode search and drive split use the seal state; any sweep that mixes cold-driven W with hot gas_Q would be internally inconsistent.  
- No power-balance check (input 4 W vs sum of all q terms + ohmic) exists in run_case or tests, so silent loss of the electric watt would go undetected.

## 4. [MIDDLE] What to read first in the sweep output
If a future `drive_4W_*.json` or direct `run_case` return is produced, inspect these first (in this order):  
- `drive` dict (or equivalent): `drive_W`, `n_modes_driven`, `f_Hz`, `P_src_per_mode_W`, `W_ac_sum_J` — confirms acoustic split uses only computed bonded modes from the window and that total acoustic energy is non-zero.  
- `P_gas` — must equal 1.0 (thermal channel).  
- `q_mag` sum and `heat_by_layer["ferrite"]` (or quartz for bare) — must equal 1.0 (magnetic placeholder).  
- `J_drive` max abs and `E_ss` max abs — confirms electric J_src is non-zero and field is marched.  
- `Tss` profile and `gas_hot` (T_gas, p_hot, c_hot) — shows whether any heating occurred and whether rarefied pressure factor is preserved.  
- `q` sum and `heat_by_layer` totals — first check that total heat is close to 4 W (will currently be short the electric watt).  
- `ac_bond["modes"]` list and `W_ac` — verify per-mode `W = P_src * Q_eff / (2*pi*f)` holds.  
- `m_bond` vs `gas_hot["shell"]` — confirm cold-driven frequencies vs hot recomputed modes.  
These fields tell us immediately whether each of the four 1 W channels was applied, whether frequencies came from the geometry's own mode list, and whether the result is still rarefied as required.
