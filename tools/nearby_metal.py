# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Tico Hannan
"""What does metal near the coil do to the reading?

A conductor in the coil's field carries eddy currents that oppose the field, so the
coil's inductance falls and its losses rise.  Three geometries:

  side plate   coil lying alongside a metal surface (axis parallel to the surface)
  end plate    metal surface facing the end of the coil (axis normal to the surface)
  tube / rod   coaxial metal around the coil (shield, metal guide) or on its axis (screw)

Two models, cross-checked against each other in section 0:

  image    Thick plates.  The plate is replaced by a mirror-image coil; finite
           conductivity and permeability push the image back by the complex depth
           mu_r * delta * (1 - j), delta = skin depth.  Valid when mu_r*delta is small
           next to the coil-to-plate distance.
  rings    Tubes, rods and plates.  The metal is cut into shorted coaxial rings coupled
           to every turn; non-magnetic metals only.

A fixed piece of metal changes the calibration curve but not the repeatability, so
calibrating in place absorbs it.  What cannot be calibrated out is reported for each
case: the change when the metal moves relative to the coil, the drift with
temperature, and the loss of Q.

Run:  python tools/nearby_metal.py
"""
import numpy as np
import matplotlib.pyplot as plt
import helix_core as hc
from plotstyle import S1, S2, S3, S4, MUTED, SECOND, save, report

# ------------------------------------------------------------------ DESIGN
AWG = 30
N = 32
N_DEAD = 2
D_COIL = 5.0e-3
C_TANK = 4715e-12
X_MAX = 3.0e-3
Q_FREE = 37.0           # coil Q with no metal nearby (from the notebook model, mid-range)

# resistivity ohm*m at 20 degC, relative permeability, resistivity tempco 1/degC
METALS = {
    "aluminium 6061":      (4.0e-8, 1.0, 0.0039),
    "brass":               (6.4e-8, 1.0, 0.0015),
    "stainless 304":       (7.2e-7, 1.0, 0.0010),
    "mild steel, mu_r 100": (1.6e-7, 100.0, 0.0050),
}
# ------------------------------------------------------------------

D_WIRE = float(hc.awg_to_mm(AWG)) * 1e-3
A_WIRE = 0.5 * D_WIRE
D_OUT = hc.enamel_od_mm(AWG) * 1e-3
R_COIL = 0.5 * D_COIL
NPHI = 72
_PHI = (np.arange(NPHI) + 0.5) * 2 * np.pi / NPHI


def coil_z(x):
    return hc.turn_positions(N, N_DEAD, D_OUT, N * D_OUT + x)


def L_free(x):
    return hc.inductance(coil_z(x), D_COIL, A_WIRE, pitch_correction=False)


def skin_depth(rho, mu_r, f):
    return np.sqrt(rho / (np.pi * f * hc.MU0 * mu_r))


def mutual_neumann(R1, R2, dz, dlat):
    """Mutual inductance of two circular loops with parallel axes, by numerical
    Neumann integral.  dz = axial offset, dlat = lateral offset of the axes; either
    may be complex (complex-image method).  dz and dlat broadcast together."""
    dz = np.asarray(dz, dtype=complex)[..., None, None]
    dlat = np.asarray(dlat, dtype=complex)[..., None, None]
    p1, p2 = _PHI[:, None], _PHI[None, :]
    dx = dlat + R2 * np.cos(p2) - R1 * np.cos(p1)
    dy = R2 * np.sin(p2) - R1 * np.sin(p1)
    r = np.sqrt(dx * dx + dy * dy + dz * dz)
    integrand = np.cos(p1 - p2) / r
    return hc.MU0 / (4 * np.pi) * R1 * R2 * integrand.sum(axis=(-1, -2)) * (2 * np.pi / NPHI) ** 2


# ---------------------------------------------------------------- image models
def image_side(x, h, rho, mu_r, f):
    """Coil axis parallel to a thick plate, axis-to-surface distance h.
    Returns (dL, dR): change in inductance and added series resistance."""
    z = coil_z(x)
    s = 2 * h + mu_r * skin_depth(rho, mu_r, f) * (1 - 1j)
    dzs = np.abs(z[:, None] - z[None, :])
    uniq, inv = np.unique(np.round(dzs, 9), return_inverse=True)
    M = mutual_neumann(R_COIL, R_COIL, uniq, s)[inv].sum()
    return M.real, -2 * np.pi * f * M.imag


def image_end(x, g, rho, mu_r, f):
    """Thick plate facing the coil end, g from the centre of the last turn."""
    z = coil_z(x)
    d = (z[:, None] + z[None, :]) + 2 * g + mu_r * skin_depth(rho, mu_r, f) * (1 - 1j)
    uniq, inv = np.unique(np.round(d, 9), return_inverse=True)
    M = -mutual_neumann(R_COIL, R_COIL, uniq, 0.0)[inv].sum()
    return M.real, -2 * np.pi * f * M.imag


# ---------------------------------------------------------------- ring model
def rings_solve(x, r_ring, z_ring, width, thick, rho, f):
    """Shorted coaxial rings (radius, axial position, strip width, metal thickness)
    coupled to the coil.  Non-magnetic.  Returns (dL, dR)."""
    w = 2 * np.pi * f
    z = coil_z(x)
    delta = skin_depth(rho, 1.0, f)
    t_eff = np.minimum(thick, delta)
    R = rho * 2 * np.pi * r_ring / (width * t_eff)
    X_int = np.where(thick > delta, R, 0.0)                  # surface-impedance reactance
    gmd = 0.2235 * (width + t_eff)
    Lrr = hc.mutual_coaxial(r_ring[:, None], r_ring[None, :], z_ring[:, None] - z_ring[None, :])
    Lrr[np.diag_indices_from(Lrr)] = hc.MU0 * r_ring * (np.log(8 * r_ring / gmd) - 2.0)
    Z = np.diag(R + 1j * X_int) + 1j * w * Lrr
    m = hc.mutual_coaxial(R_COIL, r_ring[None, :], z[:, None] - z_ring[None, :]).sum(axis=0)
    dZ = w * w * (m @ np.linalg.solve(Z, m))
    return dZ.imag / w, dZ.real


def rings_end_plate(x, g, rho, f, r_max=30e-3, w=0.2e-3, thick=3e-3):
    r = np.arange(w, r_max, w)
    return rings_solve(x, r, np.full_like(r, -g), w, thick, rho, f)


def rings_tube(x, r_tube, rho, f, margin=10e-3, w=0.25e-3, thick=1e-3, z0=None, z1=None):
    z = coil_z(X_MAX)
    zr = np.arange((z0 if z0 is not None else -margin), (z1 if z1 is not None else z[-1] + margin), w)
    return rings_solve(x, np.full_like(zr, r_tube), zr, w, thick, rho, f)


# ---------------------------------------------------------------- reporting helpers
F_MID = hc.resonant_f(L_free(1.5e-3), C_TANK)
DLDX = {x: (L_free(x + 1e-6) - L_free(x - 1e-6)) / 2e-6 for x in (1.5e-3,)}
DLDX0 = DLDX[1.5e-3]
R_FREE = 2 * np.pi * F_MID * L_free(1.5e-3) / Q_FREE


def um(dL):
    """Inductance change expressed as apparent displacement at mid-range, um."""
    return dL / DLDX0 * 1e6


def q_with(dL, dR, x=1.5e-3):
    return 2 * np.pi * F_MID * (L_free(x) + dL) / (R_FREE + dR)


def summarise(model, dist, rho, mu_r, alpha, x=1.5e-3):
    """offset um, um per 0.1 mm of distance change, um per degC, Q."""
    dL, dR = model(x, dist, rho, mu_r, F_MID)
    dLg, _ = model(x, dist + 0.1e-3, rho, mu_r, F_MID)
    dLt, _ = model(x, dist, rho * (1 + alpha * 10.0), mu_r, F_MID)
    return um(dL), um(dLg) - um(dL), (um(dLt) - um(dL)) / 10.0, q_with(dL, dR, x)


# ====================================================================== 0. validation
report("0. MODEL CHECKS")
ref = hc.mutual_coaxial(R_COIL, R_COIL, np.array([0.3e-3, 2e-3, 10e-3]))
num = mutual_neumann(R_COIL, R_COIL, np.array([0.3e-3, 2e-3, 10e-3]), 0.0).real
print(f" Neumann integral vs Maxwell formula, coaxial loops: worst difference "
      f"{np.max(np.abs(num/ref-1))*100:.3f} %")
print(f" ring frequency {F_MID/1e6:.3f} MHz; skin depth: " + ", ".join(
    f"{k.split(',')[0]} {skin_depth(r, m, F_MID)*1e6:.0f} um" for k, (r, m, a) in METALS.items()))
print(" end plate, aluminium: image model vs ring model")
rho_al = METALS["aluminium 6061"][0]
for g in (2e-3, 5e-3, 10e-3):
    a, ar = image_end(1.5e-3, g, rho_al, 1.0, F_MID)
    b, br = rings_end_plate(1.5e-3, g, rho_al, F_MID)
    print(f"   gap {g*1e3:4.1f} mm: dL/L image {a/L_free(1.5e-3)*100:+.3f} %, rings "
          f"{b/L_free(1.5e-3)*100:+.3f} %   added R image {ar*1e3:.2f} mohm, rings {br*1e3:.2f} mohm")

# ====================================================================== 1. side plate
hdr = (f" {'metal':<22s} {'dist mm':>7s} {'dL/L %':>8s} {'offset um':>10s} "
       f"{'um per 0.1 mm':>14s} {'um/degC':>9s} {'Q':>6s}")
report("1. SIDE PLATE  coil alongside a thick metal surface (distance = coil axis to surface)")
print(f" coil radius {R_COIL*1e3:.1f} mm, so 3 mm means 0.5 mm of clearance; Q with no metal = {Q_FREE:.0f}")
print(hdr)
side = {}
for name, (rho, mu_r, alpha) in METALS.items():
    for h in (3e-3, 5e-3, 7.5e-3, 10e-3, 15e-3, 20e-3):
        off, per01, perC, Q = summarise(image_side, h, rho, mu_r, alpha)
        side[(name, h)] = (off, per01, perC, Q)
        print(f" {name:<22s} {h*1e3:7.1f} {off*DLDX0/L_free(1.5e-3)*1e-6*100:8.3f} {off:10.1f} "
              f"{per01:14.2f} {perC:9.3f} {Q:6.1f}")

# ====================================================================== 2. end plate
report("2. END PLATE  thick metal facing the fixed end (distance = last turn to surface)")
print(hdr)
endp = {}
for name, (rho, mu_r, alpha) in METALS.items():
    for g in (1e-3, 2e-3, 3e-3, 5e-3, 7.5e-3, 10e-3):
        off, per01, perC, Q = summarise(image_end, g, rho, mu_r, alpha)
        endp[(name, g)] = (off, per01, perC, Q)
        print(f" {name:<22s} {g*1e3:7.1f} {off*DLDX0/L_free(1.5e-3)*1e-6*100:8.3f} {off:10.1f} "
              f"{per01:14.2f} {perC:9.3f} {Q:6.1f}")

# ====================================================================== 2b. steel
report("2b. MILD STEEL: HOW MUCH DEPENDS ON ITS PERMEABILITY  side plate, mid-range")
print(" permeability of steel at MHz is poorly known and changes with stress and temperature")
print(f" {'mu_r':>6s} {'dist mm':>8s} {'offset um':>10s} {'um per 1 % change in mu_r':>27s} {'Q':>6s}")
rho_fe, _, alpha_fe = METALS["mild steel, mu_r 100"]
for h in (5e-3, 10e-3):
    for mu in (50.0, 100.0, 200.0):
        dL, dR = image_side(1.5e-3, h, rho_fe, mu, F_MID)
        dLm, _ = image_side(1.5e-3, h, rho_fe, mu * 1.01, F_MID)
        print(f" {mu:6.0f} {h*1e3:8.1f} {um(dL):10.1f} {um(dLm)-um(dL):27.3f} {q_with(dL, dR):6.1f}")

# ====================================================================== 3. coaxial metal
report("3. COAXIAL METAL  shorted-ring model, non-magnetic metals")
print(f" {'case':<52s} {'dL/L %':>8s} {'sens. change %':>15s} {'um/degC':>9s} {'Q':>6s}")


def ring_case(label, fn, rho, alpha):
    dL, dR = fn(1.5e-3, rho)
    dLp, _ = fn(1.5e-3 + 1e-6, rho)
    dLm, _ = fn(1.5e-3 - 1e-6, rho)
    dLt, _ = fn(1.5e-3, rho * (1 + alpha * 10))
    sens = ((dLp - dLm) / 2e-6) / DLDX0 * 100
    print(f" {label:<52s} {dL/L_free(1.5e-3)*100:8.2f} {sens:15.1f} {(um(dLt)-um(dL))/10:9.3f} "
          f"{q_with(dL, dR):6.1f}")
    return dL, dR


rho, _, alpha = METALS["aluminium 6061"]
tube_rows = []
for rt in (4e-3, 5e-3, 7.5e-3, 10e-3, 15e-3):
    dL, dR = ring_case(f"aluminium tube, inner diameter {2*rt*1e3:.0f} mm, full length",
                       lambda x, r, rt=rt: rings_tube(x, rt, r, F_MID), rho, alpha)
    tube_rows.append((2 * rt * 1e3, dL / L_free(1.5e-3) * 100, q_with(dL, dR)))
rho_ss, _, alpha_ss = METALS["stainless 304"]
ring_case("stainless 304 tube, inner diameter 10 mm, 0.5 mm wall",
          lambda x, r: rings_tube(x, 5e-3, r, F_MID, thick=0.5e-3), rho_ss, alpha_ss)
rho_br, _, alpha_br = METALS["brass"]
for gap in (1e-3, 3e-3, 6e-3):
    ring_case(f"brass M3 screw on axis, tip {gap*1e3:.0f} mm beyond the fixed end",
              lambda x, r, gap=gap: rings_tube(x, 1.5e-3, r, F_MID, z0=-gap - 10e-3, z1=-gap, thick=1.5e-3),
              rho_br, alpha_br)
ring_case("brass M3 screw on axis, 3 mm inside the fixed end",
          lambda x, r: rings_tube(x, 1.5e-3, r, F_MID, z0=-10e-3, z1=3e-3, thick=1.5e-3), rho_br, alpha_br)
for gap in (1e-3, 3e-3):
    ring_case(f"brass washer (3.2/7 mm), {gap*1e3:.0f} mm beyond the fixed end",
              lambda x, r, gap=gap: rings_solve(x, np.arange(1.7e-3, 3.5e-3, 0.2e-3),
                                                np.full(9, -gap), 0.2e-3, 0.5e-3, r, F_MID),
              rho_br, alpha_br)

# ====================================================================== 4. keep-out
report("4. KEEP-OUT DISTANCES  from the tables above, mid-range")


def first_ok(table, name, col, limit):
    ds = sorted(d for (n, d) in table if n == name)
    for d in ds:
        if abs(table[(name, d)][col]) <= limit:
            return f"{d*1e3:.1f} mm"
    return f"> {ds[-1]*1e3:.0f} mm"


print(f" {'':<22s} {'drift < 0.1 um/degC':>22s} {'< 1 um per 0.1 mm shift':>26s} {'Q loss < 10 %':>16s}")
for tab, lab in ((side, "side plate"), (endp, "end plate")):
    print(f" {lab}")
    for name in METALS:
        ds = sorted(d for (n, d) in tab if n == name)
        qok = next((f"{d*1e3:.1f} mm" for d in ds if tab[(name, d)][3] >= 0.9 * Q_FREE), f"> {ds[-1]*1e3:.0f} mm")
        print(f"   {name:<20s} {first_ok(tab, name, 2, 0.1):>22s} {first_ok(tab, name, 1, 1.0):>26s} {qok:>16s}")

# ====================================================================== figures
cols = dict(zip(METALS, (S1, S3, S4, S2)))
fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.7), sharey=True)
for ax, model, d, ttl, xl in (
        (axes[0], image_side, np.linspace(3e-3, 20e-3, 30), "Side plate", "coil axis to metal surface (mm)"),
        (axes[1], image_end, np.linspace(1e-3, 15e-3, 30), "End plate", "last turn to metal surface (mm)")):
    for name, (rho, mu_r, alpha) in METALS.items():
        y = [abs(summarise(model, di, rho, mu_r, alpha)[2]) for di in d]
        ax.plot(d * 1e3, y, color=cols[name], label=name)
    ax.axhline(0.1, color=MUTED, lw=0.9, ls=(0, (4, 3)))
    ax.set_yscale("log"); ax.set_xlabel(xl); ax.set_title(ttl)
axes[0].set_ylabel("temperature drift caused by the metal\n(µm of apparent displacement per °C)")
axes[0].text(19.8, 0.115, "0.1 µm/°C", ha="right", fontsize=8.5, color=MUTED)
axes[1].legend(fontsize=9, loc="lower left")
fig.suptitle("Magnetic steel near the coil drifts with temperature; non-magnetic metals barely do",
             x=0.06, ha="left", fontweight="bold", fontsize=11)
fig.subplots_adjust(top=0.84, wspace=0.08)
save(fig, "metal-drift.png")

fig, ax = plt.subplots(figsize=(7.2, 3.4))
dia = [r[0] for r in tube_rows]
ax.plot(dia, [r[2] for r in tube_rows], color=S1, marker="o", ms=6)
for d_, dl, q in tube_rows:
    ax.annotate(f"L {dl:+.0f} %", (d_, q), textcoords="offset points", xytext=(9, -13), ha="left",
                fontsize=8.5, color=SECOND)
ax.axhline(Q_FREE, color=MUTED, lw=0.9, ls=(0, (4, 3)))
ax.text(dia[0], Q_FREE + 0.8, "no tube", ha="left", fontsize=8.5, color=MUTED)
ax.set_ylim(0, Q_FREE * 1.15)
ax.set_xlabel("inner diameter of aluminium tube around a 5 mm coil (mm)")
ax.set_ylabel("Q of the tank")
ax.set_title("A closed metal tube close around the coil costs inductance and Q")
save(fig, "metal-tube.png")
print("\nfigures written to docs/figures")
