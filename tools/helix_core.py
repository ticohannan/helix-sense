# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Tico Hannan
"""helix_core -- importable physics core for stretch-coil displacement sensing.

Same equations as the notebook cell in coil_stretch_inductance_tool.py, without the
widgets, so scripts and tests can call them.  tools/check_consistency.py verifies the
two stay in step.

Inductance: exact coaxial-filament summation over arbitrary turn positions
    L = sum_i L_self + sum_{i!=j} M_ij
    L_self = mu0*R*(ln(8R/a) - 2 + 1/4)
    M_ij   = mu0*sqrt(R1R2)*[(2/k - k)K(k) - (2/k)E(k)],  k^2 = 4R1R2/((R1+R2)^2 + d^2)
"""
import numpy as np
from scipy.special import ellipk, ellipe

MU0 = 4e-7 * np.pi
RHO_CU_20 = 1.724e-8      # ohm*m
ALPHA_CU = 0.00393        # 1/degC
G_CU = 44e9               # Pa, shear modulus of copper
RHO_CU_MASS = 8960.0      # kg/m^3

_BUILD_TBL = {20: (0.851, 0.879), 22: (0.686, 0.711), 24: (0.554, 0.582),
              26: (0.447, 0.472), 28: (0.356, 0.386), 30: (0.287, 0.310),
              32: (0.231, 0.252), 34: (0.185, 0.203), 36: (0.147, 0.163),
              38: (0.119, 0.132), 40: (0.096, 0.109)}


def awg_to_mm(awg):
    """Bare copper diameter, mm."""
    return 0.127 * 92.0 ** ((36.0 - np.asarray(awg, dtype=float)) / 39.0)


def enamel_od_mm(awg, build="heavy"):
    """Nominal overall diameter with enamel, mm (even gauges 20-40)."""
    s, h = _BUILD_TBL[int(awg)]
    return s if build == "single" else h


def mutual_coaxial(R1, R2, d):
    """Maxwell mutual inductance of two coaxial circular filaments, H."""
    m = np.clip(4.0 * R1 * R2 / ((R1 + R2) ** 2 + d ** 2), 1e-18, 1.0 - 1e-12)
    k = np.sqrt(m)
    return MU0 * np.sqrt(R1 * R2) * ((2.0 / k - k) * ellipk(m) - (2.0 / k) * ellipe(m))


def loop_self(R, a, Y=0.25):
    """Self inductance of one circular turn of wire radius a, H."""
    return MU0 * R * (np.log(8.0 * R / a) - 2.0 + Y)


def inductance(z, D_coil_m, a_wire_m, pitch_correction=True):
    """Inductance of coaxial turns at axial positions z (m).  D may be scalar or
    per-turn array, so segments of different diameter can be put in series."""
    z = np.asarray(z, dtype=float)
    N = len(z)
    R = 0.5 * np.broadcast_to(np.asarray(D_coil_m, dtype=float), (N,))
    L = float(np.sum(loop_self(R, a_wire_m)))
    if N > 1:
        M = mutual_coaxial(R[:, None], R[None, :], z[:, None] - z[None, :])
        np.fill_diagonal(M, 0.0)
        L += float(M.sum())
        if pitch_correction:
            p = float(np.mean(np.diff(z)))
            L *= np.cos(np.arctan2(p, np.pi * float(np.mean(2 * R)))) ** 2
    return L


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


def positions_from_gaps(gaps):
    """Turn positions from the N-1 centre-to-centre spacings."""
    return np.concatenate([[0.0], np.cumsum(gaps)])


def resonant_f(L, C):
    return 1.0 / (2.0 * np.pi * np.sqrt(L * C))


def turn_stiffness(D_coil_m, d_wire_m, G=G_CU):
    """Axial stiffness of ONE turn of a helical spring, N/m.  n turns in series
    give k/n.  Independent of pitch, strongly dependent on D (1/D^3)."""
    return G * d_wire_m ** 4 / (8.0 * D_coil_m ** 3)


def spring_stress(F, D_coil_m, d_wire_m):
    """Wahl-corrected wire shear stress, Pa."""
    C = D_coil_m / d_wire_m
    Kw = (4 * C - 1) / (4 * C - 4) + 0.615 / C
    return 8.0 * F * D_coil_m * Kw / (np.pi * d_wire_m ** 3)


def turn_weight(D_coil_m, d_wire_m):
    """Weight of one turn of bare copper, N."""
    return RHO_CU_MASS * 9.81 * np.pi * D_coil_m * np.pi * (0.5 * d_wire_m) ** 2
