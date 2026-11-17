# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Tico Hannan
"""How much does a stretch-coil reading change when the stretch is not uniform?

The sensor reads inductance, which depends on where every turn sits, not just on the
end-to-end length.  This script asks four questions for one coil design:

  1. Which gaps matter?        dL/d(gap) for each turn-to-turn gap.
  2. Same length, different distribution: how large is the apparent displacement?
  3. Friction in a guide tube: how much hysteresis over an extend/retract cycle?
  4. Deliberate series segments: bonded ends, two diameters, pre-opened pitch.

Run:  python tools/nonuniform_stretch.py            (prints tables, writes figures)
Edit the DESIGN block to try another coil.
"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import helix_core as hc

# ------------------------------------------------------------------ DESIGN
AWG = 30
N = 32                  # total turns
N_DEAD = 2              # bonded turns per end
D_COIL = 5.0e-3         # mean coil diameter, m
C_TANK = 4715e-12       # 4700 pF + 15 pF stray, F
X_MAX = 3.0e-3          # full-scale displacement, m
SEED = 7
# ------------------------------------------------------------------

D_WIRE = float(hc.awg_to_mm(AWG)) * 1e-3
A_WIRE = 0.5 * D_WIRE
D_OUT = hc.enamel_od_mm(AWG) * 1e-3
L0 = N * D_OUT
FIG = pathlib.Path(__file__).resolve().parent.parent / "docs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#0b0b0b", "#898781", "#e1e0d9"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
plt.rcParams.update({
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#52514e", "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "lines.linewidth": 2.0, "legend.frameon": False,
})


def L_of(z, D=D_COIL):
    return hc.inductance(z, D, A_WIRE)


def uniform_z(x, n_dead=N_DEAD, n=N):
    return hc.turn_positions(n, n_dead, D_OUT, n * D_OUT + x)


def L_uniform(x, n_dead=N_DEAD):
    return L_of(uniform_z(x, n_dead))


def dLdx(x, n_dead=N_DEAD, h=1e-6):
    return (L_uniform(x + h, n_dead) - L_uniform(x - h, n_dead)) / (2 * h)


def free_gap_slice(n_dead=N_DEAD, n=N):
    """Indices of the gaps that can open (everything not inside a bond)."""
    lo = max(n_dead - 1, 0)
    hi = (n - 1) - max(n_dead - 1, 0)
    return slice(lo, hi)


def z_from_free_ext(ext, n_dead=N_DEAD, n=N):
    """Turn positions when the free gaps are opened by the amounts in ext (m)."""
    gaps = np.full(n - 1, D_OUT)
    gaps[free_gap_slice(n_dead, n)] += ext
    return hc.positions_from_gaps(gaps)


N_FREE_GAPS = len(np.arange(N - 1)[free_gap_slice()])


def report(title):
    print("\n" + "=" * 78 + "\n " + title + "\n" + "=" * 78)


# ====================================================================== baseline
report("BASELINE  uniform stretch of the free turns")
xs = np.linspace(0, X_MAX, 61)
Lu = np.array([L_uniform(x) for x in xs])
fu = hc.resonant_f(Lu, C_TANK)
print(f" {N} turns AWG {AWG} (bare {D_WIRE*1e3:.3f} mm, OD {D_OUT*1e3:.3f} mm), "
      f"D {D_COIL*1e3:.1f} mm, {N_DEAD} bonded turns per end, close-wound {L0*1e3:.2f} mm")
print(f" {'x mm':>6} {'L uH':>8} {'f MHz':>8} {'dL/dx %/mm':>11} {'df/dx ppm/mm':>13}")
for x in (0.0, 0.5e-3, 1.0e-3, 1.5e-3, 2.0e-3, 3.0e-3):
    L = L_uniform(x)
    s = dLdx(max(x, 1e-6)) / L
    print(f" {x*1e3:6.1f} {L*1e6:8.4f} {hc.resonant_f(L, C_TANK)/1e6:8.4f} "
          f"{s*1e-3*100:11.2f} {-0.5*s*1e-3*1e6:13,.0f}")
fit = np.polyfit(xs, fu, 1)
nonlin = np.max(np.abs(fu - np.polyval(fit, xs))) / (fu[-1] - fu[0])
print(f" f(x) departs from a straight line by {100*nonlin:.2f} % of full scale "
      f"({nonlin*X_MAX*1e6:.0f} um) -- use a polynomial calibration, not a slope")
k_turn = hc.turn_stiffness(D_COIL, D_WIRE)
F3 = k_turn * X_MAX / N_FREE_GAPS
print(f" spring: {k_turn:.0f} N/m per turn, {N_FREE_GAPS} free gaps -> "
      f"{F3*1e3:.1f} mN and {hc.spring_stress(F3, D_COIL, D_WIRE)/1e6:.1f} MPa shear at "
      f"{X_MAX*1e3:.0f} mm")

# ====================================================================== 1. influence
report("1. WHICH GAPS MATTER  dL/d(gap) at x = 1.5 mm")
x_ref = 1.5e-3
z_ref = uniform_z(x_ref)
gaps_ref = np.diff(z_ref)
h = 1e-7
infl = np.empty(N - 1)
for j in range(N - 1):
    g = gaps_ref.copy(); g[j] += h
    gm = gaps_ref.copy(); g_m = gm; g_m[j] -= h
    infl[j] = (L_of(hc.positions_from_gaps(g)) - L_of(hc.positions_from_gaps(g_m))) / (2 * h)
mid = infl[(N - 1) // 2]
print(f" centre gap: {mid*1e6*1e-3:.4f} uH/mm      end gap: {infl[0]*1e6*1e-3:.4f} uH/mm"
      f"      ratio {mid/infl[0]:.1f}x")
print(f" first free gap: {infl[free_gap_slice()][0]/mid*100:.0f} % of centre;  "
      f"quarter-point gap: {infl[(N-1)//4]/mid*100:.0f} % of centre")

fig, ax = plt.subplots(figsize=(7.2, 3.6))
jj = np.arange(1, N)
fs = free_gap_slice()
ax.bar(jj, -infl * 1e3, width=0.72, color="#c3c2b7", label="gap inside a bond (cannot open)")
ax.bar(jj[fs], -infl[fs] * 1e3, width=0.72, color=S1, label="free gap")
ax.set_xlabel("gap number, fixed end to moving end")
ax.set_ylabel("inductance lost per mm of opening (µH/mm)")
ax.set_title("A free gap at the centre is worth twice a free gap at the end")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=9)
ax.grid(axis="x", visible=False)
fig.savefig(FIG / "gap-influence.png", dpi=160, bbox_inches="tight"); plt.close(fig)

# ====================================================================== 2. redistribution
report("2. SAME LENGTH, DIFFERENT DISTRIBUTION  apparent displacement error")
u = np.linspace(-1, 1, N_FREE_GAPS)
rng = np.random.default_rng(SEED)


def err_um(ext, x):
    """Apparent displacement error (um) of a non-uniform state against the uniform
    calibration curve.  Negative = sensor reads short."""
    return (L_of(z_from_free_ext(ext)) - L_uniform(x)) / dLdx(x) * 1e6


def cases(x):
    e = x / N_FREE_GAPS
    out = {}
    for g in (0.1, 0.3, 1.0):
        out[f"linear gradient, +/-{int(g*100)} % end to end"] = e * (1 + g * u)
    half = np.zeros(N_FREE_GAPS); half[N_FREE_GAPS // 2:] = x / (N_FREE_GAPS - N_FREE_GAPS // 2)
    out["only the moving-end half opens"] = half
    q = N_FREE_GAPS // 4
    cen = np.zeros(N_FREE_GAPS); cen[q:N_FREE_GAPS - q] = x / (N_FREE_GAPS - 2 * q)
    out["only the centre half opens"] = cen
    ends = np.zeros(N_FREE_GAPS); ends[:q] = ends[-q:] = x / (2 * q)
    out["only the two end quarters open"] = ends
    one = np.zeros(N_FREE_GAPS); one[N_FREE_GAPS // 2] = x
    out["one centre gap takes everything"] = one
    return out


for x in (0.5e-3, 1.5e-3, 3.0e-3):
    print(f"\n x = {x*1e3:.1f} mm   (uniform gap opening {x/N_FREE_GAPS*1e6:.0f} um per gap)")
    for name, ext in cases(x).items():
        print(f"   {name:<44s} {err_um(ext, x):+9.1f} um  ({err_um(ext, x)/(x*1e6)*100:+6.1f} % of x)")
    for sig in (0.1, 0.3):
        errs = []
        for _ in range(400):
            ext = np.clip(1 + sig * rng.standard_normal(N_FREE_GAPS), 0, None)
            ext *= x / ext.sum()
            errs.append(err_um(ext, x))
        print(f"   {'random, '+str(int(sig*100))+' % rms per gap (400 trials)':<44s} "
              f"{np.mean(errs):+9.2f} um mean, {np.std(errs):.2f} um rms scatter")

# ====================================================================== 3. friction
report("3. FRICTION IN THE GUIDE TUBE  extend 0 -> 3 mm -> 0, quasi-static")
W_TURN = hc.turn_weight(D_COIL, D_WIRE)
FREE = np.arange(N_DEAD, N - N_DEAD)          # indices of turns that can slide
print(f" one turn weighs {W_TURN*1e6:.0f} uN; friction per turn = mu x normal load")


def relax(z, fric):
    """Move each free turn until spring imbalance is within its friction limit."""
    k = k_turn
    for sweep in range(20000):
        moved = 0.0
        order = FREE if sweep % 2 == 0 else FREE[::-1]
        for i in order:
            net = k * (z[i + 1] + z[i - 1] - 2 * z[i])
            f = fric[i]
            if abs(net) > f:
                dz = (net - np.sign(net) * f) / (2 * k)
                new = min(max(z[i] + dz, z[i - 1] + D_OUT), z[i + 1] - D_OUT)
                moved = max(moved, abs(new - z[i]))
                z[i] = new
        if moved < 2e-11:
            break
    return z


def cycle(fric, n_step=40):
    z = np.arange(N) * D_OUT
    path = np.concatenate([np.linspace(0, X_MAX, n_step + 1), np.linspace(X_MAX, 0, n_step + 1)[1:]])
    Ls = []
    for x in path:
        z[N - N_DEAD:] = (N - N_DEAD + np.arange(N_DEAD)) * D_OUT + x
        z = relax(z, fric)
        Ls.append(L_of(z))
    return path, np.array(Ls)


cal_x = np.linspace(-0.2e-3, X_MAX + 0.2e-3, 400)
cal_L = np.array([L_uniform(max(x, 0)) if x >= 0 else L_uniform(0) + x * dLdx(1e-6) for x in cal_x])


def read_x(L):
    return np.interp(-L, -cal_L, cal_x)


fr_cases = [
    ("uniform, mu*load = 0.1 turn weights (PTFE, horizontal)", np.full(N, 0.1 * W_TURN)),
    ("uniform, mu*load = 0.3 turn weights (PP, horizontal)", np.full(N, 0.3 * W_TURN)),
    ("uniform, mu*load = 3 turn weights (bowed / side-loaded)", np.full(N, 3.0 * W_TURN)),
]
snag = np.full(N, 0.1 * W_TURN); snag[N_DEAD + len(FREE) // 4] = 2.0e-3
fr_cases.append(("PTFE + one turn snagged at the quarter point (2 mN)", snag))
snagc = np.full(N, 0.1 * W_TURN); snagc[N // 2] = 2.0e-3
fr_cases.append(("PTFE + one turn snagged at the centre (2 mN)", snagc))

fig, ax = plt.subplots(figsize=(7.2, 3.8))
cols = [S1, S2, S3, S4, "#e87ba4"]
short = ["PTFE, horizontal", "PP, horizontal", "side-loaded (3 turn weights)",
         "snag at quarter point", "snag at centre"]
for (name, fric), col, lab in zip(fr_cases, cols, short):
    path, Ls = cycle(fric)
    n = len(path) // 2
    err = (read_x(Ls) - path) * 1e6
    up, dn = err[:n + 1], err[n:][::-1]
    hyst = dn - up
    print(f" {name:<58s} max |error| {np.max(np.abs(err)):6.2f} um   "
          f"max up/down difference {np.max(np.abs(hyst[1:-1])):6.2f} um")
    ax.plot(path[:n + 1] * 1e3, up, color=col, label=lab)
    ax.plot(path[:n + 1] * 1e3, dn, color=col, ls=(0, (4, 2)), lw=1.4)
ax.set_xlabel("true displacement (mm)")
ax.set_ylabel("reading error (µm)")
ax.set_title("Guide-tube friction: solid = extending, dashed = retracting")
ax.axhline(0, color="#c3c2b7", lw=0.8)
ax.legend(fontsize=8.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2))
fig.savefig(FIG / "friction-hysteresis.png", dpi=160, bbox_inches="tight"); plt.close(fig)

# ====================================================================== 4. series designs
report("4. DELIBERATE SERIES SEGMENTS  sensitivity at x = 1.5 mm, full-scale stress")
print(f" {'design':<50s} {'L0 uH':>7} {'df/dx ppm/mm':>13} {'F mN':>6} {'tau MPa':>8}")


def sens_generic(zfun, x=1.5e-3, h=1e-6):
    Lp, Lm, Lc = zfun(x + h), zfun(x - h), zfun(x)
    return -0.5 * (Lp - Lm) / (2 * h) / Lc * 1e-3 * 1e6      # ppm of f per mm


rows = []
for nd in (0, 2, 4, 6, 8, 10, 12):
    ng = len(np.arange(N - 1)[free_gap_slice(nd)])
    F = k_turn * X_MAX / ng
    s = sens_generic(lambda x, nd=nd: L_uniform(x, nd))
    rows.append((nd, s, hc.spring_stress(F, D_COIL, D_WIRE) / 1e6))
    print(f" {'32 turns, '+str(nd)+' bonded turns per end':<50s} {L_uniform(0, nd)*1e6:7.3f} "
          f"{s:13,.0f} {F*1e3:6.1f} {rows[-1][2]:8.1f}")


def two_diameter(x, n_end=8, D_end=4.0e-3):
    """Stiff small-diameter end sections, soft full-diameter centre, in series."""
    Dv = np.full(N, D_COIL); Dv[:n_end] = D_end; Dv[-n_end:] = D_end
    comp = np.empty(N - 1)                       # compliance of each gap
    for j in range(N - 1):
        comp[j] = 1.0 / hc.turn_stiffness(0.5 * (Dv[j] + Dv[j + 1]), D_WIRE)
    comp[:max(N_DEAD - 1, 0)] = 0; comp[N - 1 - max(N_DEAD - 1, 0):] = 0
    gaps = D_OUT + x * comp / comp.sum()
    return hc.inductance(hc.positions_from_gaps(gaps), Dv, A_WIRE), x / comp.sum()


s = sens_generic(lambda x: two_diameter(x)[0])
F = two_diameter(X_MAX)[1]
print(f" {'8+16+8 turns, ends 4 mm dia, centre 5 mm, 2 bonded':<50s} {two_diameter(0)[0]*1e6:7.3f} "
      f"{s:13,.0f} {F*1e3:6.1f} {hc.spring_stress(F, D_COIL, D_WIRE)/1e6:8.1f}")


def preopened(x, n_open=14, pitch_mult=2.0, where="centre"):
    """Same wire and diameter, but some gaps wound open.  Stiffness per turn does not
    depend on pitch, so every free gap still opens by the same amount."""
    gaps = np.full(N - 1, D_OUT)
    idx = np.arange(N - 1)[free_gap_slice()]
    sel = idx[len(idx) // 2 - n_open // 2: len(idx) // 2 - n_open // 2 + n_open] if where == "centre" \
        else np.concatenate([idx[:n_open // 2], idx[-(n_open - n_open // 2):]])
    gaps[sel] *= pitch_mult
    gaps[idx] += x / len(idx)
    return L_of(hc.positions_from_gaps(gaps))


for where in ("centre", "ends"):
    s = sens_generic(lambda x, w=where: preopened(x, where=w))
    F = k_turn * X_MAX / N_FREE_GAPS
    print(f" {'14 gaps pre-opened to 2x pitch at the '+where:<50s} {preopened(0, where=where)*1e6:7.3f} "
          f"{s:13,.0f} {F*1e3:6.1f} {hc.spring_stress(F, D_COIL, D_WIRE)/1e6:8.1f}")

fig, ax = plt.subplots(figsize=(7.2, 3.4))
nds = [r[0] for r in rows]
ax.plot(nds, [r[1] / 1e3 for r in rows], color=S1, marker="o", ms=6)
for nd, sv, tau in rows:
    ax.annotate(f"{tau:.0f} MPa", (nd, sv / 1e3), textcoords="offset points", xytext=(0, 9),
                ha="center", fontsize=8.5, color="#52514e")
ax.set_xlabel("bonded turns per end (of 32 total)")
ax.set_ylabel("frequency sensitivity (thousand ppm/mm)")
ax.set_title("Sensitivity peaks at 4 to 6 bonded turns per end; wire stress keeps rising\n"
             "labels: shear stress at 3 mm (annealed copper yields near 40 MPa)")
ax.set_ylim(top=ax.get_ylim()[1] * 1.06)
fig.savefig(FIG / "bonded-turns-tradeoff.png", dpi=160, bbox_inches="tight"); plt.close(fig)
print("\nfigures written to docs/figures")
