# helix-sense

Tools and notes for building cheap displacement sensors from a stretched coil of wire.

A helical coil's inductance falls as its turns are pulled apart. Put the coil in
parallel with a capacitor, measure the resonant frequency, and you have a displacement
sensor with no core, no wiper and no optics: a few cents of magnet wire and a
microcontroller. The aim is to make such sensors quick to design and deploy where an
LVDT or a precision potentiometer would cost too much or wear out.

**Status:** modelling and design only. Nothing here has been validated on hardware yet.

## What is here

| Path | What it is |
|---|---|
| `tools/coil_stretch_inductance_tool.py` | Interactive design explorer. Paste into one Jupyter cell. Wire gauge, turns, diameter, stretch, tank capacitor, readout timing, temperature budget, spring stress. |
| `tools/helix_core.py` | The same physics as an importable module, for scripts. |
| `tools/nonuniform_stretch.py` | What happens when the coil does not stretch evenly: gap influence, friction hysteresis, series-segment designs. |
| `tools/check_consistency.py` | Confirms the notebook cell and `helix_core` agree. |
| `docs/nonuniform-stretch.md` | Findings from the uneven-stretch analysis. |
| `docs/literature-review.md` | Published coil and spring sensors, readout methods compared by cost, and what nobody has measured yet. |
| `docs/field-deployment.md` | Temperature, humidity, condensation, interference and cabling, sized for the reference design. |
| `designs/soft-robotics/` | First worked design: 1 to 3 mm of travel on a 10 mm coil, ring-down readout. Specification and mechanical handoff. |
| `CHANGELOG.md` | Version history for the whole repository. |

## Quick start

```
pip install numpy scipy matplotlib pandas ipywidgets
python tools/check_consistency.py
python tools/nonuniform_stretch.py
```

For the interactive explorer, open Jupyter and paste the contents of
`tools/coil_stretch_inductance_tool.py` into a single cell.

## The reference coil in numbers

32 turns of 30 AWG enamelled copper, 5 mm diameter, 10 mm long, 4700 pF across it.

- 2.0 µH compressed, 1.6 µH at 3 mm of stretch
- rings at 1.63 to 1.83 MHz
- about 37,000 ppm of frequency per millimetre, so 1 µm is 37 ppm
- 19 mN to stretch 3 mm; wire at about 40 % of yield

## Things the model has taught so far

- Shorter coils are more sensitive per millimetre. Wind close; pre-opened turns lose
  sensitivity.
- Gaps near the centre of the coil carry twice the signal of gaps near the ends, so a
  snagged turn or a side load shows up as about 20 µm of hysteresis. A coil that slides
  freely stays under a micron.
- The tank capacitor costs no sensitivity, so use a large one. It also makes the sensor
  nearly indifferent to humidity.
- Over temperature, the capacitor and the copper coil each drift about 0.4 µm/°C. A
  second, fixed coil measured as a ratio cancels both.
- An off-the-shelf inductance-to-digital converter has already been shown reading a
  spring. Buy one as a baseline.

## Roadmap

- Bench data: inductance against length on a wound coil, ring capture, hysteresis sweep.
- Firmware for ring-down timing on an RP2040.
- A continuous-oscillator-and-counter variant that runs on a classic Arduino.
- Side-by-side comparison with an LDC1612 module.
- Reference-channel ratio and polynomial calibration tool.
- Oven and humidity tests.

## License

BSD 3-Clause. See `LICENSE`.
