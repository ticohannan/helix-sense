# Stretch-Coil Displacement Sensor — Mechanical Handoff

**Version:** 0.3.0
**Date:** 2026-11-23
**For:** Mechanical / controls engineering
**Accompanying files:** `coil-sensor-schematic-v0.1.0.svg`, `coil-sensor-circuit-spec-v0.3.0.md`, `tools/coil_stretch_inductance_tool.py`

**Changed since v0.2.0:** the metal keep-out distance is now a modelled figure and is
larger (§5.4), and each sensor must be calibrated after it is installed (§5.7).

**Changed since v0.1.0:** force and stress figures corrected upward (§4.1), sensitivity
figures recomputed (§2, §3), and a new requirement on how evenly the coil stretches (§5.6).

---

## Read this first: the circuit has changed

The schematic attached to this document is **not** the configuration discussed
previously. Several parts changed and one was removed. You do not need to follow the
electrical reasoning in detail, but the headline is:

- The measurement circuit now floats on a 2.5 V reference instead of ground.
- The isolation diode is gone entirely.
- The comparator and microcontroller are both much faster parts.

None of this changes what the mechanics have to do. It changes how well we can resolve
what the mechanics deliver. The mechanical requirements in §5 are the part that matters
to you, and they have *not* moved much — except that the choice of member material now
matters more than we originally thought (§6).

---

## 1. What we are building

A displacement sensor with a **1–3 mm range** and, we hope, sub-micron resolution.

The sensing element is a small helical coil of enamelled copper wire — 32 turns of
30 AWG on a 5 mm diameter, about 10 mm long when its turns are touching. One end is
anchored to a fixed reference, the other to the member whose motion we want to measure.
As the member moves, the coil stretches, and we detect that stretch electrically.

There is no contact, no wiper, no optical path, and nothing to wear except the wire
itself.

## 2. Why a coil measures displacement

An inductor stores energy in the magnetic field inside and around its turns. How much
it stores for a given current is its *inductance*, L, measured in henries. Ours is
about 2 microhenries.

The key fact: **inductance depends on how tightly the turns are packed together.**
Adjacent turns reinforce each other's magnetic field. Pull them apart and the
reinforcement weakens, so inductance falls. Nothing about the wire changes — the turn
count is fixed and the copper is the same. Only the spacing changes.

For our geometry, stretching 3 mm drops inductance from about 2.0 µH to about 1.6 µH.
A 20% change over the full range, which is a large, comfortable signal.

Two things that may not be obvious:

**Shorter coils are more sensitive.** Sensitivity per millimetre scales roughly as
1/(coil length). A 10 mm coil gives about 7.5% inductance change per mm; a 20 mm coil
gives about 4.3%. If we need more signal, we shorten the coil rather than lengthening it.

**Filling the coil with rubber or plastic does essentially nothing to the inductance.**
This one catches people out. Inductance responds to *magnetic* permeability, and silicone,
polypropylene, PTFE and epoxy are all magnetically identical to air. Potting the coil
would not improve or degrade the reading. (It would slightly change a parasitic
capacitance, which is a second-order effect we account for separately.) So if you were
considering a filler for mechanical reasons, that decision is yours to make on mechanical
grounds alone.

**Nearby metal is a different story.** Any conductor within a coil diameter or two will
have currents induced in it, which pushes back on the coil's field and changes both the
reading and its temperature behaviour. See §5.4 — this is a real constraint on your
design.

## 3. Why we measure a frequency, not an inductance

This is the part that will feel most familiar to you.

Directly measuring 2 µH to one part in ten thousand is hard. Instead we wire the coil to
a capacitor to form a resonant circuit, give it a kick, and measure how fast it rings.

**It is exactly a mass-spring-damper.** The governing equation is the same second-order
ODE you would write for a mechanical oscillator:

| Electrical | Mechanical |
|---|---|
| Inductance L | Mass (inertia) |
| 1 / Capacitance C | Spring stiffness |
| Resistance R | Viscous damping |
| Ring frequency f = 1/(2π√(LC)) | Natural frequency ωₙ = √(k/m) |
| Quality factor Q | 1 / (2ζ) |

So: we tap the structure and read its natural frequency. Stretching the coil reduces its
"mass," and the natural frequency rises. The circuit rings at about 1.6 MHz when the coil
is compressed and about 1.8 MHz at full stretch.

Frequency is the easiest quantity to measure precisely with a microcontroller, because it
reduces to counting clock edges. Our sensitivity works out to roughly **37,000 parts per
million of frequency per millimetre** of displacement at mid-range — so one micron of
motion is a 37 ppm frequency shift, which is well within reach. The response is not a
straight line (it bends by about 1% of full scale), so we calibrate against a curve.

The ring decays like any underdamped system, over roughly 20 microseconds, and we measure
across a window in the middle of the decay. We repeat this a few hundred times and average,
which is why the whole measurement still updates more than a hundred times a second.

## 4. The mechanical arrangement we have assumed

**Please check this against your own assumptions — it may not be what you pictured.**

The proposal is:

- The coil sits **loose inside a thin-walled non-conductive tube** — the original phrasing
  was "like a plastic straw." PTFE is preferred over polypropylene for lower friction.
- The tube is a **lateral guide only**. It does not carry load and does not set the length.
- **Only the two ends of the coil are anchored** — one to the fixed reference, one to the
  moving member. The middle of the coil floats freely inside the tube.
- The coil is **not wound onto a former** and is **not potted**.

The reason for the tube is that a 10 mm coil of 30 AWG wire is floppy. Left unsupported it
would sag, buckle sideways, or coil-whip during motion. Any of those bend the magnetic
axis and corrupt the reading. The tube keeps it straight and coaxial without constraining
the thing we actually want to change, which is length.

The reason nothing else touches the coil is that whatever carries the length also carries
the thermal expansion — see §6.

### 4.1 Force and stress

We ran the helical-spring numbers, because a coil that plastically deforms would destroy
repeatability.

- **Restoring force at 3 mm extension: about 19 mN.** Negligible. The coil will not load
  your mechanism meaningfully.
- **Wire shear stress: about 16 MPa, against roughly 40 MPa shear yield for annealed
  copper.** About 40% of yield, so no permanent set is expected. (v0.1.0 said 13 MPa and
  a third of yield; it counted the bonded turns as active.) Every extra turn caught in
  the bond raises this, so long bond joints are not free.

The margin comes from the high spring index — our coil diameter is about 20× the wire
diameter, so the wire works mostly in torsion rather than tension. Stretching the *coil*
by 30% does not stretch the *wire* by anything like that.

**But the coil will not return itself.** At 19 mN it is mechanically irrelevant as a
spring. The member must positively drive the coil in both directions, which is why both
ends are bonded rather than one end simply resting.

The residual mechanical risk is **room-temperature creep in copper** if the assembly sits
stretched for long periods. Worth considering if this will hold static positions for
weeks.

## 5. What the electronics need from the mechanics

### 5.1 Straightness and coaxiality
The coil must stay on a straight axis. Bending or lateral bowing changes inductance
independently of length, and we cannot distinguish that from real displacement. This is
the tube's job.

### 5.2 Low friction, no stick-slip
If the coil rubs on the tube wall, we get hysteresis — a different reading going up than
coming down. This is the single most likely source of non-repeatability in the whole
design. We want clearance, a slippery bore, and ideally no side load.

### 5.3 Uniform turn distribution
Our model assumes the free turns spread evenly. The turns caught in the adhesive at each
end do not spread, and we account for that — we currently assume about 2 dead turns per
end. **Please tell us how long the bond joints will actually be**, in turns or in
millimetres.

### 5.4 Keep conductors away
Metal in the coil's field acts as a shorted turn: it lowers the inductance and shifts
the reading. We have now modelled how much (`docs/nearby-metal.md`), and the rule is:

- **10 mm from the coil's centreline to any metal surface running alongside it.**
- **7.5 mm from the last turn to any metal beyond the ends**, anchors included.
  Non-conductive standoffs between the bond points and any metal structure.
- **No metal screw, pin or rod entering the coil**, and no metal guide tube.
- **Prefer aluminium, brass or 300-series stainless to mild steel** for anything that
  has to be close. Mild steel is magnetic, and its effect on the coil drifts with
  temperature and with the stress in the steel.

Why these distances: fixed metal only shifts the calibration, which §5.7 takes care of.
The problem is the coil moving relative to the metal. With an aluminium surface 5 mm
from the centreline, a 0.1 mm sideways shift of the coil in its tube reads as about
7 µm. At 10 mm it reads as under 1 µm.

If 10 mm cannot be had, tell us what metal and how close. Closer is workable with a
non-magnetic metal and a snug guide; it is a problem with mild steel under 5 mm.

### 5.5 Constant coil diameter
Our model assumes the coil diameter does not change as it stretches. For a free helix this
is a good assumption. It would break if the coil were bonded into an elastomer that necks
under tension, because inductance goes as diameter *squared* — that would be a bigger
effect than the length change we are trying to measure. Please confirm nothing in the
mounting radially constrains or squeezes the coil.

### 5.6 Even stretch, or at least repeatable stretch
The reading depends on where every turn sits, not only on the end-to-end length. A gap
at the centre of the coil is worth about twice as much signal as a gap next to a bond,
so if the stretch shifts between the middle and the ends the reading shifts with it.

What the model says about this design (details in `docs/nonuniform-stretch.md`):

- A coil sliding freely in a smooth tube, lying horizontal: friction error under half
  a micron. Uniform friction largely cancels because the coil is symmetric end to end.
- One turn that snags (a burr, a kink, a blob of adhesive) a quarter of the way along:
  about 20 µm of difference between extending and retracting.
- A coil bowed or pressed against the tube wall with a few times its own weight:
  also about 20 µm.

So the requirement is a smooth bore, no adhesive wicking past the bonded turns, and no
side load. A fixed unevenness (the coil wound slightly irregularly) is harmless because
it is the same every cycle and calibrates out.

### 5.7 Access for calibration after installation
Two coils wound to the same recipe differ by several percent, and anything metallic
nearby shifts the reading again, so each sensor is calibrated in its final position.
We need a way to set the moving member to at least three known positions across the
stroke with the sensor installed: a micrometer head, gauge blocks or shims against a
hard stop. The calibration is only as good as those positions, so a reference good to
a few microns gives a sensor good to a few microns.

## 6. The material choice that matters most

**We need to know the material and coefficient of thermal expansion of the member the coil
anchors to.** This is currently the largest open item in the design.

The reason: whatever sets the distance between the two anchor points also sets what we
read. Thermal expansion of that member is indistinguishable from real displacement.

| Member material | CTE | Apparent drift over a 10 mm span |
|---|---|---|
| Invar | 1.2 ppm/°C | 0.012 µm/°C |
| Steel | 12 ppm/°C | 0.12 µm/°C |
| Aluminium | 23 ppm/°C | 0.23 µm/°C |
| Polypropylene | 100 ppm/°C | 1.0 µm/°C |
| Silicone rubber | 250 ppm/°C | 2.5 µm/°C |

Our electrical resolution should land below a micron. So with a steel member the
electronics are the limiting factor and everything is fine. With an elastomeric member,
**a two-degree room temperature change swamps the entire measurement.**

This is why the guide-tube arrangement is good news: the tube's own expansion does not
matter, because it carries no length. Only the anchored member does.

If a low-CTE member is not available, our fallback is a second identical coil held at
fixed length as a reference channel, measured as a frequency ratio. That cancels most
electrical drift and — if the reference shares the same structure and thermal environment
— much of the mechanical drift too. It is far easier to design in now than to retrofit.

## 7. What we need from you

1. **Member material and CTE.** Highest priority (§6).
2. **Bond joint length**, in turns or millimetres, at each end (§5.3).
3. **What metal sits within 10 mm of the coil's centreline or 7.5 mm of its ends**, what
   it is made of, and how the anchors attach (§5.4).
4. **Tube bore and material**, and expected radial clearance to the coil (§5.2).
5. **Confirmation that nothing radially constrains the coil** (§5.5).
6. **Duty cycle** — how many extension cycles over life, and whether it holds static
   positions for long periods (creep, §4.1).
7. **Whether 19 mN of parasitic force is acceptable** in your mechanism (it almost
   certainly is, but you should confirm rather than us assume).
8. **Orientation and vibration environment** — a floppy coil in a vibrating assembly may
   need more support than a guide tube provides. The free turns have an internal axial
   resonance near 90 Hz; vibration around that frequency will show up in the reading.
9. **How the member can be set to known positions for calibration** once the sensor is
   installed (§5.7).

## 8. Assumptions you should feel free to challenge

We picked several things on electrical grounds that you may have better reasons to change.
None of them are locked.

- 10 mm compressed length. Chosen because shorter is more sensitive; up to 20 mm is
  workable at reduced sensitivity if packaging demands it.
- 5 mm coil diameter. Larger diameter reduces wire stress and increases inductance, but
  costs radial space and worsens the metal-clearance requirement.
- 30 AWG wire. Thinner wire packs more turns into the same length but is more fragile and
  has higher resistance, which reduces signal quality.
- Both ends bonded. If your mechanism can only anchor one end, tell us — it changes the
  design substantially, because the coil cannot return itself.
- Coil loose in a tube. If you would rather support it some other way, the requirements in
  §5 are what any alternative has to satisfy.

## 9. Short glossary

**Inductance (L, henries)** — how much magnetic energy a coil stores per unit of current.
Our sensing quantity.

**Capacitance (C, farads)** — how much charge a capacitor stores per unit of voltage. We
add a fixed one to make the circuit resonate.

**Resonant frequency** — the natural frequency of the L-C pair, f = 1/(2π√(LC)). What we
actually measure.

**Ring-down** — kicking the circuit and watching it oscillate and decay. Directly analogous
to tapping a structure and watching it settle.

**Q (quality factor)** — how many cycles the ringing lasts before decaying. Inverse of
mechanical damping ratio: Q = 1/(2ζ). Ours is around 30, so the ring lasts a few tens of
cycles.

**Permeability vs permittivity** — permeability is the magnetic property that affects
inductance; permittivity is the electrical property that affects capacitance. Plastics and
rubbers change the second and not the first, which is why potting the coil does not affect
the reading.

**ppm (parts per million)** — 1 ppm is 0.0001%. Our sensitivity is ~37,000 ppm/mm, so
1 micron of displacement produces a 37 ppm frequency shift.
