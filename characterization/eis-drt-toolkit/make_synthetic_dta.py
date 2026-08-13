#!/usr/bin/env python3
"""
Write a synthetic Gamry-format .DTA EIS spectrum so the DRT tools run with no real
instrument data.

The impedance is a Randles + two-ZARC model:

    Z(w) = Rs + R1 / (1 + (j w tau1)^a1) + R2 / (1 + (j w tau2)^a2)

swept over ~70 log-spaced frequencies with ~1% Gaussian noise (seeded). Two
well-separated ZARC time constants mean the DRT should recover two peaks at known
tau values, so the output can be checked against ground truth rather than eyeballed.

    python make_synthetic_dta.py --out examples/synthetic_randles_zarc.DTA

The .DTA layout follows what pyimpspec's Gamry parser needs: a `ZCURVE` line, a
`Pt ...` header, a `#` units line, then tab-delimited rows whose columns are
Pt, Time, Freq(Hz), Zreal(ohm), Zimag(ohm), ...
"""
import argparse
import numpy as np

# ground-truth model parameters
RS = 20.0
R1, TAU1, A1 = 80.0, 1e-4, 0.85     # high-frequency ZARC
R2, TAU2, A2 = 150.0, 1e-1, 0.75    # low-frequency ZARC


def zarc(w, R, tau, alpha):
    return R / (1.0 + (1j * w * tau) ** alpha)


def model_Z(freq):
    w = 2 * np.pi * freq
    return RS + zarc(w, R1, TAU1, A1) + zarc(w, R2, TAU2, A2)


def write_dta(path, freq, Z):
    npts = len(freq)
    mod = np.abs(Z)
    phz = np.degrees(np.angle(Z))
    lines = []
    lines.append("EXPLAIN")
    lines.append("TAG\tEISPOT")
    lines.append("TITLE\tLABEL\tSynthetic Randles + two-ZARC spectrum\tsynthetic, no real data")
    lines.append(f"ZCURVE\tTABLE\t{npts}")
    lines.append("\tPt\tTime\tFreq\tZreal\tZimag\tZsig\tZmod\tZphz\tIdc\tVdc\tIERange")
    lines.append("\t#\ts\tHz\tohm\tohm\tV\tohm\tdeg\tA\tV\t#")
    for i in range(npts):
        row = [i, f"{i*1.0:.4f}", f"{freq[i]:.6e}",
               f"{Z[i].real:.6e}", f"{Z[i].imag:.6e}",
               "0.0", f"{mod[i]:.6e}", f"{phz[i]:.4f}", "0.0", "0.0", "3"]
        lines.append("\t" + "\t".join(str(v) for v in row))
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Write a synthetic Gamry .DTA EIS spectrum.")
    ap.add_argument("--out", default="examples/synthetic_randles_zarc.DTA")
    ap.add_argument("--n", type=int, default=70, help="number of frequency points")
    ap.add_argument("--noise", type=float, default=0.01, help="relative Gaussian noise")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    freq = np.logspace(6, -2, args.n)          # 1 MHz down to 10 mHz
    Z = model_Z(freq)
    # ~1% relative Gaussian noise on each component
    Z = Z + (rng.normal(0, args.noise, args.n) * np.abs(Z)
             + 1j * rng.normal(0, args.noise, args.n) * np.abs(Z))

    write_dta(args.out, freq, Z)
    print(f"[DONE] wrote {args.out}  ({args.n} points, {freq[0]:.1e} .. {freq[-1]:.1e} Hz)")
    print(f"[GROUND TRUTH] DRT should show two peaks near "
          f"tau1 = {TAU1:.1e} s and tau2 = {TAU2:.1e} s")


if __name__ == "__main__":
    main()
