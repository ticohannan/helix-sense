# =====================================================================================
#  STRETCHABLE COIL -> INDUCTANCE / RING-DOWN DESIGN EXPLORER   (v5)
#  helix-sense project version 0.2.0
#  Single standalone Jupyter cell.  WinPython 3.12.
#  numpy, scipy, matplotlib, pandas, ipywidgets>=8
#
#  Mechanical arrangement modelled: coil floats inside a guide tube, both ends bonded
#  to the member being measured.  A number of turns at each end are held by the bond
#  and do not participate in the stretch; only the free turns spread out.
#
#  v4 added: bonded (dead) end turns, MCU timer presets, member-CTE presets,
#  helical spring force / shear stress check.
#  v5 fixes turn geometry: turn centres now span (length - wire OD), so a close-wound
#  coil has pitch = wire OD with or without bonded turns, and a displacement x moves
#  the end turn by exactly x.  v4 over-spread the bonded-turn case by one wire OD and
#  under-stretched the unbonded case by a factor (N-1)/N.
#
#  INDUCTANCE: exact coaxial-filament summation over arbitrary turn positions.
#     L = sum_i L_self + sum_{i!=j} M_ij
#     L_self = mu0*R*(ln(8R/a) - 2 + 0.25)
#     M_ij   = mu0*sqrt(R1R2)*[(2/k - k)K(k) - (2/k)E(k)],  k^2 = 4R1R2/((R1+R2)^2+d^2)
#
#  RING-DOWN: s^2 + s(R_s/L + G_p/C) + (1 + R_s*G_p)/(LC) = 0
#     I0 = V_mid/(R_ex + Rds + R_dc),   Vpk = I0*sqrt(L/C)
# =====================================================================================

%matplotlib inline
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as W
from IPython.display import display
from scipy.special import ellipk, ellipe

try:
    from scipy.special import ber, bei, berp, beip
    _HAVE_KELVIN = True
except Exception:
    _HAVE_KELVIN = False

MU0 = 4e-7 * np.pi
RHO_CU_20 = 1.724e-8
ALPHA_CU = 0.00393
F_CEILING = 10e6

# ------------------------------------------------------------------ wire
def awg_to_mm(awg):
    return 0.127 * 92.0 ** ((36.0 - np.asarray(awg, dtype=float)) / 39.0)

def mm_to_awg(d_mm):
    return 36.0 - 39.0 * np.log(np.asarray(d_mm, float) / 0.127) / np.log(92.0)

_BUILD_TBL = {20:(0.851,0.879), 22:(0.686,0.711), 24:(0.554,0.582), 26:(0.447,0.472),
              28:(0.356,0.386), 30:(0.287,0.310), 32:(0.231,0.252), 34:(0.185,0.203),
              36:(0.147,0.163), 38:(0.119,0.132), 40:(0.096,0.109)}
_BT_G = np.array(sorted(_BUILD_TBL))
_BT_S = np.array([_BUILD_TBL[g][0] for g in _BT_G])
_BT_H = np.array([_BUILD_TBL[g][1] for g in _BT_G])

def insulation_build_mm(d_bare_mm, build="heavy"):
    if build == "none":
        return 0.0
    g = float(np.clip(mm_to_awg(d_bare_mm), _BT_G[0], _BT_G[-1]))
    od = np.interp(g, _BT_G, np.log(_BT_S if build == "single" else _BT_H))
    return max(float(np.exp(od)) - float(d_bare_mm), 0.0)

# ------------------------------------------------------------------ turn geometry
def turn_positions(N, n_dead, d_out_m, length_m):
    """Axial position of each turn centre.  length_m is the coil length measured over
    the outside of the end turns, so the centres span length_m - d_out_m and a
    close-wound coil (length = N*d_out) has pitch exactly d_out.  n_dead turns at each
    end are held by the bond at close-wound pitch; the rest spread evenly."""
    N = int(N)
    span = max(length_m - d_out_m, 0.0)
    n_dead = int(max(min(n_dead, (N - 2) // 2), 0))
    if n_dead == 0:
        return np.linspace(0.0, span, N)
    z = np.empty(N)
    z[:n_dead] = np.arange(n_dead) * d_out_m
    z[N - n_dead:] = span - (np.arange(n_dead)[::-1]) * d_out_m
    n_mid = N - 2 * n_dead
    if n_mid > 0:
        z[n_dead:N - n_dead] = np.linspace(z[n_dead - 1], z[N - n_dead], n_mid + 2)[1:-1]
    return z

# ------------------------------------------------------------------ inductance
def _mutual_coaxial(R1, R2, d):
    m = np.clip(4.0 * R1 * R2 / ((R1 + R2) ** 2 + d ** 2), 1e-18, 1.0 - 1e-12)
    k = np.sqrt(m)
    return MU0 * np.sqrt(R1 * R2) * ((2.0 / k - k) * ellipk(m) - (2.0 / k) * ellipe(m))

def _loop_self(R, a, Y=0.25):
    return MU0 * R * (np.log(8.0 * R / a) - 2.0 + Y)

def coil_inductance_z(z, D_coil_m, a_wire_m, mu_eff=1.0, pitch_correction=True):
    R = 0.5 * D_coil_m
    N = len(z)
    L = N * _loop_self(R, a_wire_m, 0.25)
    if N > 1:
        M = _mutual_coaxial(R, R, z[:, None] - z[None, :])
        np.fill_diagonal(M, 0.0)
        L += M.sum()
    if pitch_correction and N > 1:
        p = float(np.mean(np.diff(z)))
        L *= np.cos(np.arctan2(p, np.pi * D_coil_m)) ** 2
    return float(L * mu_eff)

def wheeler_check(N, D_coil_m, length_m):
    r = 0.5 * D_coil_m
    return MU0 * N ** 2 * np.pi * r ** 2 / (length_m + 0.9 * r)

# ------------------------------------------------------------------ resistance
def wire_length_z(z, D_coil_m):
    p = float(np.mean(np.diff(z))) if len(z) > 1 else 0.0
    return len(z) * np.hypot(np.pi * D_coil_m, p)

def r_dc_z(z, D_coil_m, a_wire_m, temp_C=20.0):
    rho = RHO_CU_20 * (1.0 + ALPHA_CU * (temp_C - 20.0))
    return rho * wire_length_z(z, D_coil_m) / (np.pi * a_wire_m ** 2)

def ac_factor(a_wire_m, f, temp_C=20.0):
    rho = RHO_CU_20 * (1.0 + ALPHA_CU * (temp_C - 20.0))
    dlt = np.sqrt(rho / (np.pi * max(f, 1e-9) * MU0))
    q = np.sqrt(2.0) * a_wire_m / dlt
    if q < 1e-3:
        return 1.0
    if _HAVE_KELVIN:
        den = berp(q) ** 2 + beip(q) ** 2
        if den > 0:
            return float(max((q / 2.0) * (ber(q) * beip(q) - bei(q) * berp(q)) / den, 1.0))
    x = a_wire_m / dlt
    return float(max(x / 2.0 + 0.25 + 3.0 / (32.0 * max(x, 1e-6)), 1.0))

# ------------------------------------------------------------------ self-C
_MED_LD = np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.5,2.0,2.5,3.0,3.5,4.0,
                    4.5,5.0,6.0,8.0,10.0,15.0,20.0,25.0,30.0,40.0,50.0])
_MED_H  = np.array([1.36,0.81,0.60,0.54,0.50,0.48,0.47,0.46,0.46,0.46,0.47,0.50,0.56,
                    0.61,0.67,0.72,0.77,0.81,0.92,1.12,1.32,1.86,2.36,2.90,3.40,4.60,5.80])

def self_capacitance(D_coil_m, length_m, eps_r=1.0, scale=1.0):
    ld = np.clip(length_m / D_coil_m, _MED_LD[0], _MED_LD[-1])
    H = float(np.interp(ld, _MED_LD, _MED_H))
    return H * (D_coil_m * 100.0) * 1e-12 * (1.0 + eps_r) / 2.0 * scale

# ------------------------------------------------------------------ spring mechanics
def spring_check(delta_m, D_coil_m, d_wire_m, n_active, G_Pa, tau_yield_Pa):
    """Helical extension spring: force, Wahl-corrected shear stress, margin."""
    if n_active < 1 or d_wire_m <= 0:
        return dict(F_mN=np.nan, tau_MPa=np.nan, util=np.nan, C=np.nan)
    C = D_coil_m / d_wire_m
    F = delta_m * G_Pa * d_wire_m ** 4 / (8.0 * D_coil_m ** 3 * n_active)
    Kw = (4 * C - 1) / (4 * C - 4) + 0.615 / C
    tau = 8.0 * F * D_coil_m * Kw / (np.pi * d_wire_m ** 3)
    return dict(F_mN=F * 1e3, tau_MPa=tau / 1e6, util=tau / tau_yield_Pa, C=C)

# ------------------------------------------------------------------ tank
DRIVE_MODES = {"mosfet_open": 0.0, "diode_clamped": 0.5, "hard_low": 1.0}

def tank(L, C, R_s, G_p=0.0):
    if C <= 0 or L <= 0:
        return dict(f0=np.nan, fd=np.nan, Q=np.nan, tau=np.nan, cycles=np.nan)
    alpha = 0.5 * (R_s / L + G_p / C)
    wn2 = (1.0 + R_s * G_p) / (L * C)
    wn = np.sqrt(wn2)
    wd = np.sqrt(wn2 - alpha ** 2) if wn2 > alpha ** 2 else 0.0
    Q = wn / (2.0 * alpha) if alpha > 0 else np.inf
    tau = 1.0 / alpha if alpha > 0 else np.inf
    return dict(f0=wn / (2 * np.pi), fd=wd / (2 * np.pi), Q=Q, tau=tau,
                cycles=(wd / (2 * np.pi)) * tau if np.isfinite(tau) else np.inf)

# ------------------------------------------------------------------ operating point
def solve_point(stretch, *, N, n_dead, D_coil_mm, d_bare_mm, d_out_mm, L0_m, mu_eff,
                eps_r, C_ext_F, C_stray_F, temp_C, use_self_C, selfC_scale, pitch_corr,
                R_ex, Rds, drive_mode, V_mid, R_probe, V_thresh,
                timer_ns, t_pd_ns, t_jit_ns, n_skip, n_meas, n_avg,
                prox_factor, C_tempco_ppm, member_cte_ppm, G_Pa, tau_yield_Pa):
    Dm = D_coil_mm * 1e-3
    a = 0.5 * d_bare_mm * 1e-3
    length = L0_m * (1.0 + stretch)
    z = turn_positions(N, n_dead, d_out_mm * 1e-3, length)

    L = coil_inductance_z(z, Dm, a, mu_eff, pitch_corr)
    Cs = self_capacitance(Dm, length, eps_r, selfC_scale) if use_self_C else 0.0
    C = C_ext_F + C_stray_F + Cs
    Rdc = r_dc_z(z, Dm, a, temp_C)

    G_p = DRIVE_MODES[drive_mode] / (R_ex + Rds) if (R_ex + Rds) > 0 else 0.0
    if np.isfinite(R_probe) and R_probe > 0:
        G_p += 1.0 / R_probe

    t = tank(L, C, Rdc, G_p)
    Rac = Rdc * ac_factor(a, t["f0"], temp_C) * prox_factor if t["f0"] > 0 else Rdc
    t = tank(L, C, Rac, G_p)

    Z0 = np.sqrt(L / C)
    I0 = V_mid / (R_ex + Rds + Rdc)
    Vpk = I0 * Z0

    if np.isfinite(t["tau"]) and Vpk > V_thresh > 0 and t["fd"] > 0:
        t_use = t["tau"] * np.log(Vpk / V_thresh)
        n_use = t["fd"] * t_use
    else:
        t_use, n_use = 0.0, 0.0

    n_eff = max(min(n_meas, n_use - n_skip), 0.0)
    if n_eff > 1 and t["fd"] > 0:
        sigma_t = np.sqrt(2 * (timer_ns * 1e-9) ** 2 / 12.0 + 2 * (t_jit_ns * 1e-9) ** 2)
        df_f = sigma_t * t["fd"] / n_eff / np.sqrt(max(n_avg, 1))
        rate = 1.0 / (max(n_avg, 1) * (t_use + 1e-6))
    else:
        df_f, rate = np.nan, np.nan
    df_hz = df_f * t["fd"] if np.isfinite(df_f) else np.nan

    tc_cap = -0.5 * C_tempco_ppm
    Qv = t["Q"]
    tc_q = (2.0 / (8.0 * Qv ** 2)) * (-ALPHA_CU * 1e6) if np.isfinite(Qv) and Qv > 0 else 0.0
    sp = spring_check(L0_m * stretch, Dm, d_bare_mm * 1e-3, max(N - 2 * n_dead, 1),
                      G_Pa, tau_yield_Pa)

    p = float(np.mean(np.diff(z))) if len(z) > 1 else 0.0
    return dict(stretch=stretch, disp_mm=(length - L0_m) * 1e3, length_mm=length * 1e3,
                pitch_mm=p * 1e3, gap_mm=(p - d_out_mm * 1e-3) * 1e3,
                pitch_deg=np.degrees(np.arctan2(p, np.pi * Dm)),
                L_H=L, L_uH=L * 1e6, C_self_pF=Cs * 1e12, C_tot_pF=C * 1e12,
                R_dc=Rdc, R_ac=Rac, Z0=Z0, I0_mA=I0 * 1e3, Vpk=Vpk,
                t_use_us=t_use * 1e6, n_use=n_use, n_eff=n_eff,
                df_hz=df_hz, df_ppm=df_f * 1e6, rate_hz=rate,
                tc_elec_ppm=tc_cap + tc_q,
                L_err_frac=(t["f0"] ** 2 / t["fd"] ** 2 - 1.0) if t["fd"] > 0 else np.nan,
                F_mN=sp["F_mN"], tau_MPa=sp["tau_MPa"], util=sp["util"], index=sp["C"], **t)

def sweep(smax, npts, **kw):
    return pd.DataFrame([solve_point(s, **kw) for s in np.linspace(0.0, smax, npts)])

# =====================================================================================
#  UI
# =====================================================================================
def _num(label, lo, hi, step, val, integer=False, dw="185px"):
    S = (W.IntSlider if integer else W.FloatSlider)(
        value=val, min=lo, max=hi, step=step, description=label, continuous_update=False,
        readout=False, layout=W.Layout(width="345px"), style={"description_width": dw})
    T = (W.BoundedIntText if integer else W.BoundedFloatText)(
        value=val, min=lo, max=hi, step=step, layout=W.Layout(width="115px"))
    W.jslink((S, "value"), (T, "value"))
    return W.HBox([S, T]), S

c_units = W.RadioButtons(options=[("Set by AWG", "awg"), ("Set by mm", "mm")], value="awg",
                         description="Wire input", style={"description_width": "185px"})
w_awg, s_awg = _num("Wire size (AWG)", 20, 40, 1, 30, integer=True)
w_dmm, s_dmm = _num("...or wire dia (mm)", 0.05, 1.2, 0.001, 0.255)
c_build = W.Dropdown(options=[("Heavy build enamel", "heavy"), ("Single build enamel", "single"),
                              ("Bare", "none")], value="heavy", description="Insulation",
                     style={"description_width": "185px"})
c_geom = W.RadioButtons(options=[("Set turns N", "N"), ("Set compressed length", "L0")],
                        value="L0", description="Geometry from",
                        style={"description_width": "185px"})
w_N,  s_N  = _num("Turns N", 3, 800, 1, 32, integer=True)
w_L0, s_L0 = _num("Compressed len (mm)", 2.0, 60.0, 0.1, 10.0)
w_D,  s_D  = _num("Coil mean dia (mm)", 1.0, 30.0, 0.05, 5.0)
w_nd, s_nd = _num("Bonded turns, each end", 0, 20, 1, 2, integer=True)
c_pitch = W.Checkbox(value=True, description="cos^2(pitch) helix correction")

w_str,  s_str  = _num("Stretch, operating (%)", 0.0, 300.0, 0.5, 15.0)
w_smax, s_smax = _num("Stretch, sweep max (%)", 5.0, 300.0, 5.0, 30.0)
w_npts, s_npts = _num("Sweep points", 5, 400, 1, 61, integer=True)

c_fill = W.Dropdown(options=[("Air (1.0)", 1.0), ("PP guide tube (2.2)", 2.2),
                             ("PTFE tube (2.1)", 2.1), ("Silicone (3.2)", 3.2),
                             ("Epoxy (3.8)", 3.8)], value=1.0, description="Filler eps_r",
                    style={"description_width": "185px"})
w_eps, s_eps = _num("...or custom eps_r", 1.0, 20.0, 0.05, 1.0)
w_mu,  s_mu  = _num("Effective core mu_r", 0.5, 50.0, 0.01, 1.0)

w_C,  s_C  = _num("Tank C, external (pF)", 100.0, 200000.0, 100.0, 4700.0)
w_Cs, s_Cs = _num("Stray/probe C (pF)", 0.0, 500.0, 0.5, 15.0)
w_T,  s_T  = _num("Temperature (degC)", -40.0, 150.0, 0.5, 20.0)
c_selfC = W.Checkbox(value=True, description="Include Medhurst self-C")
w_sC, s_sC = _num("Self-C scale factor", 0.1, 5.0, 0.05, 1.0)
w_px, s_px = _num("Proximity-effect factor", 1.0, 6.0, 0.1, 2.0)

c_drive = W.Dropdown(options=[("MOSFET opens, R disconnects (mid-rail)", "mosfet_open"),
                              ("Diode clamps one polarity (legacy)", "diode_clamped"),
                              ("Pin held LOW, no diode (legacy)", "hard_low")],
                     value="mosfet_open", description="Drive during ring",
                     style={"description_width": "185px"})
w_Rex, s_Rex = _num("Series R_ex (ohm)", 1.0, 2000.0, 1.0, 68.0)
w_Rds, s_Rds = _num("Switch Rds_on (ohm)", 0.1, 50.0, 0.1, 5.0)
w_Vm,  s_Vm  = _num("Mid-rail V across L (V)", 0.5, 15.0, 0.1, 2.5)
w_Rpr, s_Rpr = _num("Probe/bias R (kohm)", 0.5, 100000.0, 0.5, 500.0)

MCUS = {"AVR 16 MHz (Uno / Nano / Mega)": 62.5,
        "SAMD21 48 MHz (Zero, Nano 33 IoT)": 20.83,
        "ESP32 80 MHz capture": 12.5,
        "STM32F103 72 MHz (Blue Pill)": 13.9,
        "SAM3X 84 MHz (Arduino Due)": 11.9,
        "RP2040 PIO 125 MHz (Pico, Nano RP2040)": 8.0,
        "STM32H7 240 MHz (Arduino Giga R1)": 4.17,
        "Teensy 4.x 600 MHz cycle counter": 1.67}
c_mcu = W.Dropdown(options=list(MCUS), value="RP2040 PIO 125 MHz (Pico, Nano RP2040)",
                   description="MCU preset", style={"description_width": "185px"},
                   layout=W.Layout(width="470px"))
w_Vth, s_Vth = _num("Comparator hysteresis (mV)", 1.0, 500.0, 1.0, 10.0)
w_tpd, s_tpd = _num("Comparator t_pd (ns)", 1.0, 2000.0, 1.0, 10.0)
w_tjt, s_tjt = _num("t_pd dispersion (ns)", 0.05, 200.0, 0.05, 1.5)
w_tns, s_tns = _num("MCU timer LSB (ns)", 1.0, 4000.0, 0.01, 8.0)
w_skp, s_skp = _num("Cycles skipped at start", 0, 50, 1, 3, integer=True)
w_msr, s_msr = _num("Cycles measured", 2, 500, 1, 32, integer=True)
w_nav, s_nav = _num("Bursts averaged", 1, 5000, 1, 256, integer=True)

CTES = {"Invar (1.2)": 1.2, "Fused silica (0.5)": 0.5, "Borosilicate glass (3.3)": 3.3,
        "Steel (12)": 12.0, "Brass (19)": 19.0, "Aluminium (23)": 23.0,
        "Polypropylene (100)": 100.0, "Silicone rubber (250)": 250.0}
c_cte = W.Dropdown(options=list(CTES), value="Steel (12)", description="Member material",
                   style={"description_width": "185px"}, layout=W.Layout(width="470px"))
w_cte, s_cte = _num("Member CTE (ppm/degC)", 0.0, 500.0, 0.1, 12.0)
w_ctc, s_ctc = _num("Cap tempco (ppm/degC)", 0.0, 5000.0, 1.0, 30.0)
w_dT,  s_dT  = _num("Temp swing, +/- (degC)", 0.0, 60.0, 0.5, 5.0)

w_G,   s_G   = _num("Wire shear modulus (GPa)", 10.0, 90.0, 0.5, 44.0)
w_ty,  s_ty  = _num("Wire shear yield (MPa)", 5.0, 400.0, 1.0, 40.0)

c_xaxis = W.RadioButtons(options=[("Displacement (mm)", "disp_mm"), ("Stretch (%)", "pct")],
                         value="disp_mm", description="X axis",
                         style={"description_width": "185px"})
c_plots = W.SelectMultiple(options=["L vs displacement", "Frequency vs displacement",
                                    "Sensitivity dL/dx & df/dx", "Q and tau",
                                    "Usable cycles & resolution", "Ring-down waveform",
                                    "Turn positions"],
                           value=("L vs displacement", "Frequency vs displacement",
                                  "Usable cycles & resolution", "Ring-down waveform"),
                           rows=7, description="Plots", style={"description_width": "185px"})
out = W.Output()

def _mcu_pick(ch):
    s_tns.value = MCUS[ch["new"]]

def _cte_pick(ch):
    s_cte.value = CTES[ch["new"]]

c_mcu.observe(_mcu_pick, names="value")
c_cte.observe(_cte_pick, names="value")

def _render(*_a, **_k):
    with out:
        out.clear_output(wait=True)
        if c_units.value == "awg":
            awg = int(s_awg.value); d_bare = float(awg_to_mm(awg))
        else:
            d_bare = float(s_dmm.value); awg = float(mm_to_awg(d_bare))
        d_out = d_bare + insulation_build_mm(d_bare, c_build.value)
        if c_geom.value == "N":
            N = int(s_N.value); L0_mm = N * d_out
        else:
            L0_mm = float(s_L0.value); N = max(int(round(L0_mm / d_out)), 4)
        L0_m = L0_mm * 1e-3
        eps_r = float(s_eps.value) if abs(s_eps.value - 1.0) > 1e-9 else float(c_fill.value)
        n_dead = int(min(s_nd.value, (N - 2) // 2))

        kw = dict(N=N, n_dead=n_dead, D_coil_mm=float(s_D.value), d_bare_mm=d_bare,
                  d_out_mm=d_out, L0_m=L0_m, mu_eff=float(s_mu.value), eps_r=eps_r,
                  C_ext_F=float(s_C.value) * 1e-12, C_stray_F=float(s_Cs.value) * 1e-12,
                  temp_C=float(s_T.value), use_self_C=bool(c_selfC.value),
                  selfC_scale=float(s_sC.value), pitch_corr=bool(c_pitch.value),
                  R_ex=float(s_Rex.value), Rds=float(s_Rds.value), drive_mode=c_drive.value,
                  V_mid=float(s_Vm.value), R_probe=float(s_Rpr.value) * 1e3,
                  V_thresh=float(s_Vth.value) * 1e-3, timer_ns=float(s_tns.value),
                  t_pd_ns=float(s_tpd.value), t_jit_ns=float(s_tjt.value),
                  n_skip=int(s_skp.value), n_meas=int(s_msr.value), n_avg=int(s_nav.value),
                  prox_factor=float(s_px.value), C_tempco_ppm=float(s_ctc.value),
                  member_cte_ppm=float(s_cte.value), G_Pa=float(s_G.value) * 1e9,
                  tau_yield_Pa=float(s_ty.value) * 1e6)

        op = solve_point(float(s_str.value) / 100.0, **kw)
        df = sweep(float(s_smax.value) / 100.0, int(s_npts.value), **kw)
        x = df["disp_mm"].values if c_xaxis.value == "disp_mm" else df["stretch"].values * 100
        u = "mm" if c_xaxis.value == "disp_mm" else "%"
        xlab = "Displacement from compressed (mm)" if u == "mm" else "Stretch (%)"
        dLdx = np.gradient(df["L_uH"].values, x)
        dfdx = np.gradient(df["fd"].values, x)
        i_op = int(np.argmin(np.abs(df["stretch"].values - float(s_str.value) / 100.0)))
        sens_L, sens_f = dLdx[i_op], dfdx[i_op]
        ppm_per_x = 1e6 * sens_f / op["fd"]
        res_x = abs(op["df_hz"] / sens_f) if sens_f else np.nan
        wch = wheeler_check(N, s_D.value * 1e-3, L0_m * (1 + s_str.value / 100.0))
        drift_elec_x = abs(op["tc_elec_ppm"] / ppm_per_x) if ppm_per_x else np.nan
        drift_mech_x = float(s_cte.value) * 1e-6 * L0_mm
        drift_tot = np.hypot(drift_elec_x, drift_mech_x)

        print("=" * 86)
        print(f" WIRE   AWG {awg:.1f}   bare {d_bare:.4f} mm   OD {d_out:.4f} mm")
        print(f" COIL   N = {N} ({n_dead} bonded each end, {N-2*n_dead} free)"
              f"   dia {s_D.value:.3f} mm   compressed {L0_mm:.2f} mm")
        print(f" OP PT  stretch {op['stretch']*100:.1f} %  length {op['length_mm']:.2f} mm"
              f"  displacement {op['disp_mm']:.3f} mm  pitch angle {op['pitch_deg']:.2f} deg")
        print("-" * 86)
        print(f" L = {op['L_uH']:.5f} uH   (Wheeler {wch*1e6:.4f} uH,"
              f" delta {100*(op['L_H']-wch)/wch:+.1f} %)")
        print(f" C = {s_C.value:.0f} + {s_Cs.value:.1f} stray + {op['C_self_pF']:.3f} self"
              f" = {op['C_tot_pF']:.2f} pF     Z0 = {op['Z0']:.2f} ohm")
        print(f" R_dc {op['R_dc']:.4f} ohm   R_ac {op['R_ac']:.4f} ohm")
        print(f" f_d = {op['fd']/1e6:.6f} MHz   half-period {0.5e9/op['fd']:.1f} ns"
              f"   Q = {op['Q']:.1f}   tau = {op['tau']*1e6:.2f} us")
        print(f" ring lasts {op['t_use_us']:.2f} us = {op['n_use']:.0f} cycles"
              f"   I0 = {op['I0_mA']:.1f} mA   peak swing {op['Vpk']:.3f} V")
        print("-" * 86)
        print(f" MECHANICAL  spring index D/d = {op['index']:.1f}"
              f"   force at {op['disp_mm']:.2f} mm = {op['F_mN']:.2f} mN")
        print(f"             wire shear stress {op['tau_MPa']:.1f} MPa"
              f" = {100*op['util']:.0f} % of {s_ty.value:.0f} MPa yield")
        print("-" * 86)
        print(f" READOUT  {c_mcu.value}, LSB {s_tns.value:g} ns")
        print(f"          skip {int(s_skp.value)}, measure {op['n_eff']:.0f} cycles,"
              f" average {int(s_nav.value)} bursts -> {op['rate_hz']:.0f} Hz update rate")
        print(f" SENSITIVITY  dL/dx = {sens_L*1e3:+.2f} nH/{u}"
              f"   df/dx = {sens_f/1e3:+.2f} kHz/{u} = {ppm_per_x:+,.0f} ppm/{u}")
        print(f" RESOLUTION   {op['df_ppm']:.2f} ppm  ->  {res_x*1000:,.3f} um")
        print("-" * 86)
        print(" TEMPERATURE ERROR BUDGET")
        print(f"   electrical {op['tc_elec_ppm']:+.1f} ppm/degC"
              f" -> {drift_elec_x*1000:,.2f} um/degC")
        print(f"   mechanical {s_cte.value:.1f} ppm/degC on {L0_mm:.1f} mm"
              f" -> {drift_mech_x*1000:,.2f} um/degC   ({c_cte.value})")
        print(f"   combined {drift_tot*1000:,.2f} um/degC"
              f" -> +/-{drift_tot*float(s_dT.value)*1000:,.1f} um over +/-{s_dT.value:.0f} degC")
        print("=" * 86)

        warn = []
        half_ns = 0.5e9 / op["fd"]
        if op["fd"] > F_CEILING:
            warn.append(f"f_d = {op['fd']/1e6:.2f} MHz exceeds 10 MHz. Try C ="
                        f" {1/((2*np.pi*5e6)**2*op['L_H'])*1e12:,.0f} pF for 5 MHz.")
        if s_tpd.value > 0.10 * 2 * half_ns:
            warn.append(f"Comparator t_pd is {100*s_tpd.value/(2*half_ns):.0f} % of a period."
                        " LM339 (1300 ns) and LM311 (165 ns) are too slow; use LT1016CN8.")
        if half_ns < 5 * s_tns.value:
            warn.append(f"Half-period {half_ns:.0f} ns is under 5 timer LSBs"
                        f" ({s_tns.value:g} ns). This MCU cannot resolve the ring.")
        if op["n_use"] < s_skp.value + s_msr.value:
            warn.append(f"Ring lasts {op['n_use']:.0f} cycles; you asked for"
                        f" {int(s_skp.value)}+{int(s_msr.value)}. Shorten the window.")
        if op["util"] > 0.5:
            warn.append(f"Wire shear stress is {100*op['util']:.0f} % of yield."
                        " Risk of permanent set; use a smaller stretch, finer wire,"
                        " or a larger coil diameter.")
        if drift_mech_x > 5 * res_x:
            warn.append(f"Mechanical drift ({drift_mech_x*1000:.2f} um/degC) is"
                        f" {drift_mech_x/res_x:.0f}x the electrical resolution."
                        " The member, not the electronics, sets your accuracy.")
        if 2 * (s_tjt.value * 1e-9) ** 2 > 4 * (s_tns.value * 1e-9) ** 2 / 12.0:
            warn.append("Comparator delay dispersion now dominates the timer LSB."
                        " A faster MCU will not improve resolution; average more bursts"
                        " or use a lower-dispersion comparator.")
        if warn:
            print("\n WARNINGS")
            for w_ in warn:
                print("  * " + w_)

        sel = list(c_plots.value)
        if sel:
            n = len(sel); ncol = 2 if n > 1 else 1; nrow = int(np.ceil(n / ncol))
            fig, axes = plt.subplots(nrow, ncol, figsize=(6.4 * ncol, 4.0 * nrow))
            axes = np.atleast_1d(axes).ravel()
            for ax in axes[n:]:
                ax.axis("off")
            for ax, name in zip(axes, sel):
                if name == "L vs displacement":
                    ax.plot(x, df["L_uH"], lw=2); ax.set_ylabel("L (uH)"); ax.set_title("Inductance")
                elif name == "Frequency vs displacement":
                    ax.plot(x, df["fd"] / 1e6, lw=2, label="f damped")
                    ax.plot(x, df["f0"] / 1e6, lw=1, ls=":", label="f undamped")
                    ax.set_ylabel("f (MHz)"); ax.set_title("Resonance"); ax.legend(fontsize=8)
                elif name == "Sensitivity dL/dx & df/dx":
                    ax.plot(x, dLdx * 1e3, lw=2, color="C0")
                    ax.set_ylabel(f"dL/dx (nH/{u})", color="C0")
                    a2 = ax.twinx(); a2.plot(x, dfdx / 1e3, lw=2, color="C3")
                    a2.set_ylabel(f"df/dx (kHz/{u})", color="C3"); ax.set_title("Sensitivity")
                elif name == "Q and tau":
                    ax.plot(x, df["Q"], lw=2, color="C0"); ax.set_ylabel("Q", color="C0")
                    a2 = ax.twinx(); a2.plot(x, df["tau"] * 1e6, lw=2, color="C2")
                    a2.set_ylabel("tau (us)", color="C2"); ax.set_title("Damping")
                elif name == "Usable cycles & resolution":
                    ax.plot(x, df["n_use"], lw=2, color="C0")
                    ax.plot(x, df["n_eff"], lw=1.5, ls="--", color="C1")
                    ax.set_ylabel("cycles (solid avail, dashed used)", color="C0", fontsize=9)
                    a2 = ax.twinx(); a2.plot(x, df["df_ppm"], lw=2, color="C4")
                    a2.set_ylabel("resolution (ppm)", color="C4"); ax.set_title("Measurability")
                elif name == "Turn positions":
                    for frac, col, lab in ((0.0, "C0", "compressed"),
                                           (float(s_smax.value) / 100.0, "C3", "stretched")):
                        zz = turn_positions(N, n_dead, d_out * 1e-3, L0_m * (1 + frac)) * 1e3
                        ax.plot(zz, np.full_like(zz, frac), "|", ms=14, color=col, label=lab)
                    ax.set_ylim(-0.1, float(s_smax.value) / 100.0 + 0.1)
                    ax.set_xlabel("axial position (mm)"); ax.set_ylabel("stretch")
                    ax.set_title("Turn spacing (bonded ends stay put)")
                    ax.legend(fontsize=8); ax.grid(alpha=0.3); continue
                elif name == "Ring-down waveform":
                    if np.isfinite(op["tau"]) and op["fd"] > 0:
                        T = min(1.15 * max(op["t_use_us"] * 1e-6, 3 * op["tau"]), 400 / op["fd"])
                        t = np.linspace(0, T, 8000)
                        env = op["Vpk"] * np.exp(-t / op["tau"])
                        ax.plot(t * 1e6, env * np.sin(2 * np.pi * op["fd"] * t), lw=0.6)
                        ax.plot(t * 1e6, env, "r--", lw=1); ax.plot(t * 1e6, -env, "r--", lw=1)
                        ax.axhline(s_Vth.value * 1e-3, color="g", lw=1, ls=":")
                        ax.axhline(-s_Vth.value * 1e-3, color="g", lw=1, ls=":")
                        ax.set_xlabel("time (us)"); ax.set_ylabel("swing about mid-rail (V)")
                        ax.set_title(f"{op['fd']/1e6:.3f} MHz, {op['n_use']:.0f} cycles")
                    ax.grid(alpha=0.3); continue
                ax.set_xlabel(xlab); ax.grid(alpha=0.3)
            plt.tight_layout(); plt.show()

        globals()["coil_sweep_df"] = df
        globals()["coil_op_point"] = op
        print("\n[ exported: `coil_sweep_df`, `coil_op_point` ]")

for _w in [c_units, c_build, c_geom, c_fill, c_selfC, c_pitch, c_plots, c_xaxis, c_drive,
           s_awg, s_dmm, s_N, s_L0, s_D, s_nd, s_str, s_smax, s_npts, s_eps, s_mu, s_C,
           s_Cs, s_T, s_sC, s_px, s_Rex, s_Rds, s_Vm, s_Rpr, s_Vth, s_tpd, s_tjt, s_tns,
           s_skp, s_msr, s_nav, s_ctc, s_cte, s_dT, s_G, s_ty]:
    _w.observe(_render, names="value")

panel = W.VBox([
    W.HTML("<b>WIRE</b>"), c_units, w_awg, w_dmm, c_build,
    W.HTML("<b>COIL GEOMETRY</b>"), c_geom, w_N, w_L0, w_D, w_nd, c_pitch,
    W.HTML("<b>STRETCH</b>"), w_str, w_smax, w_npts,
    W.HTML("<b>MATERIALS</b>"), c_fill, w_eps, w_mu,
    W.HTML("<b>TANK</b>"), w_C, w_Cs, c_selfC, w_sC, w_px, w_T,
    W.HTML("<b>EXCITATION</b>"), c_drive, w_Rex, w_Rds, w_Vm, w_Rpr,
    W.HTML("<b>COMPARATOR &amp; MCU</b>"), c_mcu, w_tns, w_Vth, w_tpd, w_tjt,
    w_skp, w_msr, w_nav,
    W.HTML("<b>DRIFT</b>"), c_cte, w_cte, w_ctc, w_dT,
    W.HTML("<b>SPRING CHECK</b>"), w_G, w_ty,
    W.HTML("<b>OUTPUT</b>"), c_xaxis, c_plots,
])
display(W.HBox([panel], layout=W.Layout(border="1px solid #ccc", padding="6px")), out)
_render()
