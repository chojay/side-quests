"""
ito_al2o3.py - transparent-electronics gate stack: ITO against Al2O3.

Why does Al2O3 work as a gate dielectric on a degenerate transparent
conductor? Flatband alignment answers it in one picture: the electron
injection barrier from the ITO Fermi level into the Al2O3 conduction band is
roughly chi_ITO - chi_Al2O3, over 3 eV.

Representative literature values, all approximate (reported ITO electron
affinity and work function scatter by several tenths of an eV with tin
content, oxygen deficiency, and surface treatment):

  ITO    chi ~ 4.4 eV, Eg ~ 3.75 eV. Degenerate n-type: E_F sits at or above
         the conduction band edge, so d_fermi ~ 0 here (the field accepts it;
         for a metal-like contact the Thomas-Fermi length in screening.py is
         the relevant screening scale, not a depletion width).
  Al2O3  chi ~ 1.25 eV, Eg 8.8 eV crystalline (Robertson 2006); amorphous ALD
         films run narrower, ~6.5 eV, which lowers the hole barrier but
         barely moves the electron barrier that matters here.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from band_diagram import Material, heterojunction

ito = Material("ITO", e_cb=-4.40, e_vb=-8.15, color="#2b6cb0",
               d_fermi=0.0,   # degenerate: E_F pinned at the CB edge
               source="chi ~4.4 / Eg ~3.75 (approx.)")
al2o3 = Material(r"Al$_2$O$_3$", e_cb=-1.25, e_vb=-10.05, color="#2f855a",
                 source="Robertson 2006 (approx.)")

fig, ax = plt.subplots(figsize=(6.4, 5.8))
heterojunction(ito, al2o3, mode="flatband", ax=ax)
barrier = al2o3.e_cb - ito.e_cb
ax.annotate("", xy=(0.34, al2o3.e_cb), xytext=(0.34, ito.e_cb),
            arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#b3261e"))
ax.text(0.41, 0.5 * (al2o3.e_cb + ito.e_cb),
        f"e$^-$ injection barrier\n$\\approx$ {barrier:.2f} eV",
        fontsize=10, fontweight="bold", color="#b3261e", va="center")
ax.set_title("ITO / Al$_2$O$_3$: why the oxide gates a degenerate "
             "transparent conductor", fontsize=11, pad=14)
fig.tight_layout()
fig.savefig("ito_al2o3_alignment.svg")
fig.savefig("ito_al2o3_alignment.png", dpi=200)

print(f"electron injection barrier  chi_ITO - chi_Al2O3 = {barrier:+.2f} eV")
print(f"hole barrier (crystalline)  E_v(ITO) - E_v(Al2O3) = "
      f"{ito.e_vb - al2o3.e_vb:+.2f} eV")
print("note: amorphous ALD Al2O3 (Eg ~6.5 eV) trims the hole barrier to "
      "~1.2 eV; the 3 eV electron barrier is what the gate relies on")
print("wrote ito_al2o3_alignment.svg / .png")
