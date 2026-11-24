# Stretch-Coil Displacement Sensor — Circuit Specification

**Version:** 0.3.0
**Date:** 2026-11-23
**Status:** Draft for review — not yet built or measured
**Related files:** `coil-sensor-schematic-v0.1.0.svg` (unchanged at this version), `tools/coil_stretch_inductance_tool.py`, `docs/nonuniform-stretch.md`, `docs/field-deployment.md`, `docs/tolerance-and-calibration.md`, `docs/nearby-metal.md`

At this version: calibration (§8.1) and nearby-metal and unit-to-unit terms (§9) added;
open item 2 replaced by modelled keep-out distances. Circuit and bill of materials unchanged.

---

## 1. Purpose

Measure small displacements by stretching an air-core helical coil and tracking the
resulting change in inductance. Inductance is read out as the ring frequency of an
LC tank excited by a step and allowed to decay.

## 2. Requirements

| # | Requirement | Value | Source |
|---|---|---|---|
| R1 | Displacement range | 1–3 mm | Stated |
| R2 | Coil compressed length | 10 mm nominal, 20 mm max | Stated |
| R3 | Component packaging | Through-hole only | Stated |
| R4 | Ring frequency ceiling | < 10 MHz | Stated |
| R5 | Core | Air; non-magnetic filler permitted | Stated |
| R6 | Measurement method | Step excitation, ring-down frequency | Stated |
| R7 | Target resolution | Sub-micron desirable | Derived from R1 |

## 3. Coil design point

| Parameter | Value | Note |
|---|---|---|
| Wire | 30 AWG (0.255 mm bare), heavy build enamel | 0.310 mm OD |
| Mean coil diameter | 5.0 mm | Spring index D/d ≈ 20 |
| Turns | 32 | From 10 mm / 0.310 mm |
| Compressed length | 10.0 mm | Turns touching |
| Bonded turns | ~2 each end | Held by adhesive, do not spread |
| Inductance, compressed | 2.01 µH | Filament model |
| Inductance, +3 mm | 1.60 µH | −20 % |
| Ring frequency | 1.63 MHz compressed, 1.83 MHz at +3 mm | With 4700 pF + 15 pF stray |
| Frequency sensitivity | 43,000 ppm/mm compressed, 37,000 at 1.5 mm, 33,000 at 3 mm | df/f = −½ dL/L |
| Linearity of f(x) | 1.3 % of full scale (38 µm) from a straight line | Calibrate with a polynomial |

**Shorter is better.** Fractional sensitivity scales roughly as 1/(ℓ + 0.9r), so the
10 mm coil gives ~7.5 %/mm in L at mid-range where a 20 mm coil gives ~4.3 %/mm. Lengthen only if
ring amplitude proves insufficient.

**Mechanical check.** At 3 mm extension the coil needs ≈ 19 mN and the wire sees
≈ 16 MPa shear against ≈ 40 MPa shear yield for annealed copper — about 40 % of yield,
so no permanent set is expected, with less margin than v0.1.0 stated (it counted the
bonded turns as active). The high spring index is what saves this: the wire works in
torsion, not tension. Residual risk is room-temperature creep under sustained load.

**Mounting.** Coil floats inside a guide tube (PTFE preferred over PP for lower
friction), bonded to the moving member at both ends only. The coil supplies
negligible restoring force, so the member must drive both directions.

## 4. Circuit topology

Three blocks: a mid-rail generator, a current injector plus tank, and a comparator.

**Mid-rail generator.** R1/R2 divide 5 V to 2.5 V; C1 and C2 make that node a stiff
AC ground. The whole tank floats on this node.

**Injector and tank.** Q1 pulls the tank node B to ground through R5 for ~300 ns.
Current builds in L1 to V_MID/(R5 + Rds_on + R_coil) ≈ 34 mA; the L/R time constant is
~30 ns so this settles well within the pulse. When Q1 opens it goes genuinely
high-impedance and R5 disconnects, leaving the tank to ring undamped by the drive.

**Comparator.** U1 compares B against MID. R6/R7 set ~10 mV of hysteresis. R8/R9
divide the 5 V output for a 3.3 V MCU.

### 4.1 Why the tank floats on a mid-rail

This is the central design decision and it removes a part rather than adding one.

With a ground-referenced tank, the ring swings negative every other half cycle.
Something always conducts on those swings — the drive diode, the MCU's protection
diode, or the MOSFET body diode — clamping and damping one polarity only. That
asymmetry is why the published Arduino LC-meter circuits are so temperamental.

Referenced to 2.5 V, the ring stays between roughly 1.8 V and 3.2 V. No node
approaches either rail, nothing conducts, and the decay is clean and symmetric for its
full length. **The isolating diode is deleted entirely.**

The circulating ring current flows in the closed L1–C5 loop and never returns through
the mid-rail node, so the low impedance of C1/C2 does not damp the tank. It only has
to hold the comparator reference steady.

### 4.2 Why R5 is 68 Ω

R5 sets injected current and therefore ring amplitude, Vpk = I₀·√(L/C) ≈ 0.72 V.
Lowering it would give more amplitude and more usable cycles, but the swing must stay
inside U1's input common-mode range. **Amplitude is limited by the comparator, not by
the tank.** Confirm the LT1016 single-supply common-mode window against the datasheet
before changing R5.

## 5. Bill of materials

| Ref | Value | Package | Notes |
|---|---|---|---|
| L1 | ~2 µH, 32T 30 AWG on 5 mm | — | Sensor element |
| C5 | 4700 pF ±1 % | Radial | **C0G/NP0 mandatory** |
| C1 | 100 µF | Electrolytic | Mid-rail bulk |
| C2, C3 | 100 nF | Ceramic | Mid-rail and U1 bypass |
| R1, R2 | 1 kΩ 1 % | Axial | Metal film |
| R3 | 100 Ω | Axial | Gate series |
| R4 | 10 kΩ | Axial | Gate pulldown |
| R5 | 68 Ω 1 % | Axial | Injection current set |
| R6 | 470 kΩ | Axial | Hysteresis |
| R7 | 1 kΩ | Axial | Reference series |
| R8 | 1 kΩ | Axial | Level shift, omit if 5 V tolerant |
| R9 | 2 kΩ | Axial | Level shift, omit if 5 V tolerant |
| Q1 | 2N7000 | TO-92 | Low-side switch |
| U1 | LT1016CN8 | DIP-8 | 10 ns comparator |

C5 is the only component whose tolerance and tempco directly become measurement
error. X7R would drift by percent and is unusable here.

## 6. Changes from the reference designs

Both starting references (CircuitDigest LM741, Electronoobs LM339) were analysed. Four
parts changed and one was deleted.

| Item | Reference | This design | Reason |
|---|---|---|---|
| Comparator | LM741 / LM339 | LT1016CN8 | LM741 slews at 0.5 V/µs; LM339 has ~1300 ns propagation delay, longer than two full periods at 1.6 MHz. Neither can follow the ring. |
| Isolation diode | 1N4007 | **Deleted** | 1N4007 has ~2 µs reverse recovery — at 1.6 MHz it conducts backwards through much of every cycle. Mid-rail referencing removes the need for any diode. |
| Excitation | GPIO pin + 100 Ω + diode | 2N7000 + 68 Ω | A driven-low GPIO is an AC ground, so the "series" resistor becomes parallel damping across the tank. A MOSFET opens cleanly and disconnects R5. |
| Tank reference | Ground | 2.5 V mid-rail | Eliminates negative swings and all associated clamping. |
| MCU | ATmega328 @ 16 MHz | RP2040 / Teensy / Due class | 62.5 ns LSB gives ~5 counts per half period. `pulseIn()` at ~1 µs granularity is unusable. |
| Tank C | 0.1 µF (for 10 mH) | 4700 pF | Places f near 1.6 MHz for this ~2 µH coil. |

### 6.1 The GPIO-as-AC-ground insight

Worth recording because it inverts intuition. A resistor in series with the excitation
pin looks like series damping, but during ring-down that pin is held at 0 V by a
low-impedance driver. The resistor therefore runs from the tank node to AC ground —
electrically **parallel** damping. With a 150 Ω resistor across a tank of ~21 Ω
characteristic impedance, Q would collapse below 2 and the ring would die in a cycle or
two. The published circuits only work at all because their diode partially isolates the
path.

### 6.2 Frequency choice is nearly free

Because f ∝ (LC)^(−½), df/f = −½ dL/L regardless of C. Capacitance costs no fractional
sensitivity, so choose C to land the frequency where it can be counted. The limit going
the other way is that raising C lowers Z₀ = √(L/C), which reduces both ring amplitude
and Q together — so lowering the frequency to suit a slow MCU does not work.

## 7. Microcontroller selection

Requirement is a timer LSB well under the ~310 ns half period.

| Class | LSB | Verdict |
|---|---|---|
| AVR 16 MHz (Uno/Nano/Mega) | 62.5 ns | **Unusable** — ~5 counts per half period |
| SAMD21 48 MHz (Zero, Nano 33 IoT) | 20.8 ns | Marginal |
| ESP32 80 MHz capture | 12.5 ns | Workable; WiFi/RTOS jitter is a concern |
| Arduino Due (SAM3X 84 MHz) | 11.9 ns | Adequate, conventional Arduino |
| STM32F103 Blue Pill 72 MHz | 13.9 ns | Adequate; 5 V-tolerant inputs |
| **RP2040 (Pico, Nano RP2040)** | 8.0 ns | **Recommended** — PIO handles pulse and timestamps |
| Arduino Giga R1 (STM32H7) | 4.17 ns | Excellent, official Arduino |
| Teensy 4.x 600 MHz | 1.67 ns | Best timing, Arduino IDE via Teensyduino |

**Diminishing returns past ~8 ns.** Timing noise is √(2·LSB²/12 + 2·σ_pd²) across the
start and stop edges. At 8 ns LSB the LT1016's ~1.5 ns delay dispersion is already
comparable, so a faster MCU buys under 2×, not 5×. Beyond that point, average more
bursts rather than buying clock speed.

## 8. Measurement scheme

Excite, skip the first ~3 cycles, time a fixed window of ~32 cycles, repeat and average.

Skipping matters at both ends. Early cycles are distorted by Q1 turn-off and tank
settling. Late cycles are distorted because comparator propagation delay depends on
input slew rate, so as the ring decays the edges arrive progressively late. A fixed
window in the middle avoids both. Constant propagation delay cancels between two like
edges; only its dispersion contributes noise.

At 256 bursts the update rate is roughly 110 to 150 Hz, leaving room to trade speed for
resolution.

**Firmware caution.** Ring-down produces f_d = f₀·√(1 − 1/4Q²), not f₀. Computing L
from the undamped formula introduces a bias that changes with Q — and Q changes with
stretch, so it is a stretch-dependent systematic, not a constant offset that calibrates
away.

### 8.1 Calibration

Units are not interchangeable: on a shared curve they differ by 0.3 to 0.8 mm (*model*,
`docs/tolerance-and-calibration.md`). Each sensor is calibrated installed, with nearby
metal in place.

- Fit displacement as a polynomial in f/f₀ − 1 (f₀ = rest frequency), or in the
  sensor/reference ratio. Fitting in frequency needs one polynomial order less than
  fitting in inductance.
- Three known positions and a quadratic leave under 1 µm of fit error; four and a cubic
  leave none. The position reference then sets the accuracy: ±2 µm of stage error
  gives about ±5 µm.
- Field fallback: rest plus one gauge block at full scale with the modelled curve
  shape, good to about 7 µm.
- C5's value does not need to be tight, since a tare removes it. Its stability does.

## 9. Error budget

| Term | Magnitude | Comment |
|---|---|---|
| Timing noise | Sub-micron at 256 bursts | Set by LSB and comparator dispersion |
| C5 tempco (C0G) | ±30 ppm/°C → ±15 ppm/°C in f | ≈ 0.4 µm/°C |
| Coil diameter growth (copper, 17 ppm/°C) | +32 ppm/°C in L → −16 ppm/°C in f | ≈ 0.4 µm/°C; new at v0.2.0 |
| Non-uniform stretch | ~20 µm hysteresis if a turn snags off-centre or the coil is side-loaded; < 0.5 µm for a free coil in a smooth tube | `docs/nonuniform-stretch.md` |
| Stray capacitance | 0.35 pF of change reads as 1 µm | Fix the cable; see `docs/field-deployment.md` |
| Unit-to-unit spread | ±2.2 % in f, ±3.8 % in sensitivity | Removed by per-unit calibration (§8.1) |
| Calibration reference | ±2 µm stage → about ±5 µm | Sets the accuracy floor |
| Metal alongside, non-magnetic | 6.6 µm per 0.1 mm of coil side-play at 5 mm; 0.8 µm at 10 mm | Fixed offset calibrates out; drift negligible |
| Mild steel alongside | 0.11 µm/°C at 5 mm, 0.014 at 10 mm, plus stress dependence | `docs/nearby-metal.md`; estimate only |
| Member CTE (steel, 12 ppm/°C) | ≈ 0.12 µm/°C | On a 10 mm span |
| Member CTE (silicone, 250 ppm/°C) | ≈ 2.5 µm/°C | Avoid load-bearing elastomer |
| Copper tempco via Q | < 1 ppm/°C | Negligible |
| Q1 output capacitance | ~40 pF of 4700 pF | Voltage-dependent, <1 % |

The guide-tube arrangement helps here: the tube does not carry the length, the bonded
member does, so the member's CTE is what matters. A steel member drops mechanical drift
from ~2.5 µm/°C to ~0.12 µm/°C and moves the dominant terms back to the capacitor and
the coil's own expansion, which are similar in size and both cancel in a ratio against
a matched reference coil.

**Proposed for v0.2: a reference channel.** A second identical coil and capacitor,
mechanically fixed, measured as a frequency ratio. This cancels capacitor tempco,
comparator drift, and MCU clock error together. If the reference coil shares the former
and thermal environment, it cancels much of the mechanical term too. Far easier to
design in than to retrofit.

## 10. Open items

1. **Member material and CTE** — pending from the mechanical designer. Drives §9.
2. **Nearby metal** — now modelled. Keep 10 mm from the coil axis to metal alongside
   and 7.5 mm beyond the ends; no metal inside the coil or as a guide tube; avoid mild
   steel within 5 mm. The steel member chosen for low expansion is acceptable at that
   distance. Not yet measured, and steel's permeability under stress is unquantified.
3. **Friction hysteresis** — coil rubbing inside the guide tube will produce stick-slip
   in the L-vs-displacement curve. Needs measurement on a real assembly.
4. **Proximity-effect factor** — currently a guess of 2.0 in the model, and it changes
   as turns separate. Measure Q on a real coil and back it out.
5. **LT1016 common-mode window on a single 5 V supply** — verify before adjusting R5.
6. **Enamel abrasion** over many cycles against the tube wall.
7. Confirm whether coil diameter stays constant under extension in the final mounting.
8. **Baseline against an LDC1612 module.** TI demonstrated the same measurement on a
   spring with an off-the-shelf converter; one module is cheap enough to buy as a
   reference before committing to the discrete front end. See `docs/literature-review.md`.
9. **Coil internal resonance near 90 Hz** (axial surge mode of the free turns). Keep the
   measurement bandwidth below it or confirm the guide tube damps it.
10. **Benchmark against a Hall sensor and magnet** on the same stage. It is the cheap
    rival for 1 to 3 mm on a rigid mount (`docs/sensor-selection.md`).
11. **Capacitor tempco matching** between sensor and reference from one reel is assumed
    at 5 ppm/°C. One oven run would measure it.

## 11. Verification plan

1. Measure L on a wound coil at several fixed lengths with an LCR meter; compare to the
   filament model and fit the proximity factor.
2. Capture the ring on a scope; confirm amplitude, Q, cycle count, and symmetry.
3. Sweep displacement with a micrometer stage; extract the f(x) curve, fit it as in
   §8.1, and check for hysteresis on the return sweep.
4. Soak at two temperatures to separate mechanical from electrical drift.
5. Bring an aluminium plate and a steel plate up to the coil at fixed stretch and
   compare the shift with `docs/nearby-metal.md`.
6. Wind five coils and compare their curves with the spread in
   `docs/tolerance-and-calibration.md`.
