# Taking a stretch-coil sensor out of the lab

**Project version:** 0.2.0

What temperature, moisture, interference and handling do to the reading, sized for the
reference design (32 turns of 30 AWG on 5 mm, 10 mm long, 4700 pF tank, 1.6 to 1.8 MHz,
about 37 ppm of frequency per micron). Figures marked *model* come from the tools in this
repository; figures marked *source* come from the references in `literature-review.md`.
None has been measured on this hardware.

A handy conversion for this design: **1 µm = 37 ppm of frequency = 75 ppm of L or C =
0.35 pF of tank capacitance.**

## 1. Error budget in field conditions

| Effect | Size | Equivalent displacement | Cancels with a reference coil? |
|---|---|---|---|
| Anchored member expands (steel, 10 mm span) | 12 ppm/°C | 0.12 µm/°C | Only if the reference sits on the same material |
| Anchored member expands (polymer, 100 to 250 ppm/°C) | | 1 to 2.5 µm/°C | Same |
| Tank capacitor, C0G | ±30 ppm/°C (*source*) | ±0.4 µm/°C | Yes, if the two capacitors match and share temperature |
| Coil diameter grows with copper | +32 ppm/°C in L (*model*; 17 ppm/°C expansion, *source*) | 0.4 µm/°C | Yes |
| Copper resistance, through Q | < 1 ppm/°C in f | negligible | Yes |
| Microcontroller clock (crystal, typically tens of ppm over temperature) | 1:1 in f | about 1 µm over the range | Yes, exactly |
| Cable capacitance changes by 1 pF | 210 ppm of C | 3 µm | No, unless cables are identical and move together |
| Coil fully wet (water between turns) | self-capacitance 0.25 → about 10 pF (*model*) | about 28 µm | Partly |
| Snag or side load in the guide | | about 20 µm hysteresis (*model*) | No |
| Steel within a coil diameter or two | | not modelled; 0.1 to 1.4 mm bias reported on a much larger sensor (*source*) | No |

Over a 40 °C outdoor swing with a steel member and no compensation, the capacitor and
coil terms can add up to about 30 µm and the member 5 µm. With a matched reference coil
and capacitor in the same enclosure, what remains is the mismatch between the two
channels and the mechanical terms. The reference channel is therefore not optional for
field use; it is what turns a laboratory resolution into a field accuracy.

## 2. Temperature

- **Use a reference channel.** A second coil of the same wire, diameter and turns, held
  at fixed length on a low-expansion spacer, with its own C0G capacitor from the same
  reel, in the same enclosure. Report the ratio of the two frequencies.
- **Put both capacitors and both coils at the same temperature.** A reference on the
  circuit board and a sensor a metre away in the sun will not track.
- **Gradients matter more than level.** Sun on one side of an enclosure produces
  differences that no ratio removes. Shade it or give it thermal mass.
- **Log temperature anyway.** A cheap digital sensor beside the coil lets residual drift
  be fitted out afterwards and shows when a reading was taken during a transient.
- **Copper creep** speeds up with temperature. A coil parked near full stretch in a hot
  enclosure is the worst case for permanent set. Design so the resting position is near
  the compressed end.
- **Freezing.** Water in the guide tube can lock turns to the wall. That is the snag
  case, or worse.

## 3. Humidity and condensation

Why this design is fairly tolerant: inductance does not respond to water at all (water
is non-magnetic), and the tank capacitance is 4700 pF, several thousand times the coil's
own. Humidity acts on an inductive sensor through parasitic capacitance, so the defence
is to make parasitics a small fraction of the tank. A design with a 100 pF tank would be
about 50 times more exposed.

What still gets in:

- **Water between the turns.** The model scales self-capacitance by (1 + εr)/2, giving
  about 10 pF for a soaked coil and an apparent shift of about 28 µm. A dew film is
  much less. The shift appears and disappears with the water, which looks like drift.
- **Water on the circuit board.** A film between the tank node and ground adds
  capacitance and leakage right where 0.35 pF is a micron. Conformal-coat the board and
  keep the tank node short.
- **Leakage across the tank.** The tank's parallel resistance is only a few hundred
  ohms, so leakage has to be very bad (tens of kΩ or less) before it changes Q
  noticeably. Dirty or salty water can do it.
- **Hygroscopic plastics.** Nylon and some printed plastics swell several tenths of a
  percent with moisture. If such a part sets the anchor spacing, that is hundreds of
  ppm, larger than any thermal term. PTFE, polypropylene and PEEK absorb almost nothing.
- **Enamel pinholes.** Film insulation has occasional pinholes. In clean air they are
  harmless. Under conductive water two pinholes on adjacent turns make a partial short.
  Heavy-build enamel, or a thin dip of conformal coating on the wound coil, reduces the
  chance. Check that any coating does not glue turns together.

Options, cheapest first:

1. Vent and drain. A small hole at the low point of the tube and enclosure so water
   leaves. Accept shifts while wet.
2. Seal. A soft bellows or boot over the tube ends, with desiccant. The boot must not
   add stiffness or side load.
3. Fill. Silicone oil or dielectric grease in the tube keeps water out and damps the
   coil's internal resonance. It is magnetically invisible, raises self-capacitance by a
   fixed and small amount, and adds viscous drag that will slow the response. Untested;
   worth an experiment because it addresses three problems at once.

The ring-down measurement gives Q on every burst. A sudden fall in Q is a direct sign
of water or a shorted turn, so log it as a health indicator.

## 4. Electrical interference

- **The ring sits in broadcast and amateur spectrum.** 1.6 to 1.8 MHz spans the top of
  the medium-wave AM band and the bottom of the 160 m amateur band. An open coil is a
  small loop antenna. Near a transmitter this will show as bursts of bad readings. If
  it does, move the tank frequency with a different capacitor (the sensitivity in ppm
  does not change), and reject bursts whose cycle-to-cycle period scatter is high.
- **Switching power supplies** radiate harmonics through this range. Keep the coil away
  from converters and motor drives and twist its leads.
- **Shielding has a cost.** A metal shield near the coil is exactly the nearby conductor
  the design tries to avoid. If a shield is needed, keep it more than two coil
  diameters away, slit it so it is not a closed loop around the coil axis, and include
  it in the calibration.
- **Several sensors together.** Fire ring-down channels one at a time. Continuous
  oscillators on nearby coils can pull each other.

## 5. Cable and connections

- Every picofarad between the coil and the board is part of the tank. One metre of
  ordinary coax is about 100 pF, and flexing or warming it changes that by more than a
  micron's worth. Put the tank capacitor and, ideally, the comparator at the coil, and
  send a logic-level signal down the cable.
- Lead inductance adds to the coil's 2 µH. A lead loop that changes shape as the member
  moves is a second, uncalibrated sensor. Twist the leads and anchor them so that the
  moving section is short and bends the same way each time.
- The moving lead is the likeliest fatigue failure. 30 AWG solid magnet wire survives
  few sharp bends. Terminate the coil on a small pad at the moving anchor and continue
  in stranded or tinsel wire with a service loop.
- Solder joints on fine copper corrode where flux residue and moisture meet. Clean and
  coat them.

## 6. Mechanical exposure

- **Vibration.** The free turns have an axial resonance near 90 Hz (*model*) and
  lateral modes besides. Vibration near those frequencies redistributes the turns and
  appears in the reading. Average over a time longer than the vibration period, or damp
  the coil (see the fill option above).
- **Dust and grit** in the tube are snags. Cap the tube ends.
- **Orientation.** Horizontal, the coil rests on the tube and friction is set by its
  weight, which is tiny. Vertical, weight adds a fixed gradient in turn spacing that
  calibrates out. Avoid mounting changes between calibration and use.
- **UV and chemicals** attack polypropylene and many printed plastics outdoors. PTFE is
  inert. Cyanoacrylate bonds weaken in sustained damp; epoxy is the safer adhesive.
- **Overtravel.** Stress reaches yield at roughly 2.5 times the 3 mm design travel for
  this coil. A hard stop that prevents overstretch protects the calibration.

## 7. A build that respects all of the above, cheaply

- Sensor coil and identical reference coil, both in PTFE tubes, both inside one small
  plastic enclosure fixed to the structure.
- Tank capacitors (C0G, same reel) and the comparator on a small coated board in the
  same enclosure; digital signals only on the cable.
- Drain hole at the low point, caps on tube ends, epoxy bonds, stranded pigtail on the
  moving end, hard stop on travel.
- A temperature sensor on the board.
- Firmware reports frequency ratio, Q for each channel, temperature, and a flag for
  noisy bursts.

Apart from the comparator and the microcontroller this is a few dollars of parts.

## 8. Tests that would replace these estimates with data

1. Oven or cold-box sweep of sensor and reference at fixed length: gives the real
   temperature coefficient and how well the ratio cancels it.
2. Breathe on it, then mist it: gives the humidity and condensation shift and whether
   Q warns in time.
3. Extend and retract on a micrometer stage, dry and after wetting and drying: gives
   hysteresis and whether moisture leaves residue that snags.
4. A week parked at mid-stretch: gives creep.
5. Portable AM radio or a switching supply held nearby: gives interference rejection.
