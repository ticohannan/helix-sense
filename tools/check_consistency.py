# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Tico Hannan
"""Check that helix_core.py and the notebook cell compute the same inductance.

The notebook cell cannot be imported (it has an IPython magic and builds widgets),
so this executes only its physics section -- everything above the UI banner.
Run:  python tools/check_consistency.py
"""
import pathlib
import numpy as np
import helix_core as hc

src = (pathlib.Path(__file__).parent / "coil_stretch_inductance_tool.py").read_text()
head = src.split("#  UI\n")[0]
keep = [ln for ln in head.splitlines()
        if not ln.startswith("%") and "ipywidgets" not in ln and "IPython" not in ln
        and "matplotlib" not in ln]
ns = {}
exec("\n".join(keep), ns)

worst = 0.0
for length_mm in (10.0, 11.5, 13.0, 20.0):
    for n_dead in (0, 2, 4):
        z_nb = ns["turn_positions"](32, n_dead, 0.310e-3, length_mm * 1e-3)
        L_nb = ns["coil_inductance_z"](z_nb, 5e-3, 0.1275e-3)
        z_hc = hc.turn_positions(32, n_dead, 0.310e-3, length_mm * 1e-3)
        L_hc = hc.inductance(z_hc, 5e-3, 0.1275e-3)
        worst = max(worst, abs(L_nb - L_hc) / L_nb)
print(f"worst relative difference notebook vs helix_core: {worst:.2e}")
assert worst < 1e-12, "notebook cell and helix_core have drifted apart"
print("OK")
