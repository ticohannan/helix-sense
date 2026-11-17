# Changelog

All notable changes to the stretch-coil displacement sensor project.

Format follows [Keep a Changelog](https://keepachangelog.com/). Versions cover the
project as a whole — schematic, specification, handoff, and the modelling notebook
move together, because the notebook's defaults and the spec's BOM both encode the same
design decisions. A change to one usually requires a matching change to the others.

## Artifacts under version control

| File | Purpose |
|---|---|
| `tools/coil_stretch_inductance_tool.py` | Jupyter modelling cell |
| `tools/helix_core.py`, `tools/nonuniform_stretch.py` | Importable physics core and analysis scripts |
| `docs/*.md` | Findings, literature review, field-deployment notes |
| `designs/<name>/coil-sensor-schematic-v<version>.svg` | Circuit schematic |
| `designs/<name>/coil-sensor-circuit-spec-v<version>.md` | Design constraints, BOM, rationale |
| `designs/<name>/coil-sensor-handoff-v<version>.md` | Mechanical interface handoff |

---

## [0.2.0] — 2026-11-16

Repository created as `helix-sense` and widened from one sensor design to a general
toolkit. Non-uniform stretch analysed, literature reviewed, field conditions assessed.

### Added

- Repository layout: `tools/`, `docs/`, `designs/soft-robotics/`; README; BSD-3-Clause
  license.
- `tools/helix_core.py`: the notebook's physics as an importable module, with per-turn
  diameters so series sections of different diameter can be modelled.
- `tools/nonuniform_stretch.py` and `docs/nonuniform-stretch.md`: gap influence
  function, same-length redistribution errors, Coulomb-friction hysteresis cycle,
  bonded-turn / two-diameter / pre-opened-pitch designs.
- `tools/check_consistency.py`: asserts the notebook cell and `helix_core` agree.
- `docs/literature-review.md`: published spring and coil sensors, readout methods
  compared by cost, gaps in the literature.
- `docs/field-deployment.md`: temperature, humidity, condensation, interference,
  cabling and mechanical exposure, sized for the reference design.
- Handoff §5.6: requirement that the coil stretch evenly or at least repeatably.
- Spec open items: baseline against an LDC1612 module; coil internal resonance.

### Fixed

- **Turn geometry in the notebook tool (now v5).** Turn centres now span the coil
  length minus one wire diameter. Previously the bonded-turn model placed the last turn
  a full wire diameter too far out, so a "compressed" coil was already slightly open
  and read 2.6 % low in inductance, while the unbonded model moved the end turn by
  only (N−1)/N of the commanded displacement.
- **Spring force and stress.** 3 mm of stretch takes about 19 mN and puts the wire at
  about 16 MPa (40 % of yield), not 17 mN and 13 MPa (33 %). The earlier figures
  counted bonded turns as active.

### Changed

- **Design-point numbers recomputed with the filament model.** Inductance at +3 mm is
  1.60 µH (was quoted 1.65). Frequency sensitivity is 43,000 ppm/mm compressed,
  37,000 at mid-range and 33,000 at 3 mm (was quoted as a flat 32,000). One micron is
  about 37 ppm of frequency. The earlier figures came from the Wheeler approximation.
- **Error budget.** Added thermal growth of the copper coil itself (+32 ppm/°C in L,
  about 0.4 µm/°C), which is as large as the C0G capacitor term. Added non-uniform
  stretch and stray-capacitance terms.
- Spec and handoff reissued as v0.2.0. Schematic unchanged at v0.1.0.
- Changelog table of artifacts updated for the new layout.

### Notes recorded for future reference

- Gaps at the centre of the coil carry about twice the signal of the first free gaps.
- Uniform friction nearly cancels over an extend/retract cycle because the two tension
  gradients are mirror images and the coil is symmetric. A snag off-centre does not
  cancel: about 20 µm of hysteresis in the model.
- Per-turn spring stiffness does not depend on pitch, so pre-opened sections stretch
  by the same amount as close-wound ones and only reduce sensitivity.
- f(x) departs from a straight line by 1.3 % of full scale. Calibrate with a polynomial.
- The free turns have an axial resonance near 90 Hz.
- A continuous LC oscillator needs only a counter, not a fast timer, so a classic
  16 MHz Arduino can read one even though it cannot time a ring-down.
- The MSP430 Scan Interface uses the same pulse-then-ring-about-mid-supply scheme for
  LC sensors in utility meters.

### Open at this version

Everything open at 0.1.0, plus: no hardware measurement of any model result; ring-down
against LDC1612 against free-running oscillator not yet compared; condensation and
long-term creep untested; schematic file not yet committed.

## [0.1.0] — 2026-09-09

First captured design. Ring-down LC measurement of an air-core coil stretched over a
1–3 mm range, targeting sub-micron resolution.

### Added

- Coil design point: 32 turns of 30 AWG heavy-build enamel on 5 mm mean diameter,
  10 mm compressed, ≈ 2 µH, ≈ 32,000 ppm/mm frequency sensitivity.
- Mid-rail-referenced tank topology with 2N7000 current injector and LT1016 comparator.
- Circuit specification with BOM, error budget, and verification plan.
- Modelling notebook: exact coaxial-filament inductance summation, ring-down solver,
  comparator and timing model, temperature error budget, helical spring stress check.
- Mechanical handoff document.

### Changed from the reference designs

Starting points were the CircuitDigest LM741 and Electronoobs LM339 Arduino LC meters.

- **Tank reference moved from ground to a 2.5 V mid-rail.** Removes negative swings and
  every associated clamping path. This is the change that makes the rest work.
- **Comparator LM741/LM339 → LT1016CN8.** LM741 slews at 0.5 V/µs; LM339 propagation
  delay is ~1300 ns, longer than two periods at the operating frequency.
- **Excitation GPIO + resistor → 2N7000 + 68 Ω.** A driven-low GPIO is an AC ground, so
  the "series" resistor acts as parallel damping across the tank. A MOSFET opens cleanly.
- **Microcontroller ATmega328 → RP2040 class.** 62.5 ns LSB gives ~5 counts per half
  period; `pulseIn()` at ~1 µs granularity cannot resolve the ring at all.
- **Tank capacitor 0.1 µF → 4700 pF C0G.** Places the ring near 1.6 MHz for a ~2 µH coil.
- **Inductance model Wheeler/Nagaoka → exact filament summation.** Current-sheet formulas
  degrade once turn gaps approach the wire diameter, which is the whole operating regime
  of a stretched coil. Wheeler retained as a cross-check only.

### Removed

- **1N4007 isolation diode, deleted entirely.** Its ~2 µs reverse recovery would conduct
  backwards through much of every cycle at 1.6 MHz. Mid-rail referencing removes the need
  for any diode rather than replacing it with a faster one.

### Notes recorded for future reference

- A resistor in series with an excitation pin becomes *parallel* damping during ring-down,
  because the driven-low pin is an AC ground. Inverts intuition; easy to rediscover
  painfully.
- Since f ∝ (LC)^(−½), df/f = −½ dL/L regardless of C — capacitance costs no fractional
  sensitivity, so choose it to place the frequency where it can be counted. But lowering
  frequency to suit a slow MCU fails, because raising C also lowers Z₀ = √(L/C) and
  therefore both amplitude and Q.
- Shorter coils are more sensitive per millimetre, since fractional sensitivity scales as
  1/(ℓ + 0.9r).
- Timing improvement stops at roughly 8 ns LSB, where comparator delay dispersion becomes
  comparable to timer quantisation. Average more bursts instead of buying clock speed.
- Ring-down yields f_d = f₀√(1 − 1/4Q²). Using the undamped formula introduces a bias
  that varies with Q, and Q varies with stretch — a stretch-dependent systematic, not a
  calibratable offset.

### Open at this version

Member material and CTE; eddy-current coupling to nearby metal; friction hysteresis in
the guide tube; proximity-effect factor (currently a guess of 2.0); LT1016 common-mode
window on a single 5 V supply; enamel abrasion over cycles; whether coil diameter stays
constant under extension.

[0.2.0]: #020--2026-11-16
[0.1.0]: #010--2026-09-09
