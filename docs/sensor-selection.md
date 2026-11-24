# When to use a stretched coil, and when to use something else

**Project version:** 0.3.0
**Compiled:** 2026-11-23

A stretched coil is one of several ways to measure a few millimetres to a few hundred
millimetres of travel. This page says where it fits and where an ordinary bought
sensor is the better answer.

Figures for the stretched coil are from this project's models and have not been
measured. Figures for the other sensors come from the manufacturer documents listed at
the end; they describe specific parts and are examples, not limits of the technology.
Prices are given only where a source stated one.

## The short version

**Use a stretched coil when** the thing being measured is soft, light or oddly shaped;
when a sensor that pushes back with more than a few hundredths of a newton would
disturb it; when no rigid sensor body can be mounted; or when many channels are needed
and each must cost close to nothing.

**Use something else when** the number has to be trusted without calibrating each unit,
when there is steel close by that cannot be moved, when the stroke is long, or when
only one or two sensors are needed and time is worth more than parts.

For 1 to 3 mm of travel on a rigid mechanism, a Hall sensor and a small magnet is the
rival to beat, and it has not been tested against the coil here.

## Side by side

| | Stretched coil (this project, modelled) | Slide potentiometer | Precision short-stroke potentiometer | String potentiometer | LVDT | Hall sensor and magnet |
|---|---|---|---|---|---|---|
| Example part | 32 turns on 5 mm | Bourns PTA | Megatron MM10 | Celesco SP1 | generic | TI DRV5055 |
| Travel | 1 to 3 mm on a 10 mm coil | 15 to 60 mm | 8 to 15 mm | 120 to 1270 mm | many sizes | about the magnet's length |
| Accuracy without per-unit calibration | none: units differ by 0.3 to 0.8 mm | ±20 % resistance tolerance; linearity not specified | ±2 % linearity (±1 % option) | ±0.25 to ±1 % of range | 0.1 to 0.5 % | set by magnet and placement |
| Repeatability / hysteresis | 0.5 µm free, about 20 µm if snagged | not specified | backlash up to 0.1 mm | ±0.05 % of range | limited by electronics | not stated in the source |
| Force on the measured object | 0.02 N at full stroke | 30 to 250 g·cm operating force | under 0.3 N | 1.9 to 3.7 N cable tension | near zero (free core) | zero |
| Rated life | unknown; copper fatigue and creep untested | 15,000 cycles | 40 million movements | 0.25 to 2.5 million cycles | no wearing parts | no wearing parts |
| Temperature range of the part | untested | −10 to +50 °C | −30 to +105 °C | −18 to +70 °C (−40 option) | very wide | not checked |
| Electronics needed | comparator and fast timer, or a converter module | one ADC pin | one ADC pin | one ADC pin | excitation and demodulation | one ADC pin |
| Bothered by | nearby metal, cable movement, radio interference, snags | dirt, wear, vibration at one spot | dirt, wear | cable sag, wear, fast motion | little | stray magnetic fields, steel nearby, magnet temperature |

Two more options sit outside the table:

- **A flat printed coil with a sliding metal target**, read by the same inductance
  converter chip. Nothing stretches. TI's reference design reports 0.3 to 1.1 mm of
  error over 70 mm of travel; a laboratory eddy-current sensor resolved 46 nm over
  0.5 mm. It needs a circuit board to be made.
- **A digital caliper used as a sensor.** Capacitive scale, 0.01 mm resolution,
  typically $25 to $100, and some models have a data port. Bulky, but it is the
  cheapest way to buy 10 µm over 150 mm with no calibration.

## What each comparison turns on

### Against a potentiometer

A potentiometer wins on simplicity. It is linear enough to use straight from the bag,
it is absolute, and it needs one analogue input. For a one-off measurement of 10 mm or
more to a percent or two, it is the right answer and the coil is not.

The coil wins on three points. It pushes back with 0.02 N where the gentlest
potentiometer found needs up to 0.3 N, which matters on a soft actuator and not on a
steel bracket. It has no sliding contact, so nothing wears a track at a position where
the mechanism dwells or vibrates. And in the model its hysteresis is under 1 µm when
sliding freely and about 20 µm with a snag, where the precision potentiometer above is
specified at up to 100 µm of backlash.

The cheap slide potentiometer and the precision one are different products: 15,000
cycles against 40 million. A comparison with "a pot" has to say which.

### Against a string potentiometer

No contest on long strokes: string pots cover 0.1 m to over a metre, tolerate
misalignment, and install in minutes. A long spring can be read as a coil (TI did it
over 50 mm), but it would sag, swing and stretch unevenly long before a metre.

The string pot's weaknesses are its cable tension of 2 to 4 N, which loads a light
structure; its rated life, which falls to a quarter of a million cycles on long
models; and fast motion, with the example part rated to 11 to 15 g of cable acceleration.

### Against an LVDT

An LVDT is what the coil is trying not to pay for: one hundred to several hundred
dollars before its electronics. In return it gives stated linearity, no wear, a wide
temperature range and a datasheet somebody else stands behind.

Choose the LVDT when the reading has to be defended to someone else, when the sensor
must be swapped without recalibration, or when it must work unattended for years. A
stretched coil has no track record on any of those.

### Against a Hall sensor and magnet

This is the serious low-cost competitor for short strokes. The sensor is a three-pin
through-hole part that outputs a voltage; the magnet is glued to the moving member;
nothing touches. Versions of the part compensate for the magnet weakening with
temperature. TI's application brief gives a simulated best case of ±0.06 mm over
±11 mm, and notes that the usable range is about the length of the magnet.

Where the coil should do better: resolution relative to range, since frequency can be
counted to parts per million and an analogue voltage cannot; and immunity to stray
magnetic fields, which a Hall sensor reads directly. Where the Hall sensor does
better: it is rigid and simple, it needs no megahertz electronics, and steel nearby
changes the magnet's field in a fixed way instead of drifting.

Neither claim has been tested here. A side-by-side on the same stage is a cheap
experiment.

### Against soft stretch sensors

For soft robots the usual alternatives are stretchable resistive and capacitive
sensors. A 2022 review describes resistive ones as having serious hysteresis, enough
to disqualify them for dynamic feedback, and capacitive ones as low in hysteresis but
sensitive to electrical noise, temperature and moisture. A coil measures geometry
through a magnetic field, which rubber, water and temperature do not change, so it
sits between the two: stiffer and more fragile than a printed elastomer sensor, and
less affected by the material it is attached to, as long as it is anchored at two
points and not bonded along its length (see the pneumatic-actuator result in
`literature-review.md`).

## Conditions that rule the coil out

From this project's own models:

- **Mild steel within about 5 mm that cannot be moved.** It adds drift of 0.1 µm/°C or
  more and a dependence on the steel's stress state (`nearby-metal.md`).
- **A metal guide or housing close around the coil.** A closed tube under four coil
  diameters costs inductance, sensitivity and Q.
- **No way to calibrate each unit.** Units differ by up to 0.8 mm on a shared curve
  (`tolerance-and-calibration.md`).
- **Vibration near 90 Hz**, where the free turns resonate, unless the coil is damped.
- **A strong transmitter nearby** at the ring frequency (`field-deployment.md`).
- **Long cable between coil and electronics** that flexes or changes temperature.
- **Standing water or ice** in the guide.
- **The moving member cannot pull and push the coil.** It will not return by itself.

## Conditions that favour it

- The measured object is compliant and a rigid sensor would stiffen or bruise it.
- The sensor must follow a curved or flexing path.
- Loading force must stay in the tens of millinewtons.
- There is no room for a rigid body, a rod or a cable run.
- Many channels: one microcontroller timer can read coils in turn, and each added
  channel is wire, a capacitor and a comparator input.
- Strong static magnetic fields are present, which would upset a Hall sensor.
- The application can calibrate in place and tolerates tens of microns until hardware
  data shows better.

## A quick way to decide

1. Is the stroke over about 50 mm? Use a string pot, a long potentiometer or a caliper
   scale.
2. Must units be interchangeable or the accuracy certified? Use an LVDT or a precision
   potentiometer.
3. Is the measured object rigid, with room for a magnet and no stray fields? Try a Hall
   sensor first.
4. Is a percent or two enough and wear acceptable? Use a potentiometer.
5. Otherwise, and especially if the object is soft or force-sensitive, the stretched
   coil is worth building. Check the rule-out list above before committing.

## What would change this page

- A measured hysteresis and repeatability figure for a real coil. Everything in the
  coil's column is modelled.
- A cycle-life test. "Unknown" in the life row is the largest gap.
- A Hall-sensor benchmark on the same stage.
- Distributor prices for each option at the quantities planned. None were collected.

## Sources

- Bourns PTA slide potentiometer datasheet: <https://users.ece.utexas.edu/~valvano/mspm0/BournsPTASlidePotentiometer.pdf>
- Megatron MM10 linear potentiometer datasheet: <https://www.megatron.de/fileadmin/user_upload/Datenblaetter/Wegsensoren/Potentiometrische/DS_MM10_en.pdf>
- Celesco SP1 string potentiometer datasheet: <https://www.buffalo.edu/content/dam/www/seesl/Documentation/Instrumentation/celesco_sp.pdf>
- TE MTA miniature string potentiometer (76 to 127 mm, ±0.4 % of range): <https://www.te.com/en/product-CAT-CAPS0007.html>
- LVDT characteristics and price range: <https://www.eeworldonline.com/lvdt-position-sensor-faq-part-2-characteristics/>
- TI SBAA513, tracking displacement with linear Hall sensors: <https://ti.com/lit/pdf/sbaa513>
- TI DRV5055 linear Hall sensor: <https://www.ti.com/product/DRV5055>
- TI TIDA linear position reference design (printed coil and target): <https://www.ti.com/lit/pdf/tidua26>
- Eddy-current micro-displacement sensor, 46 nm resolution: <https://www.mdpi.com/2072-666X/15/3/366>
- Digital caliper principle, resolution and price: <https://www.testandmeasurementtips.com/digital-caliper-implementation-extensions-faq/>
- TI, sensing spring compression over 50 mm: <https://www.ti.com/lit/pdf/ssztch7>
- Hao et al., review of soft sensors (resistive sensors show serious hysteresis; capacitive are sensitive to noise, temperature and moisture): <https://link.springer.com/10.1186/s10033-022-00707-2>
