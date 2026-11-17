# Measuring displacement with a stretched coil: what has been done, and what it costs

**Project version:** 0.2.0
**Compiled:** 2026-11-16

Scope: published work on using the inductance of a helical coil, spring, or wound
structure as a displacement or strain sensor, the readout circuits people have used,
and where each approach runs out. The emphasis is on what can be built cheaply.

How to read this: each source is marked with how much of it was read. **[full]** means
the full text was read, **[abstract]** means only the abstract or record page, and
**[vendor]** means manufacturer documentation, which is reliable on what a part does
and optimistic on how well. Prices are as found on the date above and will drift.

---

## 1. The short version

- Using a spring's own inductance as a position sensor is established. It appears in
  robotics papers from 2015 onward, in a TI application article, and in patents on
  suspension travel measurement. Nobody claims it as novel any more.
- Published accuracy is modest: typically 0.1 to 1 % of range, limited by mechanics
  (hysteresis, nearby metal, cable and connection compliance), not by electronics.
  No source found here demonstrates sub-micron accuracy from a stretched coil. The
  resolution is there; the repeatability has not been shown.
- Most published sensors work over tens of millimetres with long springs. A 10 mm coil
  over 1 to 3 mm, as in this project, is at the short, sensitive end of what has been
  tried, which helps resolution and makes mechanical cleanliness matter more.
- The cheapest credible readouts are (a) an inductance-to-digital converter module at
  about $15, (b) a free-running LC oscillator counted by any
  microcontroller, and (c) ring-down timing, which this project uses. Section 4
  compares them. Option (a) should be bought as a baseline before more discrete design.
- Temperature is handled in the literature the same way everywhere: C0G capacitors, and
  a second coil as a reference with the result taken as a ratio.

## 2. Sensors that use a coil or spring as the sensing element

### 2.1 Springs and helical coils

**TI, "Inductive Sensing: How to Sense Spring Compression" (2015) [vendor, full].**
The closest published match to this project. A steel spring (0.7 mm wire, 46 turns,
7.3 mm diameter) replaces the sensor coil on an LDC1612 evaluation board with a 1 nF
capacitor. Stretched from 50 to 100 mm, its inductance falls from 1.92 to 1.01 µH,
oscillating near 2.5 MHz, and the converter returns about 44 output codes per micron.
Two details matter. The spring alone had too little inductance for the chip, so a fixed
2.2 µH inductor was added in series, which dilutes sensitivity. And the article shows
resolution only: no hysteresis, repeatability, or temperature data.
<https://www.ti.com/lit/pdf/ssztch7>

**TI E2E forum thread on the same idea (2021) [vendor, full].** A user with a 3 µH,
3 Ω spring and 1 nF (about 2.9 MHz) needed 10 nH resolution and reported that the
LDC1612 met it. Useful as an independent confirmation at almost exactly this project's
inductance and frequency. TI's advice was to use their design calculator's spring tab
and application note SNOA944.
<https://e2e.ti.com/support/sensors-group/sensors/f/sensors-forum/1049446/ldc1612-inductance-sensing-of-a-spring-while-expanding-or-compressing>

**Sahu, Tamadon, Rosa, Renaud, Menciassi, "A Spring-Based Inductive Sensor for Soft and
Flexible Robots," IEEE Sensors Journal 22(20), 2022 [abstract].** A spring used as a
stretchable strain sensor and possibly as a structural element. Strain is estimated
from a voltage measurement instead of by evaluating inductance directly, which the
authors call easier to implement; component values and interrogation frequency are
tuned for performance. Reported hysteresis 0.1 %, precision about 0.14 %, accuracy
0.9 %. Demonstrated in closed loop on a pneumatic muscle and a bending manipulator.
On a 3 mm range those percentages would be 3 µm, 4 µm and 27 µm.
<https://research.utwente.nl/en/publications/a-spring-based-inductive-sensor-for-soft-and-flexible-robots/>

**Choi, Park, Won, Park, "Soft Inductive Coil Spring Strain Sensor Integrated with SMA
Spring Bundle Actuator," Sensors 21(7):2304, 2021 [full].** A nitinol coil (0.5 mm
wire, 3 mm outer diameter, 116 turns, 58 mm long) moulded in soft silicone. Two coils
move in opposition and are wired as a differential half-bridge read by an AD598 LVDT
signal conditioner. Linear fit against a laser sensor R² ≈ 0.999 over 0 to 40 mm;
bench calibration needed a third-order polynomial. Response is flat to 1.67 Hz and
down to 80 % with 10° lag at 2 Hz. The authors ran it under water with supply
temperatures from 36 to 90 °C and report no effect on the output, without numbers.
Bare contact between the sensing coil and neighbouring metal springs made the
measurement unstable, hence the silicone. Hysteresis is described only as slight.
<https://pmc.ncbi.nlm.nih.gov/articles/PMC8036631>

**van der Weijde, Vlasblom, Dobbe, Vallery, Fritschi, "Force sensing for compliant
actuators using coil spring inductance," IROS 2015 [record only].** The first robotics
use found here of a series-elastic actuator's own spring as its deflection sensor.
<https://research.tudelft.nl/en/publications/force-sensing-for-compliant-actuators-using-coil-spring-inductanc>

**van der Weijde, van Ostayen, Vallery, "Influence of internal oscillations on force
sensing in coil springs," IEEE RA-L 2(3), 2017 [abstract].** A spring has mass, so
impacts excite internal oscillations between its turns. These raise measurement
uncertainty for every method tested, including inductance, by an amount comparable to
the sensors' ordinary uncertainty. This is the dynamic version of the uneven-stretch
problem analysed in `nonuniform-stretch.md`. The coil in this project has its first
internal mode near 90 Hz.
<https://research.tudelft.nl/en/publications/influence-of-internal-oscillations-on-force-sensing-in-coil-sprin/>

**van der Weijde, "Self-sensing of coil springs and twisted and coiled polymer
muscles," doctoral thesis, TU Delft, 2020 [abstract].** The long-form treatment of the
two papers above. Not read beyond the abstract; likely the best single reference for
anyone taking this further.
<https://repository.tudelft.nl/record/uuid:f00eb0bb-6a04-44ba-a7ed-89127a4b3029>

**Patents.** US 10,036,655 and US 10,386,205 cover measuring the compression travel of
a conductive suspension spring from its electrical properties. Not read; listed so that
anyone commercialising a spring-as-sensor checks them.

### 2.2 Wound structures that are not springs

**Felt, Chin, Remy, "Contraction Sensing with Smart Braid McKibben Muscles," IEEE/ASME
Trans. Mechatronics 21(3), 2016 [full].** The braid of a pneumatic muscle is woven from
insulated wire, forming a solenoid whose inductance rises from 2.96 to 6.88 µH as the
muscle contracts. A straight-line calibration gave 0.48 mm residual standard deviation,
0.83 mm on repeat calibration, and about 1 mm mean error under a 5 kg load. The paper
is the best source on two questions that matter here:

- *Nearby metal.* A steel rod beside the sensor biased it by 0.1 to 0.3 mm on average
  and up to 1.4 mm worst case.
- *Non-magnetic surroundings.* Wood, rubber, air and water made no difference in their
  modelling; the permeability change due to water was estimated below 0.001 %.

Inductance was read with a laboratory LCR meter at 30 kHz and 40 samples per second,
so the paper says nothing about cheap readout. The authors also found that a long-
solenoid formula over-predicts and a filament (Neumann) calculation matched the
measured sensitivity within 1 %, which supports the modelling choice in this project.
<https://pmc.ncbi.nlm.nih.gov/articles/PMC5424474>

**Felt, Remy, Telleria, Allen, Hein, Pompa, Albert, "An inductance-based sensing system
for bellows-driven continuum joints in soft robots," Autonomous Robots 43(2), 2019
[full].** Wire loops around each fold of a bellows; the signal comes from mutual
inductance between loops as the folds separate. Each circuit resonates with a 100 pF
NP0 capacitor and four circuits are read by one LDC1614. Orientation error 1.1° rms.
The limitations they list transfer directly: sensitivity falls sharply as turns move
apart, more turns raise Q but add parasitic capacitance, neighbouring circuits can
cross-talk, and metal contact biases the reading. Their remedy for metal is redundant
sensors on opposite sides. Temperature is not discussed.
<https://pmc.ncbi.nlm.nih.gov/articles/PMC6456049>

**Zhang, Li, Yang, Zhang, "Inductance-Based Force Self-Sensing in Fiber-Reinforced
Pneumatic Twisted-and-Coiled Actuators," arXiv 2603.18555 [full].** Nickel wire wound
helically round a pneumatic actuator, read by an LDC1614 and an Arduino. A warning for
this project: inductance tracked force with low hysteresis but tracked *length* with
strong hysteresis, and displacement error was 11 % of range. When the coil is attached
along a soft body instead of at two points, the body's hysteresis becomes the sensor's.
<https://arxiv.org/pdf/2603.18555>

**Chen and Conn, "A stretchable inductor with integrated strain sensing and wireless
signal transfer," IEEE Sensors Journal, 2020 [abstract].** Liquid-metal spiral in soft
elastomer; inductance linear with strain to 100 % extension; hysteresis negligible when
slow and under 10 % when fast. Shows the rate dependence that elastomer-supported coils
bring. Fabrication is not cheap or quick.
<https://research-information.bris.ac.uk/en/publications/a-stretchable-inductor-with-integrated-strain-sensing-and-wireles/>

### 2.3 What the published sensors have in common

| | Published range | This project |
|---|---|---|
| Coil length | 50 to 100 mm typical | 10 mm |
| Travel | 10 to 50 mm | 1 to 3 mm |
| Accuracy shown | 0.1 to 1 % of range | not yet measured |
| What limited it | hysteresis, metal, compliance of attachments | expected: guide friction, member expansion |
| Temperature data | almost none | modelled only |
| Humidity data | none | modelled only |

The gap in the literature is environmental. Robot papers run for minutes in a lab. Only
one source here ran a coil sensor through a temperature range, and it gave no numbers.

## 3. Related inductive methods, and why they are not this

**LVDT.** A moving ferromagnetic core changes the coupling between a primary and two
secondaries. Non-contact, effectively unlimited mechanical life, resolution set by the
electronics, accuracy typically 0.1 to 0.5 %. A trade FAQ puts a basic LVDT at about
one hundred to several hundred dollars before excitation and signal conditioning. That
price is the reason for this project. [trade press, full]
<https://www.eeworldonline.com/lvdt-position-sensor-faq-part-2-characteristics/>

**Linear potentiometer.** Cheaper than an LVDT, lower resolution, and it wears: a
manufacturer comparison describes potentiometer life as much shorter because of
friction. No cycle counts were given in the sources found. [vendor, full]
<https://transtekinc.com/blog/how-do-lvdts-measure-up-against-competing-methods/>

**Eddy-current sensing with a fixed coil and a moving metal target.** The mainstream
low-cost inductive method, and what TI's converter family was built for. TI's linear
position reference design uses a 100 mm printed coil and a sliding aluminium target,
with errors of 0.3 to 1.1 mm over 70 mm of travel. [vendor, full] A laboratory
eddy-current micro-displacement sensor reached 46 nm resolution over 0.5 mm, but its
output drifted 586 mV of a 10 V span between 2 and 58 °C before compensation and
44 mV after, using a digital potentiometer with a temperature lookup table. [full] The
lesson is that sub-micron resolution from a coil is ordinary and sub-micron stability
over temperature takes deliberate compensation.
<https://www.ti.com/lit/pdf/tidua26> ·
<https://www.mdpi.com/2072-666X/15/3/366>

A stretched coil differs from all three in having no separate core, wiper or target:
the coil is the moving part. That removes a component and an alignment, and it is why
the coil's own mechanics (friction, creep, internal resonance) become the error budget.

## 4. Readout methods, cheapest first

All of these turn inductance into something a microcontroller can count. The comparison
assumes this project's coil: 2 µH, about 0.2 Ω, 37,000 ppm of frequency per millimetre.

### 4.1 Free-running LC oscillator and a frequency counter

Make the coil and capacitor the tank of a continuous oscillator (a Colpitts stage, a
comparator with feedback, or an unbuffered CMOS inverter) and count cycles in a fixed
gate time.

- *Cost:* one transistor or one logic gate. Under a dollar.
- *Microcontroller:* almost any. Counting 1.7 MHz needs only a counter input, not fast
  timestamps. A 16 MHz ATmega accepts external counter clocks up to 6.4 MHz, so the
  classic Arduino boards that cannot time a ring-down can count an oscillator.
- *Resolution:* one count in the gate. At 1.7 MHz, a 10 ms gate holds 17,000 cycles, so
  one count is 59 ppm or 1.6 µm; a 100 ms gate gives 0.16 µm at 10 readings per second.
  Timing the gate edges against a fast clock (reciprocal counting) does better.
- *Limits:* the active device is inside the frequency-determining loop. Its input
  capacitance, bias and amplitude all pull the frequency and all drift with temperature
  and supply. The oscillator radiates continuously and two channels can lock to each
  other. Low Q makes this worse, and this coil's Q is modest (30 to 40 by the model).

This is the method to try first when the budget is cents and the target is tens of
microns.

### 4.2 Inductance-to-digital converter (TI LDC1612 / LDC1614)

The same oscillator-and-counter idea, integrated and done well. [vendor, full]

- *Specs:* 28-bit output, sensor frequency 1 kHz to 10 MHz, two channels (four on the
  LDC1614), 2.7 to 3.6 V, I²C. TI states that multiple channels are intended for
  environmental and ageing compensation, which is exactly the reference-coil scheme.
- *Cost:* the chip is surface-mount only (12-pin WSON), which conflicts with this
  project's through-hole rule. A ready-made Grove module carrying it was listed at
  £12.31 before tax in single quantity, which sidesteps the soldering.
- *Resolution:* governed by conversion time and by how far the frequency moves.
  TI's SNOA944 gives conversion time = 16 × RCOUNT / f_ref (26 ms at maximum count
  with a 40 MHz reference, 0.1 ms at a count of 256) and shows best performance with
  the sensor near 1 MHz, usable from 0.4 to 6 MHz. This coil's 20 % inductance swing
  is large by the standards of that note, which helps.
- *Limits:* resolution figures say nothing about drift. TI's forum threads on
  temperature drift mostly end with "use a reference coil" and a pointer to SNAA212.
  Sensor amplitude must be set between 1.2 and 1.8 V. Channels are measured in
  sequence, so sensor and reference are not sampled at the same instant.

<https://www.ti.com/product/LDC1612> · <https://www.ti.com/lit/pdf/snoa944> ·
<https://uk.rs-online.com/web/p/sensor-development-tools/1887096>

This is the baseline to beat. It is cheap, documented, already demonstrated on a
spring, and it removes the comparator, MOSFET, mid-rail and fast-timer design work.

### 4.3 Ring-down: kick the tank and time the decay (this project)

- *Precedent:* low-power water and gas meters. TI's MSP430 Scan Interface excites an LC
  sensor with a short pulse and lets it ring about a mid-supply reference generated
  on-chip, then uses a comparator and DAC to judge the decaying amplitude. Example
  values are 100 µH with 1 nF (about 500 kHz) or 470 pF (about 725 kHz). [vendor, full]
  Those products count damping to detect a passing metal vane; they do not measure
  frequency precisely. The mid-rail arrangement in this project's schematic is the same
  idea arrived at independently, which is reassuring.
- *Cost:* comparator, MOSFET, a few passives, and a microcontroller with a fast timer.
  The fast comparator is the expensive part.
- *Strengths:* the tank rings free, with no active device in the loop, so the frequency
  is set only by L, C and loss. Power is drawn only during a burst. Channels cannot
  lock because only one rings at a time. Q comes out of the same measurement for free
  and can flag a wet or damaged coil.
- *Limits:* only a few tens of cycles per burst, so resolution comes from averaging
  many bursts; needs timer resolution of roughly 10 ns or better; comparator delay
  varies with the decaying amplitude; the ring frequency is the damped one and must be
  corrected for Q.

<https://www.ti.com/lit/pdf/slaa222>

### 4.4 Relaxation oscillator (555 timer)

**Nowicki, "A Modified Impedance-Frequency Converter for Inexpensive Inductive and
Resistive Sensor Applications," Sensors 19(1):121, 2019 [full].** A 555 in astable mode
with the sensor impedance as the timing element, near 100 kHz, read as a frequency. The
converter cost about 1 € in parts. With an inductive displacement sensor it resolved
0.1 µm and was accurate to about 1 µm (0.1 %), with no detectable hysteresis. The
author says plainly that it is not designed for high accuracy and that each sensor
needs its own software calibration.

It does not transfer directly. An L/R timing circuit depends on coil resistance, and
copper resistance changes 0.39 % per °C. It also needs far more inductance than 2 µH:
at 100 kHz this coil's reactance is about 1 Ω. It would suit a coil with a ferrite core
or several hundred turns.
<https://pmc.ncbi.nlm.nih.gov/articles/PMC6339085>

### 4.5 Fixed-frequency drive and amplitude or bridge measurement

Drive the coil from a fixed oscillator and measure the voltage across it (Sahu 2022),
or put two opposed coils in a half-bridge and use an LVDT signal conditioner (Choi
2021). The bridge version cancels temperature and linearises the response, and it
needs two moving coils and a dedicated LVDT conditioner IC (price not checked here;
historically an expensive part). Amplitude measurement brings back gain and offset drift
that frequency measurement avoids.

### 4.6 Laboratory LCR meter

What most papers use to characterise the coil. Right for verification, not deployment.

### 4.7 Comparison

| Method | Parts cost | MCU needed | Resolution | Main weakness | Use when |
|---|---|---|---|---|---|
| LC oscillator + counter | < $1 | any | ~1 µm at 100 Hz | drift of the active device | cents matter, tens of µm suffice |
| LDC1612 module | ~$15 | any with I²C | sub-µm | surface-mount chip; sequential channels | fastest route to a working sensor |
| Ring-down (this project) | comparator-dominated | 10 ns timer | sub-µm with averaging | few cycles per burst | best stability per channel, low power |
| 555 relaxation | ~$1 | any | 0.1 µm reported | needs high L; resistance tempco | cored or many-turn coils |
| Bridge + LVDT conditioner | high | ADC | good | cost, two coils | not for low cost |

The resolution column is what the electronics can do. No row has been shown to hold a
micron over temperature and time on a stretched coil.

## 5. Temperature and humidity in the literature

**TI SNAA212A, "LDC100x Temperature Compensation" [vendor, full].** The clearest list of
drift sources for an LC sensor:

- Coil resistance: 3900 ppm/°C for copper. Dominant if the measurement depends on
  resistance or loss, small if it depends on frequency.
- Inductance of a wound copper coil: about 17 ppm/°C from thermal expansion.
- Capacitor: about 30 ppm/°C for C0G, which the note recommends.
- Nearby metal: tens of ppm when a target is very close, single digits beyond a fifth
  of a coil diameter.
- Mechanical expansion of whatever sets the geometry, which can exceed all of the above.

Its remedies: measure inductance in preference to loss; use C0G; calibrate against
temperature; or use two sensors and take a ratio, for which it expects errors under
0.1 %. This agrees with the plan already in this project's specification.
<https://www.ti.com/lit/pdf/snaa212>

**Vogel, Chaturvedi, Nihtianov, "Humidity Sensitivity and Coil Design of a
High-Precision Eddy-Current Displacement Sensor," Eurosensors 2017 [abstract].**
Inductive sensors are inherently less sensitive to environment than capacitive ones,
but humidity still gets in through the coil's parasitic capacitance, and more so at
higher excitation frequency. The authors derive a minimum self-resonant frequency for
the coil from the humidity range and the allowed error. The rule that follows: keep the
operating frequency far below the coil's self-resonance, so that the coil's own
capacitance is a negligible part of the tank. This project does that by a wide margin
(a 4700 pF tank against a fraction of a picofarad of self-capacitance).
<https://www.mdpi.com/2504-3900/1/4/283>

**Magnet wire.** A manufacturer's insulation guide describes polyurethane enamel as
solderable with excellent resistance to moisture and most solvents, and
polyurethane-nylon as solderable with better lubricity for winding. [vendor, full]
Solderable polyurethane or polyurethane-nylon wire is the cheap default and is suitable
for damp service. The sources found do not address abrasion life in a sliding coil.
<https://mwswire.com/wp-content/uploads/2024/01/MWS-magnet-wire-insulation-guide.pdf>

`field-deployment.md` turns these into numbers for this design.

## 6. What the literature does not answer

1. Repeatability of a short stretched coil at the micron level. No source measured it.
2. Long-term drift: copper creep under sustained stretch, enamel wear in a guide,
   ageing of bonds. No source ran longer than a laboratory session.
3. Behaviour through condensation and drying. One source ran under water; none cycled.
4. Whether ring-down or a continuous oscillator is more stable on the same coil. The
   two have not been compared side by side in anything found here.

Items 1 and 4 are cheap experiments and would be worth more than further reading.

## 7. Not found or not accessible

- The University of Twente student thesis "Characterizing a spring-based inductance
  sensor and investigating external object interference" looks directly relevant to
  the nearby-metal question; its page would not load. <https://essay.utwente.nl/essays/97053>
- Felt's companion paper on combined force and displacement sensing with smart braids
  was blocked by an access check.
- "Inductive strain sensor with high repeatability and ultra-low hysteresis" (Harbin
  Institute of Technology record) could not be opened.
- No independent price was found for the bare LDC1612 or for the LT1016 comparator.
  Check distributor pricing before comparing costs.
- Part 2 of the Machine Design "true cost of ownership" series, which should hold
  sensor life figures, was not retrieved.
