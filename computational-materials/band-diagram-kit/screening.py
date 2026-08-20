"""
screening.py - how wide is the space charge region at a junction?

Three length scales, three regimes:

1. Thomas-Fermi length (degenerate electronic screening; metals and
   transparent conductors like ITO at n ~ 1e20-1e21 cm^-3):

       lambda_TF = sqrt( 2 eps_r eps0 E_F / (3 e^2 n) ),
       E_F = (hbar^2 / 2m) (3 pi^2 n)^(2/3)

2. Debye length (linear screening, valid while e*phi << kT):

       lambda_D = sqrt( eps_r eps0 kB T / (e^2 N) )

3. Mott-Schottky depletion width (full depletion, valid when e*V_bi >> kT;
   the standard Schottky-diode and p-n junction result):

       W = sqrt( 2 eps_r eps0 V_bi / (e N) )  =  lambda_D * sqrt(2 e V_bi / kT)

The dominant knob is N: W scales as N^(-1/2), so doping sets the width far
more strongly than permittivity or built-in potential, which both enter under
square roots.

Validity floor: when a formula returns a length below the interatomic spacing
(~0.3-0.5 nm) the continuum picture has failed and the physical answer is
"about one atomic plane", not the printed number.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

E0 = 1.602176634e-19      # C
EPS0 = 8.8541878128e-12   # F/m
KB = 1.380649e-23         # J/K
HBAR = 1.054571817e-34    # J s
ME = 9.1093837015e-31     # kg


def debye_length(eps_r, n_cm3, T=298.0):
    """Linear (Debye) screening length [m]."""
    n = np.asarray(n_cm3, dtype=float) * 1e6
    return np.sqrt(eps_r * EPS0 * KB * T / (E0**2 * n))


def depletion_width(eps_r, v_bi, n_cm3):
    """Mott-Schottky depletion width [m] for band bending v_bi [V]."""
    n = np.asarray(n_cm3, dtype=float) * 1e6
    return np.sqrt(2.0 * eps_r * EPS0 * v_bi / (E0 * n))


def thomas_fermi_length(eps_r, n_cm3):
    """Degenerate electronic screening length [m], free-electron E_F."""
    n = np.asarray(n_cm3, dtype=float) * 1e6
    ef = (HBAR**2 / (2 * ME)) * (3 * np.pi**2 * n) ** (2.0 / 3.0)
    return np.sqrt(2.0 * eps_r * EPS0 * ef / (3.0 * E0**2 * n))


if __name__ == "__main__":
    EPS_SI = 11.7        # silicon
    EPS_ITO = 9.0        # ITO (reported ~8.9-9.3)
    N_ITO = 5e20         # degenerate transparent conductor [cm^-3]

    print("Si Schottky junction, V_bi = 0.6 V:")
    print(f"{'N_D (cm^-3)':>14} {'lambda_D (nm)':>15} {'W_dep (nm)':>12}")
    for n in [1e14, 1e15, 1e16, 1e17, 1e18, 1e19, 1e20]:
        ld = debye_length(EPS_SI, n) * 1e9
        w = depletion_width(EPS_SI, 0.6, n) * 1e9
        flag = "  <- degenerate: use Thomas-Fermi instead" if n >= 1e19 else ""
        print(f"{n:>14.0e} {ld:>15.1f} {w:>12.1f}{flag}")
    ltf = thomas_fermi_length(EPS_ITO, N_ITO) * 1e9
    print(f"\nITO contact (n = {N_ITO:.0e} cm^-3): lambda_TF = {ltf:.2f} nm")

    # ---- figure: W vs doping density ---------------------------------------
    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    N = np.logspace(14, 21, 300)

    for v, c in [(0.3, "#9ecae1"), (0.6, "#4292c6"), (1.0, "#08519c")]:
        ax.loglog(N, depletion_width(EPS_SI, v, N) * 1e9, color=c, lw=2.6,
                  label=f"depletion width, $V_{{bi}}$ = {v:.1f} V")
    ax.loglog(N, debye_length(EPS_SI, N) * 1e9, color="#6b46c1", lw=2.2,
              ls="--", label="Debye length (linear regime)")

    ax.axvspan(1e15, 1e18, color="#6b46c1", alpha=0.08, lw=0)
    ax.text(np.sqrt(1e15 * 1e18), 4500, "typical Si device doping",
            ha="center", va="top", fontsize=9.5, color="#6b46c1")

    ax.axhspan(0.3, 0.5, color="#777777", alpha=0.18, lw=0)
    ax.text(1.5e14, 0.38, "atomic spacing: continuum picture fails below here",
            fontsize=8.5, color="#555555", va="center")

    ax.plot(N_ITO, ltf, "o", color="#2b6cb0", ms=8, zorder=5)
    ax.annotate(f"degenerate ITO contact\n($\\lambda_{{TF}}$ = {ltf:.2f} nm)",
                xy=(N_ITO, ltf), xytext=(6e17, 0.09), fontsize=9,
                color="#2b6cb0",
                arrowprops=dict(arrowstyle="->", color="#2b6cb0", lw=1.2))

    w_mid = depletion_width(EPS_SI, 0.6, 1e16) * 1e9
    ax.plot(1e16, w_mid, "s", color="#c53030", ms=8, zorder=5)
    ax.annotate(f"$N_D = 10^{{16}}$ cm$^{{-3}}$, 0.6 V:\n"
                f"$W$ = {w_mid:.0f} nm (textbook Si Schottky)",
                xy=(1e16, w_mid * 0.8), xytext=(1.5e15, 2.5),
                ha="center", va="bottom", fontsize=9.5, fontweight="bold",
                color="#c53030",
                arrowprops=dict(arrowstyle="->", color="#c53030", lw=1.2))

    ax.set_xlabel("carrier / dopant density $N$ (cm$^{-3}$)", fontsize=11)
    ax.set_ylabel("screening / depletion width (nm)", fontsize=11)
    ax.set_title("Space charge width vs doping\n"
                 f"(curves: Si, $\\varepsilon_r$ = {EPS_SI:g}, widths scale as "
                 "$\\sqrt{\\varepsilon_r}$; dot: degenerate ITO)", fontsize=11)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.95)
    ax.grid(True, which="both", alpha=0.25)
    ax.set_ylim(0.03, 8000)
    fig.tight_layout()
    fig.savefig("depletion_width_vs_doping.svg")
    fig.savefig("depletion_width_vs_doping.png", dpi=200)
    print("wrote depletion_width_vs_doping.svg / .png")
