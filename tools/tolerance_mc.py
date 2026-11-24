# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Tico Hannan
"""Build tolerances and calibration: how alike are two hand-wound sensors, and how
many calibration points does each one need?

Monte Carlo over the things that vary from one build to the next (coil diameter, wire
build, how closely the turns sit, how many turns the adhesive catches, capacitor
value), then four questions:

  1. How far apart are the units?                      spread of L, f, sensitivity
  2. Which tolerance is responsible?                   one-at-a-time contributions
  3. How much calibration does a unit need?            shared curve / 1 point / 2 points
                                                       / n-point polynomial
  4. What does a reference coil leave uncancelled?     mismatch and temperature split

Run:  python tools/tolerance_mc.py        Edit DESIGN and TOL to try another build.
"""
import numpy as np
import matplotlib.pyplot as plt
import helix_core as hc
from plotstyle import S1, S2, S3, S4, MUTED, SECOND, save, report

# ------------------------------------------------------------------ DESIGN
AWG = 30
N = 32                  # turns
N_DEAD = 2              # nominal bonded turns per end
D_COIL = 5.0e-3         # mean coil diameter, m
C_TANK = 4700e-12       # tank capacitor, F
C_STRAY = 15e-12        # stray capacitance, F
X_MAX = 3.0e-3          # full-scale displacement, m
UNITS = 2000
SEED = 11

# ------------------------------------------------------------------ TOLERANCES (1 sigma)
TOL = dict(
    diameter=0.010,     # coil mean diameter, fraction (mandrel + springback)
    wire_od=0.015,      # enamelled wire OD, fraction (enamel build)
    rest_gap=10e-6,     # extra gap per turn at rest, m, half-normal (turns not quite touching)
    bond_turns=1,       # bonded turns per end: nominal +/- this many, uniform, each end
    cap=0.005,          # tank capacitor, fraction (1 % part taken as 2 sigma)
    stray=5e-12,        # stray capacitance, F
)
# ------------------------------------------------------------------

D_WIRE = float(hc.awg_to_mm(AWG)) * 1e-3
A_WIRE = 0.5 * D_WIRE
D_OUT = hc.enamel_od_mm(AWG) * 1e-3
XS = np.linspace(0.0, X_MAX, 25)


def unit_curve(D, d_out, extra, n1, n2, C):
    """Ring frequency of one built unit at each displacement in XS."""
    gaps0 = d_out + extra
    lo, hi = max(n1 - 1, 0), (N - 1) - max(n2 - 1, 0)
    nfree = hi - lo
    f = np.empty(len(XS))
    for k, x in enumerate(XS):
        gaps = gaps0.copy()
        gaps[lo:hi] += x / nfree
        f[k] = hc.resonant_f(hc.inductance(hc.positions_from_gaps(gaps), D, A_WIRE), C)
    return f


def draw(rng, active=None):
    """One random unit.  active = set of tolerance names to vary (None = all)."""
    on = (lambda k: True) if active is None else (lambda k: k in active)
    D = D_COIL * (1 + TOL["diameter"] * rng.standard_normal()) if on("diameter") else D_COIL
    d_out = D_OUT * (1 + TOL["wire_od"] * rng.standard_normal()) if on("wire_od") else D_OUT
    extra = np.abs(TOL["rest_gap"] * rng.standard_normal(N - 1)) if on("rest_gap") else np.zeros(N - 1)
    b = TOL["bond_turns"]
    n1 = N_DEAD + (rng.integers(-b, b + 1) if on("bond_turns") else 0)
    n2 = N_DEAD + (rng.integers(-b, b + 1) if on("bond_turns") else 0)
    C = C_TANK * (1 + TOL["cap"] * rng.standard_normal()) if on("cap") else C_TANK
    C += C_STRAY + (TOL["stray"] * rng.standard_normal() if on("stray") else 0.0)
    return unit_curve(D, d_out, extra, n1, n2, C)


F_NOM = unit_curve(D_COIL, D_OUT, np.zeros(N - 1), N_DEAD, N_DEAD, C_TANK + C_STRAY)


def invert(f_meas, f_curve):
    """Displacement read off a monotonic calibration curve f_curve(XS)."""
    return np.interp(f_meas, f_curve, XS)


def err_shared(f):
    return invert(f, F_NOM) - XS


def err_one_point(f):
    """Tare at rest: scale the nominal curve to the unit's rest frequency."""
    return invert(f, F_NOM * f[0] / F_NOM[0]) - XS


def err_two_point(f):
    """Rest and full scale known: nominal shape stretched between the two."""
    s_nom = (F_NOM - F_NOM[0]) / (F_NOM[-1] - F_NOM[0])
    return invert(f, f[0] + s_nom * (f[-1] - f[0])) - XS


def lin_var(f, f_rest):
    """Calibration variable proportional to the inductance change: 1 - L/L0."""
    return 1.0 - (f_rest / f) ** 2


def err_poly(f, order, npts, var="L", stage_sigma=0.0, rng=None):
    """Per-unit polynomial x = p(v) fitted at npts evenly spaced stage positions."""
    idx = np.round(np.linspace(0, len(XS) - 1, npts)).astype(int)
    v = lin_var(f, f[0]) if var == "L" else f / f[0] - 1.0
    x_ref = XS[idx] + (stage_sigma * rng.standard_normal(npts) if stage_sigma else 0.0)
    c = np.polyfit(v[idx], x_ref, order)
    return np.polyval(c, v) - XS


def p95max(errs):
    """95th percentile across units of the largest error over the range, um."""
    return np.percentile(np.max(np.abs(errs), axis=1), 95) * 1e6


# ====================================================================== 1. spread
rng = np.random.default_rng(SEED)
units = np.array([draw(rng) for _ in range(UNITS)])
report(f"1. UNIT-TO-UNIT SPREAD  ({UNITS} simulated builds)")
L_rest = 1.0 / ((2 * np.pi * units[:, 0]) ** 2 * (C_TANK + C_STRAY))
mid = len(XS) // 2
sens = np.gradient(units, XS, axis=1)[:, mid] / units[:, mid] * 1e-3 * 1e6      # ppm/mm
for name, v, unit, fmt in (("rest frequency", units[:, 0] / 1e6, "MHz", ".4f"),
                           ("apparent L at rest", L_rest * 1e6, "uH", ".4f"),
                           ("span, f(3 mm)/f(0) - 1", (units[:, -1] / units[:, 0] - 1) * 100, "%", ".2f"),
                           ("sensitivity at 1.5 mm", sens, "ppm/mm", ",.0f")):
    lo, med, hi = np.percentile(v, [2.5, 50, 97.5])
    print(f" {name:<26s} median {med:{fmt}} {unit:<7s} 95 % of units within "
          f"{lo:{fmt}} .. {hi:{fmt}}  (+/-{(hi-lo)/2/med*100:.1f} %)")
ppm_um = np.median(sens) * 1e-3
print(f" 1 um = {ppm_um:.1f} ppm of frequency at mid-range")

# ====================================================================== 2. contributions
report("2. WHICH TOLERANCE IS RESPONSIBLE  (one varied at a time, 400 builds each)")
labels = {"diameter": "coil diameter, 1 %", "wire_od": "wire OD, 1.5 %",
          "rest_gap": "turns not touching, 10 um", "bond_turns": "bonded turns, +/-1 per end",
          "cap": "tank capacitor, 0.5 %", "stray": "stray capacitance, 5 pF"}
contrib = {}
print(f" {'tolerance (1 sigma)':<30s} {'shared curve':>13s} {'1-point tare':>13s} {'2-point':>10s}   um, 95th pct")
for key, lab in labels.items():
    r = np.random.default_rng(SEED + 1)
    u = np.array([draw(r, {key}) for _ in range(400)])
    contrib[key] = [p95max(np.array([fn(f) for f in u])) for fn in (err_shared, err_one_point, err_two_point)]
    print(f" {lab:<30s} {contrib[key][0]:13.1f} {contrib[key][1]:13.1f} {contrib[key][2]:10.2f}")

# ====================================================================== 3. calibration
report("3. HOW MUCH CALIBRATION DOES A UNIT NEED  (worst error over 0-3 mm, um)")
methods = [("shared nominal curve, no per-unit data", np.array([err_shared(f) for f in units])),
           ("1 point: tare at rest, nominal shape", np.array([err_one_point(f) for f in units])),
           ("2 points: rest and full scale, nominal shape", np.array([err_two_point(f) for f in units]))]
poly_rows = []
for order, npts in ((1, 2), (2, 3), (3, 4), (3, 7), (4, 5), (4, 9), (5, 11)):
    for var in ("L", "f"):
        e = np.array([err_poly(f, order, npts, var) for f in units])
        poly_rows.append((order, npts, var, np.median(np.max(np.abs(e), axis=1)) * 1e6, p95max(e)))
print(f" {'method':<48s} {'median unit':>12s} {'95th pct unit':>14s}")
for name, e in methods:
    print(f" {name:<48s} {np.median(np.max(np.abs(e), axis=1))*1e6:12.1f} {p95max(e):14.1f}")
for order, npts, var, med, p95 in poly_rows:
    vn = "in 1-(f0/f)^2" if var == "L" else "in f/f0-1"
    print(f" {'polynomial order '+str(order)+', '+str(npts)+' points, '+vn:<48s} {med:12.3f} {p95:14.3f}")

print("\n effect of a +/-2 um (1 sigma) error in the stage positions used for calibration")
r = np.random.default_rng(SEED + 2)
sub = units[:400]
for order, npts in ((3, 4), (3, 7), (3, 13), (4, 9), (4, 25)):
    e = np.array([err_poly(f, order, npts, "L", 2e-6, r) for f in sub])
    print(f"   order {order}, {npts:2d} points: worst error {p95max(e):5.2f} um (95th pct), "
          f"rms over range {np.sqrt(np.mean(e**2))*1e6:.2f} um")

# ====================================================================== 4. reference coil
report("4. WHAT A REFERENCE COIL LEAVES UNCANCELLED")


def dlnL_dlnD(x, h=1e-4):
    z = hc.turn_positions(N, N_DEAD, D_OUT, N * D_OUT + x)
    return (hc.inductance(z, D_COIL * (1 + h), A_WIRE) / hc.inductance(z, D_COIL, A_WIRE) - 1) / h


CTE_CU = 17e-6
print(" residual drift of the sensor/reference frequency ratio, as displacement")
print(f"   {'source':<58s} {'ppm/degC':>9s} {'um/degC':>9s}")
for x in (0.0, 1.5e-3, 3.0e-3):
    d = 0.5 * (dlnL_dlnD(x) - dlnL_dlnD(0.0)) * CTE_CU * 1e6
    print(f"   {'coil growth, sensor at '+format(x*1e3,'.1f')+' mm vs reference at rest':<58s} "
          f"{d:9.2f} {abs(d)/ppm_um:9.3f}")
for lab, mism in (("capacitor tempco mismatch, same reel (assumed 5 ppm/degC)", 5.0),
                  ("capacitor tempco mismatch, different lots (up to 30)", 30.0)):
    print(f"   {lab:<58s} {mism/2:9.2f} {mism/2/ppm_um:9.3f}")
tc_abs = 0.5 * 30 + 0.5 * dlnL_dlnD(1.5e-3) * CTE_CU * 1e6
print(f"\n if sensor and reference sit at different temperatures, the uncancelled part is "
      f"{tc_abs:.0f} ppm = {tc_abs/ppm_um:.2f} um per degC of difference")
print(f" microcontroller clock error cancels exactly in the ratio")

# ====================================================================== figures
fig, ax = plt.subplots(figsize=(7.2, 3.6))
names = ["shared curve\nno calibration", "1 point\n(tare at rest)", "2 points\n(rest + full scale)",
         "3 points\nquadratic in f", "4 points\ncubic in f"]
pick = {(2, 3, "f"), (3, 4, "f")}
vals = [p95max(e) for _, e in methods] + [p for o, n, v, m, p in poly_rows if (o, n, v) in pick]
ax.bar(range(len(vals)), vals, width=0.62, color=S1)
ax.set_yscale("log")
ax.set_ylim(0.01, max(vals) * 4)
for i, v in enumerate(vals):
    lab = f"{v:,.0f} µm" if v >= 10 else (f"{v:.1f} µm" if v >= 0.1 else f"{v:.2f} µm")
    ax.text(i, v * 1.25, lab, ha="center", fontsize=9.5, color=SECOND)
ax.axhline(1.0, color=MUTED, lw=0.9, ls=(0, (4, 3)))
ax.text(len(vals) - 0.55, 1.12, "1 µm", ha="right", fontsize=8.5, color=MUTED)
ax.set_xticks(range(len(vals)), names, fontsize=8.5)
ax.set_ylabel("worst error over 0–3 mm (µm)\n95th-percentile unit")
ax.set_title("Units are not interchangeable; three stage points per unit reach a micron")
ax.grid(axis="x", visible=False)
save(fig, "calibration-methods.png")

fig, ax = plt.subplots(figsize=(7.2, 3.4))
keys = sorted(contrib, key=lambda k: contrib[k][1])
y = np.arange(len(keys))
FLOOR = 0.1
ax.barh(y + 0.19, [max(contrib[k][0], FLOOR) for k in keys], height=0.36, color=S2, label="shared curve")
ax.barh(y - 0.19, [max(contrib[k][1], FLOOR) for k in keys], height=0.36, color=S1, label="after 1-point tare")
for yi, k in zip(y, keys):
    for off, v in ((0.19, contrib[k][0]), (-0.19, contrib[k][1])):
        ax.text(max(v, FLOOR) * 1.15, yi + off, f"{v:,.0f}" if v >= 1 else "0", va="center",
                fontsize=8.5, color=SECOND)
ax.set_xlim(FLOOR, max(c[0] for c in contrib.values()) * 3)
ax.set_yticks(y, [labels[k] for k in keys])
ax.set_xscale("log")
ax.set_xlabel("worst error over 0–3 mm (µm), 95th-percentile unit")
ax.set_title("A tare removes capacitor error; coil geometry errors remain")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=9)
ax.grid(axis="y", visible=False)
save(fig, "tolerance-contributions.png")
print("\nfigures written to docs/figures")
