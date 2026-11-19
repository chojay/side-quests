# xpslint roadmap

> [!NOTE]
> **One line**
> **`xpslint` is "ruff for XPS peak fits":** point it at a finished fit and it reports which established constraints the fit violates, which it cannot check because the instrument response was never declared, and which choices are conventions that need a stated basis.

## 1. What This Project Is Actually For

The motivation is not a deliverable. It is that XPS peak fitting feels like black magic, and that bothers me. See [why-tiers.md](why-tiers.md) for the diagnosis: the field mixes derivable physics, instrument-specific measurements, and inherited habit, and writes all three in the same confident voice.

**Writing a checker is the most effective way to stop a subject feeling arbitrary.** Encoding a craft into executable rules is unforgiving in a useful way. Every rule forces three questions that reading papers lets you dodge:

1. *What exactly is the claim?* A rule needs a threshold, so "the FWHM should be reasonable" has to become a number, a tolerance, and a conditional.
2. *What is it conditional on?* Writing `FW001` immediately exposes that the FWHM envelope depends on an instrumental width you have to measure, which is Tier 2, not Tier 1.
3. *How would I know it fired wrongly?* Which forces the synthetic test model, which forces you to be able to generate a correct spectrum from first principles, which is the real test of whether you understand it.

Tacit knowledge that survives being written as code is knowledge. Tacit knowledge that dissolves on contact was folklore. Either outcome is a win, and both are the point.

The secondary goal is to **use and adapt the existing state of the art rather than rebuild it.** Section 3 maps exactly what can be depended on, what can be ported, and what can only be reimplemented from published formulas.

If it later turns out to be useful to other people, that is upside. It is not the reason to build it.

---

## 2. Landscape and the Gap (verified 2026-08-17)

| Tool | What it is | What it does not do |
| :--- | :--- | :--- |
| lmfit | General non-linear least squares. Foundation of everything below. | Nothing XPS-specific. |
| lmfitxps | lmfit extension: `ShirleyBG`, `TougaardBG`, `SlopeBG`; `ConvGaussianDoniachSinglett`/`Dublett`; `FermiEdgeModel`. Native active background. | **No file I/O, no physics validation.** Constraints are only lmfit's generic `min`/`max`/`vary=False`. |
| KherveFitting | wxPython GUI over lmfitxps. Excel integration, Auto ID, PCA. Peer reviewed 2026. | GUI-first, not callable as a library. |
| PikaXPS | Cross-platform GUI, XPSPEAK 4.1 successor, **leave-one-out fit auditor**. | Nearest prior art on auditing, but it audits its own fits inside its own app. |
| POLEVAL | Jupyter-based HAXPES analysis, sequence constraints across spectra. | Constraint *application*, not *auditing*. |
| `pynxtools-xps` | FAIRmat reader: VAMAS ISO 14976 plus vendor formats into NeXus. | Pure I/O. A dependency, not a competitor. |

> [!TIP]
> **The gap**
> Every tool helps you **apply** constraints while fitting. None **audits a finished fit** as a portable artifact. Nothing answers: *"here is a CasaXPS export, which established constraints does it violate?"*

**Name check (PyPI JSON API, 2026-08-17):** `xpslint`, `xpsrules`, `goldenxps`, `xpsguard`, `xpsaudit`, `spectrolint`, `peakguard`, `xpscheck`, `pyxps`, `xpskit` all **available**. `xpsfit` taken.

---

## 3. Reuse vs Reimplement: the License Map

Licenses verified 2026-08-17 from PyPI metadata and repository `LICENSE` files.

| Package | License | How to use it |
| :--- | :--- | :--- |
| **lmfit** | BSD-3-Clause | **Depend.** Permissive, unambiguous. |
| **lmfitxps** | MIT (Hochhaus, 2023) | **Depend, and port freely if needed.** MIT means you may lift code with attribution. This is your background and line shape engine. |
| **LG4X** | MIT (Nakajima, 2020) | **Port freely.** Useful for GUI and preset-handling patterns. |
| **LG4X-V2** | MIT (Hochhaus, 2022) | **Port freely.** The most directly reusable full application. |
| **pynxtools-xps** | Apache-2.0 | **Depend.** Solves VAMAS ISO 14976 and vendor formats so you never write a parser. |
| **xps** (Dalhousie) | ISC | **Depend or vendor.** Permissive. Source of TPP-2M IMFP and RSF tables. |
| **KherveFitting** | **Dual-licensed:** GPL-3.0 or an alternative option | **Read the `LICENSE.md` before copying anything.** The dual option may permit permissive reuse, but it must be checked, not assumed. |
| **PikaXPS** | **GPL-3.0** | **Do not copy code into a permissive project.** Reimplement the leave-one-out auditor from its description. |
| **hyperspy** | **GPL-3.0** | **Do not vendor.** Reimplement Doniach-Sunjic from the 1970 published formula. |

> [!IMPORTANT]
> **The distinction that matters**
> **Algorithms and published formulas are free. Code carries a license.** Doniach-Sunjic, TPP-2M, Shirley, Tougaard and the leave-one-out audit are all published mathematics you may implement from the papers regardless of what license any implementation carries. What you cannot do is copy GPL-3 source into an MIT project.
>
> **How this was settled:** GPL-3 was a real option, and would have permitted vendoring from PikaXPS and hyperspy directly. It lost to MIT only because the parent repository is MIT, not because permissive licensing is the automatic default. Inheriting "MIT by default" without weighing it would be its own small piece of folklore, which is a bad look in a project about unexamined conventions. The cost of the choice is accepted explicitly: those two dependencies must be reimplemented from their published formulas rather than copied.

**Recommended composition:**
```
xpslint  (your rules, your reports, your CLI)
   ├── depends on  pynxtools-xps   (Apache-2.0)  -> file I/O
   ├── depends on  lmfit           (BSD-3)       -> ModelResult ingestion
   ├── depends on  lmfitxps        (MIT)         -> line shapes, backgrounds, synthetic generation
   ├── depends on  xps             (ISC)         -> TPP-2M, RSF tables
   └── reimplements from papers                  -> leave-one-out audit, Abbe criterion
```
Nothing in that stack requires writing a fitting engine or a file parser. The novel surface is only the rule layer, which is exactly the part worth understanding.

---

## 4. Scope

**In scope:** ingest a fit (VAMAS, CasaXPS export, lmfit `ModelResult`, or declarative TOML), evaluate the rule catalog, emit diagnostics, ship reference data, generate synthetic spectra for testing.

**Explicitly out of scope:** optimization or fitting (delegate to lmfit/lmfitxps), a GUI, chemical state assignment databases, depth profiling and ARXPS reconstruction.

> [!WARNING]
> **The one real risk**
> Drifting into writing another fitting engine. It is a year of work, it competes with peer reviewed tools, and it buries the only novel idea. Every feature request gets tested against: *does this move a peak?* If yes, reject.

---

## 5. The Rule Catalog

Rules carry a **tier** as well as a severity, which is the design change that falls directly out of [why-tiers.md](why-tiers.md):

- **Tier 1** violations are unconditional errors. No configuration may downgrade them.
- **Tier 2** checks require declared instrument metadata. **Decided 2026-08-17: without it the result is `cannot-check`, never a warning.** See section 5.1.
- **Tier 3** items never fail. They **prompt for a declaration**.

| Code | Rule | Tier | Default severity |
| :--- | :--- | :--- | :--- |
| **SO001** | Doublet area ratio deviates from `2j+1` multiplicity (p 1:2, d 2:3, f 3:4) | 1 | error |
| **SO002** | Doublet separation outside the reference value for that element and orbital | 1 | error |
| **SO003** | Doublet FWHMs forced equal where Coster-Kronig broadening is expected | 1 | warning |
| **LS001** | Doniach-Sunjic asymmetry applied to a declared insulator | 1 | error |
| **LS002** | Pure Gaussian line shape (zero Lorentzian contribution) | 1 | error |
| **LS003** | Un-truncated DS profile used for quantification (divergent integral) | 1 | error |
| **ST001** | Assigned compound's heteroatom absent from the survey scan | 1 | error |
| **ST002** | Matrix-corrected atomic ratio deviates from assigned stoichiometry | 1 | error |
| **DQ001** | Component count exceeds what the counting statistics can support | 1 | warning |
| **LS004** | Gaussian-Lorentzian mix declared as a free parameter rather than derived from measured instrumental width and tabulated lifetime width | 2 | warning |
| **FW001** | Component FWHM outside the envelope implied by instrumental width plus lifetime width | 2 | warning |
| **FW002** | Chemically similar components in one spectrum have inconsistent FWHM | 2 | warning |
| **FW003** | FWHM drifts across a spectrum sequence without declared justification | 2 | info |
| **FW004** | One component more than 2x the width of its neighbors (the "filler peak") | 2 | error |
| **ST003** | Quantification without RSF, transmission function, or IMFP correction | 2 | error |
| **ST004** | Atomic percentages reported to a precision finer than the ~10% TPP-2M uncertainty allows | 2 | warning |
| **BG001** | Static background endpoints clip the peak envelope | 2 | error |
| **RS001** | Abbe criterion below threshold: residuals are structured | 2 | error |
| **RS002** | Leave-one-out test shows a component is statistically unnecessary | 2 | warning |
| **RS003** | Reduced chi-squared far below 1 (overfit) or far above 1 (underfit) | 2 | warning |
| **BG002** | Shirley background used for quantification without cross-check against a wider-window Tougaard treatment | 3 | prompt |
| **BG003** | Background model choice not declared | 3 | prompt |
| **CA001** | Adventitious carbon referenced to a point value on an insulator without a measured work function | 3 | prompt |
| **CA002** | Charge referencing method not declared, or reference value cited without its calibration chain | 3 | prompt |
| **DQ002** | Energy step size too coarse relative to the narrowest fitted FWHM | 2 | warning |

> [!NOTE]
> **Why BG002 is Tier 3 and RS001 is Tier 2**
> This pairing is the sharpest thing the tool encodes. Shirley backgrounds have been shown to produce **completely wrong component areas while still yielding satisfying residuals and Abbe criteria**. So the residual check (RS001) can pass on a fit that the background check should have caught. RS001 is therefore necessary but not sufficient, and BG002 cannot be adjudicated statistically at all. It can only be prompted for. Encoding that asymmetry honestly is more valuable than any individual rule.

Design details worth building:
- Each diagnostic carries `code`, `tier`, `severity`, `message`, `component_id`, `observed`, `expected`, `citation`.
- `# noqa: SO001` suppression with a **mandatory justification string**. An unjustified suppression becomes its own diagnostic.
- Configuration lives in `[tool.xpslint]` in `pyproject.toml`, mirroring ruff.

### 5.1 The Outcome Model (decided)

A missing instrument declaration yields `cannot-check`, not a warning. Warnings are claims about the fit; this is a claim about the *metadata*, and conflating them would let the tool imply it had adjudicated something it could not see.

Five outcomes, not two:

| Outcome | Meaning | Counts toward |
| :--- | :--- | :--- |
| `pass` | Rule ran, fit satisfies it | coverage |
| `fail` | Rule ran, fit violates it | coverage, exit code |
| `cannot-check` | Rule could not run: required metadata absent | **uncovered** |
| `not-applicable` | Rule does not apply to this fit (e.g. `SO001` on an s-orbital singlet) | neither |
| `prompt` | Tier 3: a declaration is requested, nothing is adjudicated | neither |

> [!WARNING]
> **`not-applicable` must never be folded into `cannot-check`**
> They look similar and mean opposite things. `not-applicable` is a complete answer; `cannot-check` is an absent one. Merging them corrupts the coverage figure below, which is the whole payoff of this design.

**Driven automatically by `requires`.** The engine compares each rule's `requires` set against the declared metadata and emits `cannot-check` without the rule body ever executing. No rule author writes this logic, so it cannot be forgotten in a new rule.

**Coverage is the headline metric.** By analogy with test coverage:

```
coverage = (pass + fail) / (pass + fail + cannot-check)
```

This is the number that matters, because it measures precisely the thing that makes XPS feel like black magic: **how much of this fit is even checkable from what was reported.** A fit with zero errors and 20% coverage has not been validated. It has been left unexamined, and now says so out loud.

**Exit codes:**

| Condition | Default | Under `--strict` |
| :--- | :--- | :--- |
| Any `fail` | `1` | `1` |
| Only `cannot-check` | `0` | `1` |
| Coverage below `--min-coverage` | `0` | `1` |
| Clean | `0` | `0` |

The honest default does create one failure mode: a fit declaring no metadata at all passes trivially, because every rule degrades to `cannot-check`. Three mitigations, in order of importance:

1. **The coverage figure is always printed**, so a trivial pass is visibly a 0% pass. Silence is not available.
2. `--min-coverage 0.8` for anyone who wants a real gate, without ever converting missing metadata into a false claim about the fit.
3. **Every `cannot-check` names the exact missing key and how to supply it.** An unactionable `cannot-check` is just noise, and noise gets ignored, which would waste the whole design.

The plan is to declare metadata once per instrument in `[tool.xpslint.instrument]` and reuse it across every fit (today it sits in each fit file's `[instrument]` table), so the friction is one-time setup rather than per-analysis burden. That is deliberate: it makes the path of least resistance the thing the field currently fails to do.

> [!TIP]
> **The unexpected payoff**
> **The `cannot-check` list is a methods-section checklist.** Every unchecked rule names something that was not reported. Run it against your own draft and the output is, quite literally, the list of disclosures the paper is missing. That may end up more useful than the pass/fail rules.

---

## 6. Architecture

**Target architecture.** Files marked `(planned)` do not exist yet.

```
src/xpslint/
  models.py             # frozen dataclasses: Spectrum, Component, FitResult, Instrument (Doublet planned)
  config.py             # [tool.xpslint] parsing, tolerances, severity overrides
  io/
    vamas.py            # via pynxtools-xps (planned)
    casa.py             # CasaXPS export adapter (planned)
    lmfit_adapter.py    # wrap an lmfit ModelResult (planned)
    declarative.py      # TOML fit description (used by the test suite)
  rules/
    base.py             # Rule protocol, Tier, Severity, Diagnostic, registry
    spin_orbit.py  fwhm.py  lineshape.py  background.py
    stoichiometry.py  referencing.py  residuals.py (planned)  dataquality.py (planned)
  refdata/
    spin_orbit.toml     # separations and ratios per element/orbital
    lifetimes.toml      # tabulated core-hole lifetime widths
    rsf.toml            # Scofield and Wagner sets, kept separate (planned)
    imfp.py             # TPP-2M, returning value AND uncertainty (planned)
  synth.py              # forward model: spectra from known ground truth
  report/               # terminal (plain text today; rich planned), json, html (planned)
  cli.py
```

```python
class Rule(Protocol):
    code: str
    tier: Tier
    severity: Severity
    citation: str
    requires: frozenset[str]  # instrument metadata keys needed

    def check(self, fit: FitResult, cfg: Config) -> Iterator[Diagnostic]: ...
```

`requires` is what makes `cannot-check` automatic rather than hand-written: if the declared metadata does not cover a rule's requirements, the engine emits `cannot-check` without the rule ever running.

Planned: rules self-register via an entry point group (`xpslint.rules`) so lab-specific rule packs can be added without forking. Today they register with a decorator in `rules/base.py`.

**Target CLI output:**
```
$ xpslint check data/TiO2_Ti2p.vms

data/TiO2_Ti2p.vms:Ti2p_component_2
  error       SO001  [T1] Doublet area ratio 1.71 deviates from theoretical 2.00
                           cite: (2j+1) degeneracy; Major et al. JVST A 38, 061203 (2020)
  error       LS001  [T1] Doniach-Sunjic asymmetry (alpha=0.08) on a declared insulator
  cannot-check FW001 [T2] requires instrument.gaussian_width
                           set [tool.xpslint.instrument] gaussian_width = <eV at your pass energy>
                           measure on Ag 3d5/2 (clean silver) or the Fermi edge
  prompt      CA001  [T3] referenced to 284.8 eV without a measured work function.
                           State the basis. ISO recommends a range, not a point value.

1 file: 2 failed, 9 passed, 4 unchecked, 2 n/a, 1 prompt
coverage: 11/15 checks (73%)
exit 1
```

---

## 7. Build and Tooling

| Concern | Choice |
| :--- | :--- |
| Package manager / env | `uv` |
| Build backend | `hatchling` |
| Config | `pyproject.toml` only |
| Lint + format | `ruff` (fitting, given the subject) |
| Types | `mypy --strict` now, Astral's `ty` on the roadmap |
| Tests | `pytest` + `pytest-cov`; `hypothesis` planned (listed in the dev extras, no property tests yet) |
| Versioning | Static `version` in `pyproject.toml` today; `hatch-vcs`, tag-derived, planned |
| CI | Planned, not set up: ruff, mypy, pytest over Python 3.11-3.13. Today these run by hand. |
| Release | Not set up: no package is published; install from this folder. |
| Docs | Planned: MkDocs Material + mkdocstrings, one page per rule code |

The per-rule documentation pages are the real artifact. Each states the physics, the tier, the failure mode, a figure of a violating fit, and the citation. That page set is a restatement of the [background survey](background-golden-rules.md) in a form that has been forced through executable precision.

---

## 8. Testing: the part that proves you understood it

The hard question for any validator is *how do you know the validator is right?* The answer is a synthetic forward model, and building it is where the actual learning happens: you cannot generate a physically correct spectrum without knowing precisely what "correct" means.

1. `synth.py` builds a spectrum from ground truth: declared components, known line shapes, known doublet ratios, a known background, Poisson noise at a specified count rate.
2. **Negative controls:** valid fits must produce zero diagnostics. A false positive is the worst possible bug for a tool whose purpose is trust.
3. **Injected violations:** perturb exactly one parameter, assert exactly one rule code fires.
4. **`cannot-check` coverage:** strip instrument metadata, assert Tier 2 rules degrade to `cannot-check` rather than silently passing. This is the easiest behavior to get wrong.
5. **Property-based (`hypothesis`):** across randomized elements, orbitals, count rates and component counts, assert that valid fits never error and that every rule is deterministic and side-effect free.
6. **Golden-file tests** for report rendering.

---

## 9. Milestones, ordered by how much each teaches

| # | Deliverable | Status |
| :--- | :--- | :--- |
| **M0** | `uv` + hatchling + ruff + mypy strict + pytest. | **done** 2026-08-17 (run locally; this repository has no CI) |
| **M1** | `models.py`, `Rule` protocol with tiers, Tier 1 rules `SO001` `SO002` `LS001` `LS002` `LS003` `ST001`. Declarative TOML input, terminal and JSON output. | **done** |
| **M2** | `synth.py` forward model, negative controls, injected-violation tests, `cannot-check` coverage tests, malformed-config tests. 106 tests, 96% coverage (local run, 2026-11-19). | **done** |
| **M3** | Tier 2 machinery: `requires`, engine-level `cannot-check`, coverage metric, `FW001` deriving its envelope from measured instrumental width plus tabulated lifetime width. *Remaining:* TPP-2M with propagated uncertainty, RSF tables, `ST004`. | **partial** |
| **M4** | Remaining rules. Tier 3 prompts `BG002` `BG003` `CA001` `CA002` shipped. *Remaining:* `SO003`, `FW002`-`FW004`, `RS001`-`RS003`, `BG001`, `DQ001`-`DQ002`. | **partial** |
| **M5** | Real I/O via `pynxtools-xps` and a CasaXPS adapter. | not started |
| **M6** | HTML report, `noqa` with mandatory justification, docs with a page per rule. | not started |

> [!NOTE]
> **What exists as of 2026-11-18**
> Eleven rules across all three tiers, all five outcomes reachable, zero runtime dependencies, ruff and mypy-strict clean. The clean example reports 19/19 coverage and exits 0; the questionable example reports 7 failures at 75% coverage and exits 1; the clean example with its `[instrument]` and `[survey]` tables removed reports 9/19 (47%) and still exits 0, which is the honest default working as intended.
>
> **The reference data is the main thing standing between this and real use.** `refdata/spin_orbit.toml` and `refdata/lifetimes.toml` are provisional and want checking against primary sources. Absent entries produce `cannot-check` rather than a guess, so the tables are safe to ship incomplete and can be filled in element by element.

The package version is `v0.1.0` with eleven rules. A small finished thing beats a large unfinished one.

---

## 10. Open Decisions

1. ~~**License.**~~ **Settled: MIT**, inherited from the parent repository. The consequence is deliberate and worth restating: GPL-3 code from PikaXPS and hyperspy cannot be vendored, so their published algorithms have to be reimplemented from the papers. See section 3.
2. **First input format:** declarative TOML is far faster to build and test. VAMAS at M5.
3. ~~**Tier 2 default posture.**~~ **Decided 2026-08-17: `cannot-check`.** Specified in section 5.1. Remaining sub-question: what should `--min-coverage` default to, if anything? Recommendation is no default, since an arbitrary threshold would be exactly the kind of unjustified round number this project exists to eliminate.
4. **Scope of the reference data:** curating spin-orbit separations and lifetime widths for the whole periodic table is a large data-entry task. Start with the elements the bundled examples and tests use (Si, O, C, Ti, Al, Hf, N), then add elements one at a time as each is verified.

---

## Sources

Ecosystem, packaging, and epistemic sources are collected in [why-tiers.md](why-tiers.md) and the [background survey](background-golden-rules.md). Licenses in section 3 were verified 2026-08-17 against the PyPI JSON API and each repository's `LICENSE` file.

- lmfitxps, <https://github.com/Julian-Hochhaus/lmfitxps> (MIT)
- LG4X-V2, <https://github.com/Julian-Hochhaus/LG4X-V2> (MIT)
- LG4X, <https://github.com/hidecode221b/LG4X> (MIT)
- KherveFitting, <https://github.com/KherveFitting/KherveFitting> (dual-licensed, check `LICENSE.md`)
- PikaXPS, <https://github.com/contact993/pikaxps> (GPL-3.0)
- pynxtools-xps, <https://github.com/FAIRmat-NFDI/pynxtools-xps> (Apache-2.0)
- xps (Dalhousie), <https://gitlab.com/ddkn/xps> (ISC)
- lmfit, <https://github.com/lmfit/lmfit-py> (BSD-3-Clause)
