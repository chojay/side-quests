"""
band_diagram.py - heterojunction band-alignment diagrams with band bending.

The bent-band junction figure (CB/VB edges, space charge, built-in field) is
probably the most-drawn diagram in semiconductor interface work, and it is
almost always drawn by hand in a vector editor. This module draws it from an
explicit electrostatic construction instead, so every figure is regenerated
from numbers and the classic hand-drawing mistakes are structurally impossible.

CONSTRUCTION (Anderson rule + depletion approximation)
------------------------------------------------------
Inputs per material: CBM and VBM referenced to the vacuum level (eV, negative),
plus the bulk Fermi-level depth d_i = E_c - E_F (eV, positive; ~0.3-1.0 for a
doped/defective oxide, ~gap/2 for an intrinsic one).

  work function      W_i    = -E_c,i + d_i
  built-in potential V_bi   = W_left - W_right
  -> the LARGER-W side has the deeper E_F, so it ACCEPTS electrons and carries
     the NEGATIVE space charge; the other side is left POSITIVE.
  -> negative side: bands bend DOWN toward the interface (textbook p-side)
     positive side: bands bend UP   toward the interface (textbook n-side)
  -> built-in field E points from the + space charge to the - space charge.

Poisson in 1D with a box charge profile gives a parabolic potential inside each
depletion width w_i and flat bands outside.  Charge neutrality N1*w1 = N2*w2
makes the potential drop split as phi_i = V_bi * w_i / (w1 + w2).

Self-consistency check (worth knowing, it is what makes the picture correct):
with both bulks drawn at their own d_i above a COMMON flat E_F, the CB
discontinuity that falls out at the interface is

    E_c,right(0+) - E_c,left(0-) = (d_r + phi_r) - (d_l - phi_l)
                                 = (d_r - d_l) + V_bi
                                 = chi_left - chi_right          (Anderson offset)

i.e. the band offset is fixed by the electron affinities alone and does NOT
depend on the doping - exactly as it should.  Plotting the two bulk levels at
their vacuum-referenced values AND bending them by the full V_bi (a common
mistake in hand-drawn versions) double-counts the offset.

No dependency beyond numpy + matplotlib.
"""

from dataclasses import dataclass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


@dataclass(eq=False)          # identity hashing so a Material can key a dict
class Material:
    name: str                 # display label, LaTeX allowed
    e_cb: float               # CBM vs vacuum [eV], negative
    e_vb: float               # VBM vs vacuum [eV], negative
    color: str = "#3f7d20"
    d_fermi: float = 0.5      # bulk E_c - E_F [eV]; gap/2 if intrinsic
    width: float = 1.0        # drawn slab width [arb. units]
    w_dep: float = 0.38       # depletion width [same units]
    source: str = ""          # provenance tag, printed under the label
    e_cb_alt: tuple = None    # (lo, hi) disputed/alternative CBM range [eV]

    @property
    def gap(self):
        return self.e_cb - self.e_vb

    @property
    def work_function(self):
        return -self.e_cb + self.d_fermi


def _bend(x, x_if, w, phi, sign):
    """Parabolic band shift in the space-charge region.

    sign = +1 positively charged side (bands bend UP at the interface)
           -1 negatively charged side (bands bend DOWN at the interface)
    Zero slope at the bulk edge of the depletion region, full shift at x_if.
    """
    d = np.abs(x - x_if)
    u = np.where(d <= w, (w - d) / max(w, 1e-12), 0.0)
    return sign * phi * u ** 2


def heterojunction(left, right, mode="equilibrium", v_bi=None, ax=None,
                   n_charge=3, gap_arrows=True, field_label="Built-in Electric field",
                   panel=None, annotate="vacuum"):
    """Draw a two-material band diagram.

    mode = "equilibrium" : after contact.  E_F flat, band bending, space charge.
           "flatband"    : before contact.  Isolated slabs on a vacuum-referenced
                           axis (the Anderson starting point).
    v_bi : override the built-in potential [eV].  Default = W_left - W_right,
           i.e. driven by the d_fermi values.  Use a measured KPFM/UPS work
           function difference when you have one.
    annotate = "vacuum" prints the input CBM/VBM values (as the paper does),
               "relative" prints the plotted E - E_F values.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(5.4, 5.6))

    x_if = 0.0
    xl = np.linspace(-left.width, x_if, 400)
    xr = np.linspace(x_if, right.width, 400)

    if mode == "flatband":
        base = {id(left): (left.e_cb, left.e_vb),
                id(right): (right.e_cb, right.e_vb)}
        sgn = {id(left): 0, id(right): 0}
        phi = {id(left): 0.0, id(right): 0.0}
        ylab = "Energy vs. vacuum (eV)"
    else:
        if v_bi is None:
            v_bi = left.work_function - right.work_function
        neg = left if v_bi > 0 else right      # larger W accepts e-, goes negative
        pos = right if v_bi > 0 else left
        sgn = {id(neg): -1, id(pos): +1}
        wl, wr = left.w_dep, right.w_dep
        phi = {id(left): abs(v_bi) * wl / (wl + wr),
               id(right): abs(v_bi) * wr / (wl + wr)}
        base = {id(m): (m.d_fermi, m.d_fermi - m.gap) for m in (left, right)}
        ylab = "$E - E_F$ (eV)"

    # ---- band edges ---------------------------------------------------------
    for mat, x in ((left, xl), (right, xr)):
        cb0, vb0 = base[id(mat)]
        shift = _bend(x, x_if, mat.w_dep, phi[id(mat)], sgn[id(mat)])
        ax.plot(x, cb0 + shift, color=mat.color, lw=3.4, zorder=4,
                solid_capstyle="round")
        ax.plot(x, vb0 + shift, color=mat.color, lw=3.4, zorder=4,
                solid_capstyle="round")

        x0, x1 = x[0], x[-1]
        ax.axvspan(x0, x1, color=mat.color, alpha=0.09, lw=0, zorder=0)
        if mode != "flatband":
            scr = (x_if - mat.w_dep, x_if) if mat is left else (x_if, x_if + mat.w_dep)
            ax.axvspan(*scr, color=mat.color, alpha=0.20, lw=0, zorder=1)

        xt = x0 + 0.06 * (x1 - x0)
        cb_txt = f"{mat.e_cb:.2f} eV" if annotate == "vacuum" else f"{cb0:+.2f} eV"
        vb_txt = f"{mat.e_vb:.2f} eV" if annotate == "vacuum" else f"{vb0:+.2f} eV"
        ax.text(xt, cb0 + 0.13, cb_txt, fontsize=11, fontweight="bold", va="bottom")
        ax.text(xt, vb0 - 0.13, vb_txt, fontsize=11, fontweight="bold", va="top")
        ax.text(xt, cb0 - 0.26, "CB", color=mat.color, fontsize=13,
                fontweight="bold", va="top")
        ax.text(xt, vb0 + 0.26, "VB", color=mat.color, fontsize=13,
                fontweight="bold", va="bottom")

        if gap_arrows:
            xa = x0 + 0.60 * (x1 - x0)
            ax.annotate("", xy=(xa, cb0 - 0.04), xytext=(xa, vb0 + 0.04),
                        arrowprops=dict(arrowstyle="-|>", ls="--", lw=2.2,
                                        color="#1f3864", shrinkA=0, shrinkB=0),
                        zorder=5)

    tops = [base[id(m)][0] for m in (left, right)]
    bots = [base[id(m)][1] for m in (left, right)]
    ytop, ybot = max(tops), min(bots)

    # ---- space charge, field arrow, E_F ------------------------------------
    if mode != "flatband":
        ymid = 0.5 * (ytop + ybot)
        for mat in (left, right):
            xs = (x_if - 0.55 * mat.w_dep) if mat is left else (x_if + 0.55 * mat.w_dep)
            for yy in np.linspace(ymid - 0.16 * (ytop - ybot),
                                  ymid + 0.16 * (ytop - ybot), n_charge):
                ax.text(xs, yy, "+" if sgn[id(mat)] > 0 else "−", ha="center",
                        va="center", fontsize=18, fontweight="bold",
                        color="#222222", zorder=6)

        yarr = ytop + 1.00
        src = 0.85 * right.width if sgn[id(right)] > 0 else -0.85 * left.width
        dst = -0.85 * left.width if sgn[id(right)] > 0 else 0.85 * right.width
        ax.annotate("", xy=(dst, yarr), xytext=(src, yarr),
                    arrowprops=dict(arrowstyle="-|>,head_width=0.45,head_length=0.8",
                                    lw=7, color="#a8c8e8"), zorder=3)
        ax.text(0, yarr + 0.22, field_label, ha="center", va="bottom",
                fontsize=13, fontweight="bold", color="#3a3a3a")
        ax.axhline(0.0, ls=":", lw=1.7, color="#8a8a8a", zorder=2)
        ax.text(right.width * 0.97, 0.07, "$E_F$", fontsize=11, color="#6a6a6a",
                va="bottom", ha="right")
        ytop_lim = yarr + 0.75
        ax.set_title(f"$V_{{bi}}$ = {abs(v_bi):.2f} V   "
                     f"$\\Delta E_C$ = {right.e_cb - left.e_cb:+.2f} eV   "
                     f"$\\Delta E_V$ = {right.e_vb - left.e_vb:+.2f} eV",
                     fontsize=10.5, color="#555555", pad=10)
    else:
        ytop_lim = ytop + 0.9
        ax.set_title("before contact (isolated slabs)", fontsize=10.5,
                     color="#555555", pad=10)

    # ---- cosmetics ----------------------------------------------------------
    ax.set_xlim(-left.width, right.width)
    ax.set_ylim(ybot - 1.25, ytop_lim)
    ax.axvline(x_if, color="#ffffff", lw=1.3, zorder=2)
    for m, xc in ((left, -left.width / 2), (right, right.width / 2)):
        ax.text(xc, ybot - 1.05, m.name, ha="center", va="center", fontsize=15,
                fontweight="bold", color=m.color)
    if panel:
        ax.text(0.012, 0.985, panel, transform=ax.transAxes, fontsize=17,
                fontweight="bold", va="top")
    ax.set_ylabel(ylab, fontsize=11)
    ax.set_xticks([])
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    return ax


def stack_profile(layers, ax=None, barrier_ref=0, ylabel="Energy vs. vacuum (eV)"):
    """Physical multilayer stack (e.g. Si | SiO2 | HfO2), flat bands, Type-I check.

    Draws the layers left-to-right at their vacuum-referenced edges and
    annotates the two blocking barriers against layers[barrier_ref]:

        electron barrier  dEc = E_c(layer) - E_c(reference)   > 0 blocks e-
        hole barrier      dEv = E_v(reference) - E_v(layer)   > 0 blocks h+

    Both positive  <=>  Type-I (straddling)  <=>  the layer is a barrier
    to carriers in both directions.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(8.2, 5.2))
    ref = layers[barrier_ref]
    edges, x = [], 0.0
    for m in layers:
        edges.append((x, x + m.width))
        x += m.width
    for m, (x0, x1) in zip(layers, edges):
        ax.fill_between([x0, x1], m.e_vb, m.e_cb, color=m.color, alpha=0.20, lw=0)
        ax.plot([x0, x1], [m.e_cb] * 2, color=m.color, lw=3.4, solid_capstyle="butt")
        ax.plot([x0, x1], [m.e_vb] * 2, color=m.color, lw=3.4, solid_capstyle="butt")
        xc = 0.5 * (x0 + x1)
        ax.text(xc, m.e_cb + 0.18, f"{m.e_cb:.2f}", ha="center", va="bottom",
                fontsize=9.5, fontweight="bold")
        ax.text(xc, m.e_vb - 0.18, f"{m.e_vb:.2f}", ha="center", va="top",
                fontsize=9.5, fontweight="bold")
        ax.axvline(x1, color="#cccccc", lw=0.9, zorder=0)

    lo = min(m.e_vb for m in layers) - 4.0
    for m, (x0, x1) in zip(layers, edges):
        ax.text(0.5 * (x0 + x1), lo + 0.70, m.name, ha="center", va="bottom",
                fontsize=12, fontweight="bold", color=m.color)
        if m.source:
            ax.text(0.5 * (x0 + x1), lo + 0.30, m.source, ha="center", va="bottom",
                    fontsize=7.5, color="#888888", style="italic")

    # barriers annotated at each internal interface, vs the reference layer
    for m, (x0, x1) in zip(layers, edges):
        if m is ref:
            continue
        d_ec = m.e_cb - ref.e_cb
        d_ev = ref.e_vb - m.e_vb
        ok = "Type I" if (d_ec > 0 and d_ev > 0) else "not Type I"
        col = "#1a7a3a" if ok == "Type I" else "#b3261e"
        ax.text(0.5 * (x0 + x1), lo + 1.85,
                f"$\Delta E_C$ {d_ec:+.2f}\n$\Delta E_V$ {d_ev:+.2f}\n{ok}".replace("\\n", "\n"),
                ha="center", va="bottom", fontsize=8.5, color=col, linespacing=1.5)

    ax.axhline(ref.e_cb, ls="--", lw=1.1, color=ref.color, alpha=0.55, zorder=0)
    ax.axhline(ref.e_vb, ls="--", lw=1.1, color=ref.color, alpha=0.55, zorder=0)
    ax.set_xlim(0, x)
    ax.set_ylim(lo, max(m.e_cb for m in layers) + 1.0)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_xticks([])
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    return ax


def stack_alignment(materials, ax=None, ylabel="Energy vs. vacuum (eV)"):
    """Flat alignment chart for an N-layer stack (no bending) - the 'bapt' view.

    Useful for screening problems like the gate-dielectric offset question,
    where what matters is whether a candidate's CBM sits far enough above the
    channel's CBM (electron blocking) and its VBM below (hole blocking).
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(1.4 * len(materials) + 1.6, 4.8))
    for i, m in enumerate(materials):
        ax.bar(i, m.gap, bottom=m.e_vb, width=0.72, color=m.color, alpha=0.26,
               edgecolor=m.color, lw=2.4)
        ax.text(i, m.e_cb + 0.10, f"{m.e_cb:.2f}", ha="center", va="bottom",
                fontsize=9.5, fontweight="bold")
        ax.text(i, m.e_vb - 0.10, f"{m.e_vb:.2f}", ha="center", va="top",
                fontsize=9.5, fontweight="bold")
        ax.text(i, 0.5 * (m.e_cb + m.e_vb), f"{m.gap:.2f} eV", ha="center",
                va="center", fontsize=9, color=m.color)
        if m.e_cb_alt:
            lo, hi = sorted(m.e_cb_alt)
            ax.add_patch(plt.Rectangle((i - 0.36, lo), 0.72, hi - lo,
                                       facecolor="#b3261e", alpha=0.16,
                                       edgecolor="#b3261e", lw=1.0, ls="--",
                                       hatch="///", zorder=3))
    ax.set_xticks(range(len(materials)))
    ax.set_xticklabels([m.name for m in materials], fontsize=11,
                       fontweight="bold")
    _cb = [m.e_cb for m in materials] + [x for m in materials
                                         for x in (m.e_cb_alt or ())]
    _vb = [m.e_vb for m in materials]
    ax.set_ylim(min(_vb) - 1.5, max(_cb) + 0.9)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    return ax


if __name__ == "__main__":
    # Anderson's textbook system: an n-GaAs / N-AlGaAs isotype heterojunction.
    # Electron affinities and gaps from standard compilations: GaAs chi = 4.07,
    # Eg = 1.42; Al0.3Ga0.7As chi = 3.74, Eg = 1.80 (all eV).
    gaas = Material("n-GaAs", e_cb=-4.07, e_vb=-5.49, color="#2b6cb0",
                    d_fermi=0.10)
    algaas = Material(r"N-Al$_{0.3}$Ga$_{0.7}$As", e_cb=-3.74, e_vb=-5.54,
                      color="#c05621", d_fermi=0.10)

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.8))
    heterojunction(gaas, algaas, mode="flatband", ax=axes[0], panel="(a)")
    heterojunction(gaas, algaas, mode="equilibrium", ax=axes[1], panel="(b)",
                   field_label="Built-in field")
    fig.suptitle("n-GaAs / N-Al$_{0.3}$Ga$_{0.7}$As heterojunction "
                 "(Anderson construction)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig("gaas_algaas_junction.svg")
    fig.savefig("gaas_algaas_junction.png", dpi=200)

    for m in (gaas, algaas):
        print(f"{m.name:<26} chi={-m.e_cb:5.2f} eV  Eg={m.gap:5.2f} eV  "
              f"W={m.work_function:5.2f} eV")
    print(f"V_bi = {gaas.work_function - algaas.work_function:+.2f} V "
          f"(GaAs side negative: the electron transfer that modulation "
          f"doping exploits)")
    print(f"interface dEc = chi(GaAs) - chi(AlGaAs) = "
          f"{-gaas.e_cb - -algaas.e_cb:+.2f} eV (Anderson invariant)")
    print("wrote gaas_algaas_junction.svg / .png")
