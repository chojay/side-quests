"""
gate_stack.py - the gate-dielectric offset problem, drawn to scale.

Reproduces the classic screening argument of Robertson 2006 (Rep. Prog.
Phys. 69, 327, doi:10.1088/0034-4885/69/2/R02): a gate dielectric on silicon
needs a conduction-band offset of at least ~1 eV to keep electron tunneling
injection acceptable. SiO2 and HfO2 clear the bar; Ta2O5 and TiO2 do not,
which is one of the two independent reasons Ta2O5 lost the high-k race (the
other, thermodynamic instability against Si, is the demo of the neighboring
mp-interface-reactions project).

Band edges vs vacuum from Robertson's compiled electron affinities and gaps
(representative mid-range values; reported EAs scatter by a few tenths of an eV).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from band_diagram import Material, stack_alignment, stack_profile

SI = Material("Si", e_cb=-4.05, e_vb=-5.17, color="#2b6cb0",
              source="chi 4.05 / Eg 1.12")
SIO2 = Material("SiO$_2$", e_cb=-0.90, e_vb=-9.90, color="#2f855a",
                source="Robertson 2006")
HFO2 = Material("HfO$_2$", e_cb=-2.50, e_vb=-8.40, color="#38a169",
                source="Robertson 2006")
TA2O5 = Material("Ta$_2$O$_5$", e_cb=-3.75, e_vb=-8.15, color="#dd6b20",
                 source="Robertson 2006")
TIO2 = Material("TiO$_2$", e_cb=-4.00, e_vb=-7.20, color="#c53030",
                source="Robertson 2006")

fig = plt.figure(figsize=(14.5, 5.8))
gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.24)

ax1 = fig.add_subplot(gs[0])
stack_alignment([SI, SIO2, HFO2, TA2O5, TIO2], ax=ax1)
ax1.axhline(SI.e_cb, ls="--", lw=1.3, color=SI.color, alpha=0.7)
ax1.axhline(SI.e_cb + 1.0, ls=":", lw=1.6, color="#b3261e", alpha=0.9)
ax1.annotate("Si CBM", xy=(1.005, SI.e_cb), xycoords=("axes fraction", "data"),
             ha="left", va="center", fontsize=8.5, color=SI.color,
             annotation_clip=False)
ax1.annotate("> 1 eV offset rule", xy=(1.005, SI.e_cb + 1.0),
             xycoords=("axes fraction", "data"), ha="left", va="center",
             fontsize=8.5, color="#b3261e", annotation_clip=False)
ax1.set_title("(a) gate-dielectric screening vs Si", fontsize=11.5,
              fontweight="bold", pad=12)

ax2 = fig.add_subplot(gs[1])
stack_profile([SI, SIO2, HFO2], ax=ax2, barrier_ref=0)
ax2.set_title("(b) Si | SiO$_2$ | HfO$_2$ gate stack", fontsize=11.5,
              fontweight="bold", pad=12)

fig.suptitle("Gate-dielectric band offsets (Robertson 2006 values)",
             fontsize=13, fontweight="bold", y=1.00)
fig.savefig("gate_stack_alignment.svg", bbox_inches="tight")
fig.savefig("gate_stack_alignment.png", dpi=200, bbox_inches="tight")

print(f"{'oxide':<8} {'dEc vs Si (eV)':>15}   verdict (> 1 eV rule)")
for m in (SIO2, HFO2, TA2O5, TIO2):
    d = m.e_cb - SI.e_cb
    print(f"{m.name.replace('$','').replace('_',''):<8} {d:>+15.2f}   "
          f"{'pass' if d > 1.0 else 'FAIL'}")
print("wrote gate_stack_alignment.svg / .png")
