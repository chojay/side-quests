# Silicon vs 18 Fab Gases: 0 K vs 300 K Interface Reaction Energies

Silicon against the gases a wafer actually meets: Bosch-process etch and
passivation (SF6, C4F8), poly and oxide etch (Cl2, HBr, CF4, CHF3, C2F6,
BCl3), chamber cleans (NF3, ClF3, F2), MEMS release (XeF2), W-CVD precursor
(WF6), vapor HF, elemental halogens, and the two main etch byproducts (SiF4,
SiCl4). Ranked by 0 K reaction energy, then re-ranked with SISSO Gibbs
energies at 300 K.

**0 K source**: the 0 K summary produced by `run_interface_reactions.py` (GGA/GGA+U hull, MP2020)
**300 K source**: the same run with temperature 300 (SISSO Gibbs entries)
**Materials compared**: 18

## Key Observations

- **Average shift**: +0.1422 eV/atom (300 K vs 0 K)
- **Largest shift**: XeF2 (+1.6695 eV/atom) - the documented spurious-phase artifact, see below
- **Largest negative shift**: C4F8 (-0.1875 eV/atom)
- **Materials with rank change >= 3**: 4

## Comparison Table

| Rank (0K) | Material | E_0K (eV/atom) | E_300K (eV/atom) | ΔE (eV/atom) | Rank (300K) | Rank Δ |
|-----------|----------|---------------:|------------------:|---------------:|------------:|-------:|
| 1 | F2 | -3.4720 | -3.2595 | +0.2125 | 1 | 0 |
| 2 | NF3 | -2.5995 | -2.5958 | +0.0037 | 2 | 0 |
| 3 | ClF3 | -2.2720 | -2.1985 | +0.0735 | 3 | 0 |
| 4 | XeF2 ** | -1.8103 | -0.1408 | +1.6695 | 15 | -11 |
| 5 | Cl2 | -1.7420 | -1.2904 | +0.4516 | 6 | -1 |
| 6 | SF6 | -1.4264 | -1.5599 | -0.1335 | 4 | +2 |
| 7 | Br2 ** | -1.2610 | -0.5229 | +0.7381 | 12 | -5 |
| 8 | C4F8 ** | -1.1331 | -1.3206 | -0.1875 | 5 | +3 |
| 9 | CF4 | -1.0763 | -1.1884 | -0.1121 | 7 | +2 |
| 10 | C2F6 | -1.0197 | -1.1259 | -0.1062 | 8 | +2 |
| 11 | CHF3 | -0.7720 | -0.8564 | -0.0844 | 10 | +1 |
| 12 | WF6 ** | -0.7504 | -0.8864 | -0.1360 | 9 | +3 |
| 13 | HF | -0.4469 | -0.5456 | -0.0987 | 11 | +2 |
| 14 | HCl | -0.3013 | -0.2778 | +0.0235 | 13 | +1 |
| 15 | HBr | -0.2984 | -0.0435 | +0.2549 | 16 | -1 |
| 16 | BCl3 | -0.1680 | -0.1765 | -0.0085 | 14 | +2 |
| 17 | SiCl4 | 0.0000 | 0.0000 | +0.0000 | 17 | 0 |
| 18 | SiF4 | 0.0000 | 0.0000 | +0.0000 | 18 | 0 |

## Reading the outliers honestly

- **XeF2 (+1.67 eV/atom, rank 4 -> 15) is an artifact, not chemistry.** At
  300 K the Gibbs-converted entry set introduces a spurious "Si3F" phase that
  caps the reaction at -0.14 eV/atom; the 0 K result (Xe + SiF4 at -1.81,
  the reason XeF2 etches silicon spontaneously in MEMS release) is the
  physical one. This is the "SISSO is approximate for gases" caveat made
  concrete: the 300 K mode deserves the same skepticism it enables.
- **Br2's +0.74 shift** is dominated by the diatomic zero-correction
  convention: Br2 itself gets no Gibbs correction while its products do.
- **SiF4 and SiCl4 sit at exactly 0.000 at both temperatures** - silicon is
  stable against its own etch byproducts, a satisfying internal sanity check.
- Excluding the XeF2 artifact, the average shift is still ~15x larger than in
  a condensed-phase screening: gas-consuming reactions live or die by
  entropy, and 0 K rankings of etch chemistries deserve double-checking.

## Methodology Notes

- **0 K**: Ground-state DFT formation enthalpies with MP2020 compatibility corrections
- **300 K**: SISSO-based Gibbs free energy (Bartel et al. 2018) via `GibbsComputedStructureEntry`
- For 9 of the 18 gases (BCl3, HBr, HCl, HF, NF3, SF6, SiCl4, SiF4, WF6), NIST-JANAF experimental data replaces the SISSO descriptor
- SISSO was trained on crystalline solids - approximate for gas-phase molecules
- Elemental diatomics (F₂, Cl₂, Br₂) get 0 Gibbs correction by convention; gas-phase entropy NOT captured
- Minimum Gibbs temperature is 300 K (pymatgen constraint), not 298.15 K
