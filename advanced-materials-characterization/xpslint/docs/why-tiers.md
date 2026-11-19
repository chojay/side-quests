# What Is Actually Known in XPS Peak Fitting

> [!NOTE]
> **The complaint this note answers**
> XPS peak fitting feels like black magic. Two competent people fit the same spectrum and get different answers, both defend their choices with citations, and neither can point to the step where the other went wrong.

## The Diagnosis

XPS does not feel arbitrary because the physics is unknown. It feels arbitrary because **three epistemically different kinds of claim are written in the same voice, in the same methods paragraph, with the same confidence.**

A typical methods sentence reads: *"Spectra were charge-referenced to adventitious carbon at 284.8 eV, fitted with 80:20 Gaussian-Lorentzian line shapes after Shirley background subtraction, constraining the Si 2p doublet to a 2:1 area ratio with 0.60 eV separation."*

Four claims, presented identically. In reality:

- The **2:1 ratio and 0.60 eV separation** are quantum mechanics. They are true on any instrument, in any lab, forever.
- The **Shirley background** is an admitted non-physical approximation that can produce completely wrong areas while looking statistically excellent.
- The **80:20 mix** is a software default with no derivation behind it.
- The **284.8 eV** is a number inherited from a calibration chain that most users never actually invoke, and which the recent literature has largely disqualified for insulators.

Once you sort every convention in the field into which tier it belongs to, the black magic evaporates. What is left is a short list of things that are genuinely true, a medium list of things you must measure on your own instrument, and a long list of things that are habits.

---

## Tier 1: Derivable. True regardless of instrument, sample, or operator.

These follow from quantum mechanics, mathematics, or counting statistics. Violating one is an error anywhere, and no experimental circumstance excuses it.

| Principle | Basis | Practical form |
| :--- | :--- | :--- |
| Spin-orbit doublet area ratio | State degeneracy `2j+1` | p = 1:2, d = 2:3, f = 3:4 |
| Spin-orbit splitting energy | Element-specific, measured and tabulated; weakly dependent on chemical state for light elements, but for transition-metal 2p state dependent by several tenths of an eV | Si 2p = 0.60 eV, Cu 2p = 19.75 eV (metal) |
| Lorentzian component exists | Finite core-hole lifetime, Heisenberg | A pure Gaussian peak is unphysical |
| Doniach-Sunjic asymmetry requires metallic DOS at the Fermi level | Many-body screening by conduction electrons | Asymmetry on a true insulator is fabrication |
| The DS integral diverges | Mathematics | DS cannot be used for quantification unless truncated (hence DSS) |
| Counting noise is Poissonian | Statistics | Sets a hard floor on how many components a spectrum can support |
| Stoichiometry must close | Conservation of atoms | An assigned compound requires its heteroatom, at the right corrected ratio |

> [!WARNING]
> **The one honest caveat in Tier 1**
> The `2j+1` ratio is the **statistical limit**. Real deviations exist: Coster-Kronig decay alters relative widths and can perturb intensities, and photoelectron diffraction in single crystals distorts ratios at specific geometries. The rule is not "the ratio is always 2:1." The rule is **"departure from 2:1 requires a named physical mechanism, not a better residual."** That distinction is the whole game.

---

## Tier 2: Measurable, but specific to your instrument and your sample.

This is the tier that causes the most confusion, because these quantities **are** knowable, and the literature quotes them as if they were constants. They are not constants. They are measurements that most papers never report.

| Quantity | Why it is not a constant | What you should actually do |
| :--- | :--- | :--- |
| Gaussian instrumental width | Depends on pass energy, source linewidth, analyzer, slits | Measure it: Ag 3d5/2 on clean silver, or the Fermi edge, at your working pass energy |
| Expected FWHM ranges (metal 0.4-1.0 eV, oxide 1.1-2.0 eV) | These envelopes are inherited heuristics from other people's instruments | Treat as a sanity envelope, not a constraint. Derive your own from your measured instrumental width plus tabulated lifetime widths |
| Analyzer transmission function | Instrument-specific, energy-dependent | Calibrate, or use the vendor function and say so |
| IMFP via TPP-2M | A predictive fit, not a measurement | Use it, but propagate its uncertainty (below) |
| RSFs | Scofield cross-sections are computed theory; applied RSFs fold in angular asymmetry, transmission, and IMFP. Vendor sets differ | State which set you used. Never mix sets |
| Sample work function | Material-specific | Measure by UPS if you intend to charge-reference correctly |

> [!IMPORTANT]
> **The number that recalibrates everything**
> **TPP-2M carries roughly 10% uncertainty.** Tanuma, Powell and Penn's own reliability study reports an RMS deviation of **11.0%** against reference IMFPs for ten materials, and a standard uncertainty of **9.2%** [T1][T2]. A later comparison for 41 elemental solids over 50 eV to 200 keV found an average RMS deviation of 11.9%, or 8.9% excluding diamond, graphite and cesium [T3].
>
> This means **an XPS atomic concentration can inherit an uncertainty of order 10% from the IMFP term alone** (concentrations depend on IMFP ratios, so errors that correlate between elements partly cancel), before RSF error, before transmission error, before fitting error. Reporting "23.4 at.% oxygen" implies a precision that the method cannot deliver. Reporting "23 +/- 3 at.%" is honest. Nearly nobody does this, and the resulting false precision is a large part of why XPS results from different groups appear irreconcilable.

---

## Tier 3: Convention, habit, and historical artifact.

These have weak, broken, or purely social justification. They are not necessarily wrong to use, but using them without declaring the choice is what makes the field feel like folklore.

### The 284.8 eV adventitious carbon reference

The single most revealing example, because the number has a **traceable and largely forgotten origin**.

- 284.6 eV was the recommended value under the older calibration convention where Cu 2p3/2 is set to 932.47 eV. 284.8 eV is the value under the newer convention where Cu 2p3/2 sits at 932.67 eV [C1]. The two numbers are not competing measurements. They are the same measurement expressed on two different energy scales, and citing one without its calibration chain is meaningless.
- ISO charge-referencing guidance recommends a **range of 284.6 to 285.2 eV**, not a point value [C1].
- Observed adventitious carbon C 1s positions vary by as much as **1.4 eV** across samples, and the binding energy correlates with the substrate work function such that their sum is roughly constant, which is the signature of vacuum-level rather than Fermi-level alignment [C2][C3].
- On native aluminum oxide the adventitious C 1s can appear near 286 eV [C2]. There is no universal value to reference to.

This is the clearest case of a Tier 3 habit that the community has treated as Tier 1 for fifty years. See Rule 7 in the [background survey](background-golden-rules.md).

### The 80:20 Gaussian-Lorentzian mix

There is no derivation that produces 80:20 or 90:10. They are round numbers that became software defaults and then became citations.

The physically correct construction is not a tunable mix at all. It is a **Voigt whose Gaussian width is your measured instrumental width (Tier 2) and whose Lorentzian width is the tabulated core-hole lifetime width for that transition (Tier 1)**. Done properly, the "mix" is not a free parameter. It is determined by two things you already know. Treating it as a knob to improve a residual is how a Tier 1/Tier 2 quantity gets demoted into folklore.

### The Shirley background

The most load-bearing item on this list, and the most uncomfortable.

- The Shirley and linear methods are **explicitly not based on physical models**. Shirley is an effective empirical approximation valid within a limited energy window [S1][S2].
- It is commonly misdescribed as accounting for inelastically scattered electrons, and it does not distinguish extrinsic from intrinsic background contributions [S1].
- Most importantly, comparative work against the improved Tougaard method found that **Shirley backgrounds produced completely wrong component areas in spite of sometimes rather satisfying residual functions and Abbe criteria** [S1].

> [!CAUTION]
> **The corollary that undermines a comfortable assumption**
> Rule 6 in the [background survey](background-golden-rules.md) presents the Abbe criterion and residual randomness as the objective test of a fit. The Shirley comparison shows that **a fit can pass residual randomness and Abbe testing while returning wrong areas.**
>
> Statistical validation is therefore **necessary but not sufficient**. It detects a missing component or a wrong line shape. It cannot detect a systematically wrong background, because the background error is smooth and absorbs into the peak areas without leaving structured residuals.
>
> The only checks that catch that failure mode are external to the fit: independent stoichiometric closure (Rule 1), agreement with a wider-window Tougaard treatment, or consistency across a sample series. This is the strongest argument in the whole subject for why quantitative cross-validation matters more than goodness-of-fit.

### Other Tier 3 habits worth naming

- Accepting a fit because the envelope "looks good" or the residual is visually flat.
- Assigning chemical states from handbook binding energies without matrix, referencing, or stoichiometric context. Database spreads for a given species are frequently wider than the shifts being claimed.
- Reporting component percentages to three or four significant figures (see the TPP-2M note above).
- Reusing a component count from a previous paper on a different material because it fit before.

---

## What This Reorganization Buys You

**1. A reading protocol for other people's papers.** Given a methods section, ask of every stated choice: is it Tier 1 (then it must be obeyed), Tier 2 (then was it measured, and is it reported?), or Tier 3 (then was the choice declared and justified?). Most methods sections collapse under this in one pass, which is consistent with the finding that major errors appear in roughly 40% of XPS papers that use peak fitting [5].

**2. A defensible protocol for your own work.** Obey Tier 1 absolutely. Measure Tier 2 once for your instrument and reuse it. Declare every Tier 3 choice explicitly rather than inheriting it silently.

**3. A better software design.** This is the part that shaped [xpslint](../README.md).

> [!TIP]
> **Rules should carry a tier, not just a severity**
> - A **Tier 1** violation is an unconditional error. No configuration should be able to downgrade it.
> - A **Tier 2** check is meaningless unless the instrument response has been declared. The honest output when it has not is **not** a warning. It is `cannot-check: instrumental width not declared`. That third outcome, distinct from pass and fail, is the single most useful thing such a tool can report, because it names exactly what a paper failed to disclose.
> - A **Tier 3** item is not a rule at all. It is a **prompt**: "you referenced to 284.8 eV. State your basis." It never fails a build. It forces a declaration.
>
> A checker that only emits pass and fail would itself be participating in the black magic, by implying it can adjudicate things that depend on unreported information. A checker that can say "I cannot know this, and neither can your reader" is doing something genuinely new.

---

## Sources

- [T1] Tanuma, Powell, Penn, *Calculation of electron inelastic mean free paths (IMFPs) VII. Reliability of the TPP-2M IMFP predictive equation*, Surface and Interface Analysis (2003), <https://onlinelibrary.wiley.com/doi/pdf/10.1002/sia.1526>
- [T2] NIST record for the same, <https://www.nist.gov/publications/calculation-electron-inelastic-mean-free-paths-imfps-vii-reliability-tpp-2m-imfp>
- [T3] Shinotsuka, Tanuma, Powell, Penn, *Calculations of electron inelastic mean free paths. X. Data for 41 elemental solids over the 50 eV to 200 keV range with the relativistic full Penn algorithm*, Surface and Interface Analysis 47, 871 (2015), <https://doi.org/10.1002/sia.5789>
- [S1] Hesse, Weiss, Szargan, Streubel, Denecke, *Comparative study of the modelling of the spectral background of photoelectron spectra with the Shirley and improved Tougaard methods*, Journal of Electron Spectroscopy and Related Phenomena 186, 44 (2013), <https://www.sciencedirect.com/science/article/abs/pii/S0368204813000224>
- [S2] Shirley Background, The XPS Library, <https://xpslibrary.com/shirley-background-2/>
- [S3] *Improved peak-fit procedure for XPS measurements of inhomogeneous samples: development of the advanced Tougaard background method*, <https://www.sciencedirect.com/science/article/abs/pii/S0368204815001437>
- [C1] Carbon, XPS Analysis, Cardiff University, <https://sites.cardiff.ac.uk/xpsaccess/reference/carbon/>
- [C2] *Defining the nature of adventitious carbon and improving its merit as a charge correction reference for XPS*, Applied Surface Science (2024), <https://www.sciencedirect.com/science/article/pii/S0169433224000333>
- [C3] *The same chemical state of carbon gives rise to two peaks in X-ray photoelectron spectroscopy*, Scientific Reports (2021), <https://www.nature.com/articles/s41598-021-90780-9>
- [5] Baer et al., reproducibility introduction, cited in the [background survey](background-golden-rules.md)
