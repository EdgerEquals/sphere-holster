I reached the repo. I read the root page and README, `DESIGN_STATE.md`, `AGENTS.md`, `drive_model_output.txt` and the issues list. I did not open the solver and shoot scripts, `model_data_v0.json`, the viewer, `reviews/` or `ledger/`, so anything below about code is inference from outputs and docs. The one numeric inconsistency I found (item 1) is easy to check against the code.

## What I'd fix

**1. A factor-of-2 mismatch inside `drive_model_output.txt`.**
- The 22 Torr, 600 V case appears twice, once as example runs and once as the frequency sweep.
- The sweep's ring-gas and shell amplitudes are exactly half the example values at matching frequencies. At 20 Hz, gas is 4.047e-3 Pa in the sweep and 8.093e-3 Pa in the example. At 20 kHz it is 4.030 Pa in the sweep and 8.060 Pa in the example. Shell shows the same split (1.108e-4 vs 2.215e-4 at 20 Hz).
- The sweep's 2 kHz value equals the example's 1 kHz value.
- That looks like an f versus 2f, half-cycle versus full-cycle, or peak versus RMS slip. `dT_gas` agrees to within a fraction of a percent, so the two paths disagree only on the acoustic terms.
- Best approach: write a regression test that runs both code paths at one operating point and asserts they agree. Then fix whichever is wrong.

**2. The power scales don't connect.**
- The drive model runs at about 1.3e-7 J per cycle, which is roughly 0.1 mW at 1 kHz.
- The design text talks about about 1 W heat-path problems, about 10 W for the BTO Curie point, 8–16 W for KSF saturation, and a 7.5 kW quartz cap.
- The weakest layer sets the real limit, which is about 10 W, so the 7.5 kW figure doesn't constrain anything. The model's electrical energy sits about five orders below that.
- The drive model also runs at 20 Hz to 20 kHz. The shell modes are at 1.87 MHz and 3.236 MHz, and the gas l=0 mode is at 762 kHz. Nothing yet connects the electrical drive to the shell.
- Best approach: pick one operating point and carry power and frequency through every layer in one chain. Put it in a single table of the power at which each layer fails.

**3. Numerical noise is reported as physics.**
- Non-ionising cases print `dT_gas` of 3e-11 to 8e-10 K, which varies non-monotonically. They should be exactly 0 or clamped to a stated floor.
- The fill sweep is a coarse log grid. It has only 3 points inside the 10–180 Torr window where ionisation actually happens at 600 V.
- Best approach: replace the 1D sweeps with a 2D map of fill against voltage on a fine grid, with the knee drawn on it.

**4. Single-cycle is ambiguous.**
- It isn't clear whether `dT_gas` is a peak, a cycle average or a steady state. A rough estimate from 3.8e14 molecules gives about 10 K if all 1.3e-7 J heats the gas at once, against the reported 0.24 K.
- There is no accumulation over many cycles. The open question about the test shell passing HHO autoignition at 1 W is exactly a steady-state question.
- Best approach: add a lumped multi-cycle thermal network (gas → wall → layers → ambient) and label what each temperature means.

**5. Material identity: crystal or fused quartz?**
- The output says "bare crystal quartz", but the shell-mode numbers look like fused-silica properties. My rough check of the 1.87 MHz breathing mode used about 72 GPa and 2200 kg/m³.
- Fused silica isn't piezoelectric. Crystal quartz is anisotropic, so a sphere has orientation-dependent coupling.
- Best approach: decide which one it is, then tag the elastic and piezo constants accordingly.

**6. Repo hygiene.**
- The README is stale. It lists only the solver and the viewer, and says `index.html` is to follow.
- Versions live in filenames (`shoot`, `shoot_v03`, `v04`, `v041`, `shoot_drive`). Generated outputs and PNGs sit in the root.
- "Locked" and "Open" overlap. For example, the lock shell is Locked while "which quartz shell" is Open item 1.
- Best approach: use one source file per model with git tags for versions, move generated files to `outputs/`, and rewrite the README.

## What I checked and found sound
- The HHO sound speed uses a mean molar mass of 12.011 g/mol, which is right for 2:1 H₂:O₂. It gives 532.9 m/s at 293 K.
- The 762 kHz gas mode matches a rigid-wall radial mode for a 0.5 mm radius.
- The 1.87 MHz shell breathing mode matches my rough fused-silica estimate.
- The chemistry heat is consistent with the stated 8.7e-3 % H₂ conversion.

## What's missing
- **Validation against external data.** Paschen curves for H₂/O₂, the DBD energy per cycle (Manley), and shell resonances all need benchmarks. The reviewers' PASS verdicts are not a substitute.
- **Uncertainty and sensitivity analysis.** Everything is an `[est]` point value. A tornado chart would show which three parameters drive the answer.
- **The drive-to-shell electromechanical link.** The piezo coupling and the acoustic matching between gas, quartz and BTO are absent. The BTO, tourmaline, phosphor and layer-5 sections are mostly text, with no coupled numbers.
- **A stated figure of merit.** The repo never says what output you are optimising or what "gain" means, only that layer 5's nonlinear option needs a coherent megawatt-level pump.
- **A physical basis for the golden-ratio choices.** Currently the φ-sized shell and the φ boundary shift read as numerology. They need a mechanism or should be treated as a free parameter.
- **A hazard analysis.** A sealed H₂/O₂ fill with a discharge and autoignition margins needs one before any build.
- **Evidence the review loop catches errors.** Issues #3, #4 and #6 are all PASS. The planted-mistake scoring has had no paid run, and spec reviews, which cover most of the physics claims, are never scored. The reviewers are all LLMs, so their errors may be correlated. Run the planted-error test before trusting PASS.
- **Balance of effort.** There are 18 harnesses, a ledger, cost rollups and a receipt gate, against one 0-D gas model. I'd build one end-to-end vertical slice (drive → gas → shell → heat) before more infrastructure.

## What I think you're trying to do
You're building a multi-physics design model for a millimetre-scale layered sphere. Its core is an HHO gas bubble, driven by a dielectric-barrier discharge and a piezo quartz shell. It is surrounded by BTO, tourmaline, a downshifting phosphor and an outer nonlinear or magnetocaloric layer. The aim seems to be tracing how energy moves between the optical, acoustic, electric, thermal, magnetic and chemical domains, and finding operating points that are feasible and safe. The 434 nm mention suggests the plasma's visible emission is downshifted by the phosphor. The viewer is meant to make this explorable.

You are also building a way to do this reliably with several AI models. Cursor is the coordinator, Claude and Grok audit, and Kimi and DeepSeek do cheap checks. Everything is gated by receipts, a ledger and a retired-items list so that nothing is called "locked" without evidence. My guess is that the second goal is currently ahead of the first.

I'm inferring all of this, because the repo never states the end goal. If I've misread it, tell me and I'll redo the priorities.
