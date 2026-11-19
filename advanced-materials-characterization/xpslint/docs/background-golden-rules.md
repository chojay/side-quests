# Advanced Methodologies and Foundational Principles in X-Ray Photoelectron Spectroscopy Peak Fitting

This is the background literature review that [xpslint](../README.md) encodes into
executable rules. Each rule in the project README's catalog traces to one of the
numbered rules below (several codes can share one rule; Rule 6 has no shipped rule yet). For why those rules are sorted into three tiers rather than
treated as one flat list, see [why-tiers.md](why-tiers.md).

> [!WARNING]
> **Read this as a survey, not as an authority**
> Two honest caveats about this document. First, every equation in the original was an
> embedded image object, so the conversion to markdown lost them; all inline math here
> was **reconstructed from surrounding context** (`2j + 1`, `chi-squared`, `Si 2p3/2`,
> `SiO2`, work function `Phi`). The reconstructions are unambiguous but unverified.
> Second, it was assembled with heavy AI research assistance, and it shows: the
> reference list runs to about 50 entries while only 26 are actually cited in the body. The
> uncited remainder is provenance noise from automated searching, not evidence anyone
> read them. Treat the citations as leads to check, not as claims already verified.
> The specific numbers that *have* been checked against their cited sources are the ones
> quoted in [why-tiers.md](why-tiers.md); most are primary papers, and the calibration
> values come from a university XPS reference page.

X-ray Photoelectron Spectroscopy (XPS) represents one of the most critical analytical techniques in contemporary materials science, surface chemistry, and semiconductor metrology. By harnessing the photoelectric effect, XPS facilitates the precise determination of elemental composition, empirical formulas, and the localized chemical and electronic states of materials [1]. The utility of XPS, however, is heavily dependent on the extraction of high-fidelity chemical information from core-level photoemission spectra. This extraction process requires peak fitting, a sophisticated mathematical deconvolution that separates overlapping photoemission signals originating from diverse chemical environments [4].

Despite the foundational importance of XPS, the scientific community is currently grappling with a severe reproducibility crisis regarding spectral interpretation. Exhaustive reviews of published literature indicate that approximately 60% of papers utilizing XPS rely on peak fitting, and critically, major errors are identified in roughly 40% of these specific analyses [5]. This equates to nearly 30% of all published XPS literature containing significant flaws [5]. The most pervasive errors originate from a fundamental misunderstanding of the physics governing photoemission, manifesting as the use of mathematically convenient but physically impossible full width at half maximum (FWHM) values, the omission of spin-orbit splitting constraints, the misapplication of background subtraction algorithms, and the arbitrary assignment of chemical states that violate stoichiometric logic [4].

Because the non-linear least-squares minimization algorithms utilized in curve fitting traverse complex, multi-dimensional parameter spaces, it is entirely possible to achieve a mathematically perfect fit that represents an abject physical impossibility [4]. To circumvent these local mathematical minima and extract valid physicochemical parameters, analysts must rigidly adhere to established best practices. This report details the definitive "golden rules" of XPS peak fitting, illustrates their practical application in complex heterogeneous interfaces such as the silicon/silicon dioxide system, and critically evaluates the modern computational landscape, comparing the commercial standard CasaXPS against the rapidly evolving ecosystem of open-source Python modules.

## The Pre-Fitting Imperative: Experimental Design and Data Integrity

The golden rules of peak fitting cannot salvage inherently flawed data. Optimal peak fitting begins long before the mathematical optimization is initiated, specifically during the experimental design and data acquisition phases [7]. The fundamental rule is that peak fitting should only be applied to spectra acquired under strictly controlled and understood physical conditions [9].

The primary consideration is the acquisition of adequate statistics. The signal-to-noise ratio of a narrow scan dictates the reliability of the optimization algorithm; spectra with poor statistics will cause fitting algorithms to chase random noise fluctuations, resulting in arbitrary synthetic peak generation [4]. Analysts must ensure that step sizes and dwell times are optimized to produce highly defined spectral envelopes. Furthermore, differential charging across insulating or heterogeneous samples must be minimized using low-energy electron and ion flood guns, as uncontrolled charging introduces asymmetric broadening that can be erroneously interpreted as novel chemical states [7].

Finally, analysts must conduct rigorous literature searches regarding expected core-level linewidths, cross-sections, and multiplet splitting behaviors for their specific materials prior to constructing a fitting model [9]. If reference materials are unavailable, isoelectronic species or elements within the same periodic column should be evaluated to establish baseline expectations for chemical reactivity and spectral line shapes [9].

## The Golden Rules of XPS Peak Fitting

Peak fitting is an exercise in applied constraints. Without constraints, synthetic models lack physical meaning [6]. The following rules represent the immutable physical and mathematical tenets that must govern every XPS optimization protocol.

### Rule 1: Stoichiometric Validation and Global Chemical Consistency

The most egregious error in XPS peak fitting is the isolated deconvolution of a single core-level spectrum without corroborating the proposed chemical states against the broader chemical environment of the sample [6]. The first golden rule dictates that a synthetic model must reflect the total physical and stoichiometric reality of the material.

If an analyst assigns a high-binding-energy component in a core-level spectrum to a specific compound, the corresponding heteroatom must be present in the survey scan, and its corresponding narrow scan must contain a chemically shifted peak that mirrors this assignment [9]. For example, if a component in the Si 2p spectrum is assigned to silicon dioxide (SiO2), the fundamental stoichiometry dictates that there must be an O 1s peak corresponding to the Si-O bond [10].

This relationship extends beyond qualitative identification into strict quantitative validation. The integrated area of the assigned Si 2p peak (A_Si) and the O 1s peak (A_O) must reflect the 1:2 atomic ratio of SiO2. However, raw areas cannot be directly compared. They must be normalized using their respective relative sensitivity factors (RSF), the transmission function of the specific hemispherical analyzer, and the inelastic mean free path (IMFP) of the photoelectrons as they travel through the specific sample matrix [4]. The relationship must satisfy the following proportionality (reconstructed from the source equation image):

```
   A_Si / (RSF_Si * T(E_Si) * lambda_Si)        1
  ----------------------------------------  =  ---
   A_O  / (RSF_O  * T(E_O)  * lambda_O )        2
```

The IMFP can be accurately calculated using the Tanuma-Powell-Penn (TPP-2M) equations, which account for the kinetic energy of the specific photoelectrons and the bulk density and valence electron configuration of the matrix [11]. If the matrix-corrected atomic ratio deviates significantly from the expected stoichiometry (for example, yielding a 1:1 or 1:4 ratio), the fitting model is invalid. Such deviations indicate that the background subtraction has clipped the signal, overlapping contaminant species have been misidentified, or the assigned synthetic peaks represent a physical impossibility [4].

### Rule 2: Strict Application of Spin-Orbit Coupling Constraints

For all photoelectrons emitted from electronic orbitals with an angular momentum quantum number `l >= 1` (specifically p, d, and f orbitals), the coupling between the electron's spin and its orbital angular momentum splits the energy level into two distinct states, resulting in a doublet peak in the XPS spectrum (for example, 2p3/2 and 2p1/2) [4]. The relationship between the components of these doublets is dictated by immutable laws of quantum mechanics, and these relationships must be locked as absolute constraints during peak fitting [6].

The intensity ratio of the doublet components is determined by the degeneracy of the states, given by the multiplicity `2j + 1`. Consequently, the area ratios for spin-orbit doublets are fundamentally fixed and must never be allowed to float freely during algorithmic optimization.

| Orbital | Angular Momentum (l) | Spin-Orbit States (j) | Required Area Ratio |
| :------ | :------------------- | :-------------------- | :------------------ |
| s | 0 | 1/2 | None (singlet) |
| p | 1 | 1/2, 3/2 | 1:2 (p1/2 : p3/2) |
| d | 2 | 3/2, 5/2 | 2:3 (d3/2 : d5/2) |
| f | 3 | 5/2, 7/2 | 3:4 (f5/2 : f7/2) |

*Table 1: Theoretical area ratios for spin-orbit doublets based on state multiplicity [10]. Note that the higher `j` value corresponds to a lower binding energy.*

In addition to area constraints, the binding energy separation (`delta E_SO`) between the doublet components is an intrinsic, invariant property of the specific element and its oxidation state [10]. For instance, the Si 2p doublet separation is universally 0.60 eV, while the Cu 2p separation is approximately 20.0 eV [10]. This separation must be constrained based on empirical data from high-resolution reference databases.

While it is standard practice to constrain the FWHM of both doublet components to be identical, analysts must account for the quantum mechanical phenomenon of Coster-Kronig transitions [15]. A Coster-Kronig transition is a highly rapid, non-radiative Auger-like process where the core hole in the lower-`j` state (for example the 2p1/2 level) is filled by an electron from the higher-`j` state (the 2p3/2 level) of the same principal shell [15]. This rapid transition drastically decreases the lifetime of the lower-`j` core hole. According to the Heisenberg uncertainty principle (`delta E * delta tau >= hbar / 2`), a shorter lifetime (`tau`) dictates a larger uncertainty in energy (`delta E`), which manifests as a physically broader peak [15]. Therefore, in specific transition metals (such as titanium 2p), the 2p1/2 peak will legitimately exhibit a larger FWHM than the 2p3/2 peak. Analysts must anticipate this inherent asymmetry in linewidth and apply specialized, distinct FWHM constraints rather than forcing an artificial equality [15].

### Rule 3: Rational FWHM Constraints and Phonon Broadening Mechanics

The Full Width at Half Maximum (FWHM) of a synthetic peak provides profound insights into the chemical, physical, and structural environment of the atom [4]. The observed experimental FWHM is mathematically a convolution of several discrete physical broadening mechanisms: the natural inherent linewidth of the atomic core level (a Lorentzian function dictated by core-hole lifetime), the broadening caused by the instrumental resolution (a Gaussian function dictated by the X-ray source linewidth and analyzer pass energy), and inhomogeneous broadening mechanisms such as phonon interactions and structural disorder [6].

Because instrumental broadening remains entirely constant for a given spectrometer configuration, pass energy, and monochromatic X-ray source, any synthetic peaks arising from identical elements in similar chemical environments must exhibit nearly identical FWHM values [5]. The most common indicator of a poor XPS fit in the literature is the presence of an extraordinarily wide synthetic peak deployed merely to fill an unassigned region in the residual envelope [5].

To prevent overfitting, the third golden rule requires that analysts firmly constrain FWHM ranges based on the physical state of the material:

- Highly ordered, crystalline pure metals typically exhibit narrow FWHM values ranging from 0.4 eV to 1.0 eV, often clustering between 0.6 eV and 0.8 eV [10].
- Metal oxides and organic polymers inherently display broader FWHM values, ranging from 1.1 eV to 2.0 eV (typically 1.3 eV to 1.6 eV) [10]. This broadening is driven by the excitation of multiple, closely spaced vibrational states during the photoemission event (phonon broadening) and the varied bond angles inherent in amorphous or semi-crystalline matrices [9].
- Hydroxides and sulfates often stretch the upper limits of FWHM, occasionally ranging up to 1.8 eV due to extensive hydrogen bonding networks and varying localized dipole environments [10].

Any deviation from these standard FWHM ranges must be explicitly justified by the analyst, citing specific physical mechanisms such as severe differential charging, intentional multiplet splitting in transition metals, or verified overlapping satellite structures [9].

### Rule 4: The Strategic Selection of Complex Line Shapes

The assumption that photoemission peaks are purely Gaussian is a fundamental error [6]. The true intrinsic line shape of an ejected photoelectron represents the finite lifetime of the resulting core hole, generating a Lorentzian profile [6]. Conversely, the broadening introduced by the instrumental apparatus and macroscopic inhomogeneous sample charging introduces a Gaussian profile. Therefore, the optimal line shape for a standard insulating sample is the mathematical convolution of these two profiles, known as the Voigt function, or its computationally efficient approximation, the pseudo-Voigt (which relies on a Gaussian-Lorentzian sum or product) [4]. For standard inorganic oxides and polymers, an 80:20 or 90:10 Gaussian-to-Lorentzian mix is generally prescribed [10].

Electrically conductive materials, such as transition metals, graphitic carbons, and highly doped semiconductors, introduce an extraordinary complication that invalidates the symmetric Voigt profile [17]. When a core hole is created in a metal, the sudden change in the local potential interacts strongly with the continuum of empty conduction band states located immediately above the Fermi level [17]. This interaction generates a cascade of low-energy electron-hole pairs, draining a minute fraction of kinetic energy from the escaping primary photoelectron [19]. In the resulting energy spectrum, this energy loss manifests as an asymmetric tail extending toward higher binding energies [17].

This many-body interaction is rigorously modeled utilizing the Doniach-Sunjic (DS) line shape [19]. The DS profile is defined by an asymmetry parameter (`alpha`), often termed the singularity index, which dictates the severity of the high-binding-energy tail [19]. While the DS profile perfectly describes the core-hole-conduction-band coupling, it suffers from a fatal mathematical flaw: the function decays so slowly that its integral, the total peak area, reaches infinity, rendering absolute quantitative area analysis mathematically impossible unless the function is arbitrarily truncated [16].

To solve this critical defect, modern XPS protocols advocate for the Doniach-Sunjic-Shirley (DSS) line shape [16]. The DSS line shape merges the fundamental DS profile with a Shirley-type energy loss background mechanism [16]. The addition of the Shirley response truncates the infinite asymmetric tail, yielding a physically accurate, asymmetric peak shape that integrates to a finite, quantifiable area [16].

The absolute golden rule regarding line shapes is one of exclusivity: **Doniach-Sunjic asymmetry parameters must never be applied to insulators** [10]. Because true insulators lack a density of states at the Fermi level, the physical mechanism for conduction band coupling does not exist. The artificial addition of asymmetry to an insulator peak to improve a residual score is a mathematical fabrication that destroys the physicochemical validity of the model [10].

### Rule 5: The Active Background Methodology

Quantitative analysis in XPS is fundamentally reliant on the accurate subtraction of the background signal, which consists primarily of inelastically scattered extrinsic photoelectrons [4]. The traditional, "static" approach to background subtraction requires the analyst to visually define two distinct endpoints on either side of a spectral feature and subtract a predetermined baseline, usually a Shirley, Tougaard, or simple linear function, prior to executing the peak fitting algorithm [24].

This static methodology is inherently flawed and highly susceptible to user bias. If a broad, complex peak or an extended asymmetric tail crosses the boundaries of the manually selected endpoints, the static background will artificially clip the peak envelope, leading to severe underestimations of atomic concentrations [25]. Furthermore, static backgrounds force an averaged, constant scattering dynamic across the entire spectral window, which contradicts the physical reality that different chemical species exhibit different inelastic scattering behaviors [25].

The modern standard, championed extensively by A. Herrera-Gomez, is the **Active Background Approach** [24]. In the active methodology, the background is not predetermined or subtracted prior to fitting. Instead, the mathematical parameters governing the background's intensity, shape, and endpoints are treated as floating variables and are optimized simultaneously alongside the synthetic photoemission peaks during the iterative least-squares minimization [25].

The active approach allows the background to dynamically evolve as the peak model refines itself, entirely eliminating manual endpoint selection bias [25]. Furthermore, it permits the construction of complex, hybrid backgrounds. A prominent example is the Shirley-Vegh-Salvi-Castle (SVSC) background [24]. When deployed actively, the SVSC formalism allows the intensity of the Shirley-step to vary independently across different overlapping peaks within the same spectrum, providing a phenomenologically accurate representation of inelastic energy loss without requiring iterative convergence loops [24].

### Rule 6: Statistical Validation of the Mathematical Minimum

Visual inspection of a fitted envelope is subjective and routinely leads to overfitting, a scenario where an analyst introduces an excess of unconstrained parameters until the synthetic curve perfectly masks the experimental data, irrespective of chemical reality [4]. Objective statistical validation is mandatory.

The optimization algorithms (such as Levenberg-Marquardt) evaluate fit quality by minimizing the chi-squared (`chi^2`) metric [4]. However, a low `chi^2` value alone does not guarantee a physically meaningful fit [4]. Analysts must rigorously evaluate the normalized residuals, the point-by-point difference between the experimental data and the total synthetic envelope [29]. The golden rule mandates that normalized residual plots must be visibly presented alongside every published fit [29].

The randomness of these residuals must be quantified using the Abbe criterion [29]. The Abbe criterion tests for systematic spatial structures within the residual noise. If the calculated Abbe value approaches 0, it signifies that the residuals are highly correlated (non-random). This indicates a systemic failure in the model, such as an incorrect background, an inappropriate line shape, or an entirely omitted chemical state [29]. Conversely, if the Abbe criterion approaches 1, the residuals represent purely random instrumental and counting noise, statistically confirming that the applied physical model has successfully captured all genuine structural features within the spectrum [29].

### Rule 7: Overcoming the Adventitious Carbon Referencing Fallacy

A rapidly emerging paradigm shift in XPS analysis concerns the calibration and referencing of the binding energy scale. Since the inception of XPS, the global community has almost universally relied on adventitious carbon (AdC), a ubiquitous layer of atmospheric hydrocarbon contamination, for charge referencing [30]. The standard practice involves shifting the entire acquired energy scale such that the C-C/C-H component of the AdC C 1s peak aligns to an arbitrary, fixed value, typically 284.8 eV [30].

Exhaustive, recent metrological studies conducted by Greczynski and Hultman have definitively proven that this historical practice is fundamentally flawed when applied to electrically insulating samples [30]. Analyzing a dataset of over 360 distinct thin-film specimens encompassing oxides, nitrides, carbides, and borides, they demonstrated that the adventitious carbon layer does not align to the Fermi level of the sample; rather, it aligns to the sample's vacuum level [31].

Because the AdC layer aligns to the vacuum level, the true binding energy of the C 1s peak dynamically shifts in direct correlation with the intrinsic work function (`Phi`) of the underlying substrate [31]. Consequently, arbitrarily forcing the C 1s peak to 284.8 eV across all materials artificially distorts the binding energy scale by up to several electron volts, entirely destroying the reliability of chemical state assignments [31].

The new golden rule for referencing dictates that utilizing adventitious carbon as an absolute standard for insulators must be abandoned [30]. If AdC must be used, the sample's specific work function must be independently measured (for example via ultraviolet photoelectron spectroscopy), and the C 1s peak must be calibrated relative to that specific `Phi` value [31]. Alternatively, analysts must rely on internal referencing using known stoichiometric bulk peaks from within the sample matrix or employ sophisticated noble-metal decoration techniques to establish a reliable, grounded Fermi edge [30].

## Case Study: Deconvoluting the Silicon and Silicon Dioxide Interface

To crystallize the application of these golden rules, one must examine the peak fitting of a native oxide layer on a silicon wafer, a quintessential and highly complex XPS analytical scenario [14]. The Si 2p core level requires meticulous attention to quantum spin-orbit constraints, suboxide chemical shifts, precise FWHM variances, and macroscopic overlayer thickness calculations [14].

### Structural Deconvolution and Suboxide Binding Energies

The Si 2p signal represents electrons ejected from the principal `n = 2` shell with an angular momentum `l = 1`. Following Rule 2, this necessitates a spin-orbit doublet comprising the 2p3/2 and 2p1/2 states [14]. Any synthetic model evaluating silicon must enforce a strict 2:1 area ratio between the 2p3/2 and 2p1/2 components, and fix the energy separation at precisely 0.60 eV [10].

The transition from the bulk silicon substrate to a fully oxidized silica surface is not an abrupt stoichiometric boundary; it involves a gradient of intermediate, low-valent oxidation states known as suboxides [14]. Adhering to Rule 1 and Rule 4, the Si 2p region must be deconvoluted into the following potential species, mapping the discrete 2p3/2 binding energy positions [14]:

| Oxidation State | Chemical Species | Typical Si 2p3/2 Binding Energy (eV) | Expected FWHM Characteristics |
| :-------------- | :--------------- | :----------------------------------- | :---------------------------- |
| **Si(0)** | Bulk elemental silicon | 99.4 - 99.5 | Narrow (~0.6 - 0.8 eV) |
| Si(1+) | Suboxide (Si2O) | 100.4 | Intermediate |
| Si(2+) | Suboxide (SiO) | 101.1 - 101.7 | Intermediate |
| Si(3+) | Suboxide (Si2O3) | 102.3 - 103.0 | Intermediate |
| Si(4+) | Silicon dioxide (SiO2) | 103.3 - 103.9 | Broad (~1.3 - 1.8 eV) |

*Table 2: Characterization of the Si 2p spectral region outlining progressive oxidation states, binding energy shifts, and structural broadening mechanics [14].*

The elemental silicon (Si(0)) peak at 99.4 eV will possess a highly narrow FWHM, reflective of the highly ordered, defect-free crystalline lattice of the bulk wafer [35]. Conversely, the fully oxidized SiO2 peak, located near 103.3 eV, will exhibit a significantly broader FWHM [35]. This broadening is not an error; it is a physical manifestation of the amorphous nature of the native oxide layer, which introduces localized dielectric disorder, varied Si-O-Si bond angles, and complex phonon broadening interactions during photoionization [9].

### Oxide Thickness Estimations and Heteroatom Verification

Beyond identifying chemical states, the intensities of these fitted peaks can be utilized to calculate the absolute thickness of the silicon dioxide overlayer. Because photoelectrons undergo inelastic scattering as they traverse the oxide layer, the intensity of the bulk Si(0) signal is exponentially attenuated compared to the surface Si(4+) signal [35]. By comparing the integrated areas of the accurately fitted Si(0) and SiO2 peaks, and incorporating the IMFP of Si 2p electrons traveling through SiO2, the overlayer thickness can be quantified with sub-nanometer precision [35].

However, the validity of these SiO2 and suboxide assignments hinges entirely on Rule 1: heteroatom stoichiometry. If the 103.3 eV peak is confirmed as SiO2, the analyst must transition to the O 1s spectral region. A robust O 1s peak must be identified between 532.0 and 533.0 eV [10]. The relative atomic concentrations derived from the SiO2 and O 1s peaks, after strict corrections for their respective RSF and kinetic-energy-dependent IMFP variations, must yield a highly accurate 1:2 ratio. Any deviance implies that the active background subtraction was mishandled, or that exogenous silicates or organic silicone contaminants have been erroneously convoluted into the native oxide fit.

## Computational Ecosystems: CasaXPS versus Open-Source Python Architectures

The rigorous execution of these golden rules requires highly sophisticated computational software. For decades, the commercial application CasaXPS has reigned as the undisputed industry standard for spectral deconvolution [16]. However, the modernization of scientific computing via the Python programming language has birthed a highly robust, transparent, and rapidly expanding ecosystem of open-source XPS analysis modules [41].

A frequent query among modern metrologists and academic researchers is whether an open-source Python module can be considered "better" than CasaXPS. The answer requires a nuanced evaluation of algorithmic transparency, reproducibility, and batch automation capabilities.

### The Legacy and Power of CasaXPS

CasaXPS is a comprehensive, graphical-user-interface (GUI) driven program [41]. Its primary strength lies in its unparalleled, polymorphic library of built-in line shapes [16]. CasaXPS natively supports standard pseudo-Voigt profiles, the fundamental Doniach-Sunjic (DS) profile, and heavily specialized asymmetric shapes such as the LA series and the highly advanced Doniach-Sunjic-Shirley (DSS) profile [16]. For analyzing complex transition metals where precise manipulation of the singularity index and asymmetric tails is required, CasaXPS remains a formidable tool [16]. Furthermore, it provides built-in mechanisms for generating uniqueness plots, allowing analysts to manually verify the robustness of their chi-squared local minima [9].

**The limitations of CasaXPS:** the primary critique of CasaXPS is rooted in the reproducibility crisis [5]. Because it is a closed-source, GUI-dependent application, reproducing a complex multi-peak fit requires an analyst to meticulously document a labyrinth of manual click-and-drag operations, endpoint selections, and arbitrary parameter constraints [5]. In the hands of a novice, this manual operation is highly susceptible to user bias [5]. Furthermore, applying identical constraints across large datasets, such as depth profiles or time-resolved *in-situ* oxidation studies, can be tedious and prone to human error without the use of complex, proprietary macro scripting.

### The Python Paradigm Shift: Algorithmic Transparency

The open-source Python ecosystem leverages object-oriented programming to construct highly programmatic, reproducible, and transparent data analysis pipelines [1]. Because the analysis script itself acts as an immutable, auditable record of all mathematical constraints, background parameters, and optimization limits, it naturally combats the reproducibility crisis [41]. The foundation of nearly all Python-based XPS fitting is lmfit, a highly robust non-linear least-squares minimization library that utilizes the Levenberg-Marquardt algorithm to navigate parameter spaces [23].

Several advanced packages have evolved from this foundation, addressing specific requirements of the golden rules:

#### 1. lmfitxps and the LG4X Lineage

The lmfitxps package serves as a direct extension of lmfit, tailored explicitly for XPS [42]. Its most profound analytical advantage is its native, programmatic implementation of the **Active Background Approach** (Herrera-Gomez method) [25]. Unlike legacy software where static backgrounds are often the default behavior, lmfitxps treats Shirley, Tougaard, and step functions as active mathematical models, convoluted directly with the peak signals during optimization to prevent signal clipping [42].

Because purely programmatic fitting can alienate users accustomed to visual manipulation, a series of powerful GUIs have been developed over the lmfitxps architecture:

- **LG4X (versions 1 and 2):** initially conceptualized by H. Nakajima and substantially advanced by J.A. Hochhaus (LG4X-V2), these GUI tools wrap lmfitxps within a PyQt5 interface [46]. They facilitate the active background approach and allow users to seamlessly import and export constraint presets, streamlining repetitive batch fitting procedures [46].
- **KherveFitting (LG4X-V3):** developed by Gwilherm Kerherve at Imperial College London, this iteration introduces a wxPython-based interface, deep Excel integration, and an automatic peak identification (Auto ID) system [48]. It includes specialized toolkits for Fermi edge fitting, principal component analysis (PCA) for complex datasets, and advanced Tougaard/Raman cross-section optimization [48].

#### 2. PikaXPS and the "Fit Auditor"

PikaXPS positions itself as a modern, cross-platform successor to legacy freeware like XPSPEAK 4.1 [43]. Its defining innovation is a **built-in fit auditor** [43]. In standard software, users can easily violate the golden rules by mathematically overfitting data, adding arbitrary, unconstrained synthetic peaks until the residual Abbe criterion appears perfect [9]. PikaXPS solves this crisis utilizing a statistical leave-one-out cross-validation test [43]. The auditor programmatically removes individual synthetic peaks and recalculates the chi-squared optimization, explicitly flagging instances where a peak is mathematically unnecessary. This algorithmically enforces the physical rule of parsimony [10].

#### 3. POLEVAL for HAXPES and Sequence Constraints

For high-throughput environments such as hard X-ray photoelectron spectroscopy (HAXPES) at synchrotron facilities, the POLEVAL toolbox offers collaborative, Jupyter Notebook-based XPS analysis [41]. Its paramount advantage is the programmatic enforcement of "sequence constraints" [41]. If an analyst acquires 50 sequential spectra during an *in-situ* thermal annealing study, POLEVAL can mathematically lock FWHM and spin-orbit binding energy separations globally across the entire sequence [41]. This ensures that the optimization algorithm utilizes prior physical knowledge from the entire dataset, preventing individual noisy spectra from dropping into errant local minima [41].

#### 4. Specialized Toolkits: xps, EMpeaksR, and HyperSpy

The Python ecosystem also excels in highly specialized niche calculations:

- **xps (Dalhousie):** this package provides vital tools for stoichiometric validation, housing databases for empirical atomic sensitivity factors (Wagner/Scofield) and algorithms to calculate the IMFP utilizing the exact TPP-2M equations, necessary for accurate matrix factor corrections [11].
- **EMpeaksR:** utilizes a highly advanced spectrum-adapted expectation-conditional maximization (ECM) algorithm to fit Doniach-Sunjic-Gauss mixture models, allowing rigorous evaluation of the asymmetry parameter (`alpha`) independent of standard Levenberg-Marquardt constraints [51].
- **hyperspy:** while traditionally used for electron microscopy, it contains highly robust 1D signal processing modules, including a native Doniach-Sunjic lineshape generator capable of complex multidimensional photoemission data visualization [19].

### Comparative Synthesis: Which is "Better"?

Defining an absolute superiority between CasaXPS and Python is subjective and heavily dependent on the operational context of the laboratory.

| Analytical Capability | CasaXPS (commercial standard) | Open-source Python ecosystem (lmfitxps, PikaXPS, POLEVAL) |
| :-------------------- | :---------------------------- | :-------------------------------------------------------- |
| **Reproducibility and auditing** | Manual logging required; highly vulnerable to operator reporting errors [5]. | Flawless, immutable code-based audit trails via Jupyter Notebooks [41]. |
| **Line shape library** | Unmatched breadth (DS, DSS, LA, pseudo-Voigt) integrated seamlessly [16]. | Highly robust, but highly specialized asymmetric shapes (like the DSS) require custom mathematical definition [19]. |
| **Background optimization** | Supports both active and static (iterative Shirley, Tougaard). | Native, programmatic active background optimization explicitly built into lmfitxps [42]. |
| **Overfitting prevention** | Relies entirely on the user's manual evaluation of uniqueness plots and Abbe criteria [9]. | Automated and algorithmically enforced via the PikaXPS leave-one-out fit auditor [43]. |
| **Batch/sequence processing** | Attainable via macros, but cumbersome for complex multi-parameter constraints. | Structurally superior. Modules like POLEVAL globally lock constraints across vast, multi-dimensional datasets [41]. |

*Table 3: Comparative assessment of XPS analytical software platforms against the requirements of modern metrological best practices.*

For an analyst processing single, highly anomalous spectra that require proprietary line shapes and profound manual manipulation, CasaXPS remains the supreme instrument. However, for analysts prioritizing rigorous reproducibility, the batch processing of large-scale datasets, algorithmic transparency, and statistical auditing against overfitting, the open-source Python ecosystem is structurally superior. By forcing the analyst to explicitly declare their mathematical constraints in open code, Python effectively hardcodes the golden rules into the analytical workflow.

## Conclusion

The structural integrity of X-ray photoelectron spectroscopy relies entirely on the stringent intersection of mathematical rigor and physical chemistry applied during peak fitting. The reproducibility crisis currently undermining modern surface science literature is not an indictment of XPS instrumentation; rather, it is a catastrophic failure of analysts to adhere to the foundational golden rules of spectral deconvolution.

Every synthetic peak deployed in a mathematical model must represent a tangible physical state corroborated by the broader stoichiometry of the sample. The arbitrary assignment of a silicon dioxide peak demands the rigorous, matrix-corrected validation of an oxygen peak at a precise atomic ratio. Spin-orbit doublet peaks must be inextricably constrained by their quantum mechanical area ratios and energy separations. FWHM values must reflect the physical realities of core-hole lifetimes, instrumental resolution, and phonon broadening, rather than being exploited as mathematical conveniences to artificially flatten residual errors. Backgrounds must be applied using an active methodology to prevent signal clipping, and complex line shapes must match the conductivity of the material, strictly restricting Doniach-Sunjic asymmetry parameters to metals. Finally, the analytical community must urgently discard the reliance on adventitious carbon referencing for insulators, recognizing that sample work functions dynamically alter binding energy alignment.

While legacy applications like CasaXPS remain monumental tools in the field, the transition toward open-source Python architectures such as lmfitxps, PikaXPS, and POLEVAL represents a vital evolution in surface science metrology. By substituting opaque manual GUI operations with transparent code-driven analysis, statistical fit auditors, and globally enforced programmatic constraints, these modern analytical modules naturally enforce the golden rules, ensuring that XPS remains a reliable, irreproachable pillar of materials characterization for the future.

## Works cited

1. Case Study - X-ray Photoelectron Spectroscopy (XPS), python-scripting-experimental documentation, MolSSI Education, <https://education.molssi.org/python-scripting-experimental/xps_processing.html>
2. Modeling X-ray Photoelectron Spectroscopy of Macromolecules Using GW, <https://pubs.acs.org/doi/10.1021/acs.jpclett.2c01935>
3. Towards XPS 2.0: Standing on the shoulders of Nobel Laureates, WISE, <https://wise-materials.org/external/towards-xps-2-0-standing-on-the-shoulders-of-nobel-laureates/>
4. Practical guide for curve fitting in X-ray photoelectron spectroscopy, ResearchGate, <https://www.researchgate.net/publication/344519439_Practical_guide_for_curve_fitting_in_X-ray_photoelectron_spectroscopy>
5. Introduction to topical collection: Reproducibility challenges and solutions with a focus on guides to XPS analysis, <https://ywcmatsci.yale.edu/sites/default/files/files/2021%20Baer%20JVST%20A%20-%20Intro%20to%20Reproducibility%20Challenges%20and%20Solutions%20XPS.pdf>
6. (PDF) Guide to XPS data analysis: Applying appropriate constraints to synthetic peaks in XPS peak fitting, ResearchGate, <https://www.researchgate.net/publication/364817694_Guide_to_XPS_data_analysis_Applying_appropriate_constraints_to_synthetic_peaks_in_XPS_peak_fitting>
7. Practical Guides for X-Ray Photoelectron Spectroscopy (XPS): First Steps in planning, conducting and reporting XPS measurements, PMC, <https://pmc.ncbi.nlm.nih.gov/articles/PMC6774202/>
8. A step-by-step guide to perform x-ray photoelectron spectroscopy, AIP Publishing, <https://pubs.aip.org/aip/jap/article/132/1/011101/2837063/A-step-by-step-guide-to-perform-x-ray>
9. Good Practices for XPS Peak Fitting, II, ResearchGate, <https://www.researchgate.net/publication/305653584_Good_Practices_for_XPS_Peak_Fitting_II>
10. Content, Methods, Prep, and Layout, The International XPS Spectra-Base of Monochromatic XPS Reference Spectra, <https://xpsdatabase.com/content-methods-prep-and-layout/>
11. xps, PyPI, <https://pypi.org/project/xps/>
12. Practical guides for x-ray photoelectron spectroscopy: Quantitative XPS, SciSpace, <https://scispace.com/papers/practical-guides-for-x-ray-photoelectron-spectroscopy-2metq4iuxa>
13. Practical guide for curve fitting in x-ray photoelectron spectroscopy, AIP Publishing, <https://pubs.aip.org/avs/jva/article/38/6/061203/1023652/Practical-guide-for-curve-fitting-in-x-ray>
14. Tunable Synaptic Characteristics of a Ti/TiO2/Si Memory Device for Reservoir Computing, ACS Applied Materials and Interfaces, <https://pubs.acs.org/doi/10.1021/acsami.1c06618>
15. Coster-Kronig peak broadening, HarwellXPS Guru, <https://www.harwellxps.guru/xpskb/coster-kronig-peak-broadening/>
16. Definition of a New (Doniach-Sunjic-Shirley) Peak Shape for Fitting Asymmetric Signals, OSTI.GOV, <https://www.osti.gov/servlets/purl/1976397>
17. Asymmetries in Transition Metal XPS Spectra: Metal Nanoparticle Structure, and Interaction with the Graphene-Structured Substrate Surface, ResearchGate, <https://www.researchgate.net/publication/26812154_Asymmetries_in_Transition_Metal_XPS_Spectra_Metal_Nanoparticle_Structure_and_Interaction_with_the_Graphene-Structured_Substrate_Surface>
18. Characterization of Carbon Nanostructures by Photoelectron Spectroscopies, PMC, NIH, <https://pmc.ncbi.nlm.nih.gov/articles/PMC9267296/>
19. hyperspy._components.doniach module, <https://hyperspy.org/hyperspy-doc/v1.6/api/hyperspy._components.doniach.html>
20. Limitations in Determining Oxidation States in Condensed Matter at the Subnanometric Scale, PMC, <https://pmc.ncbi.nlm.nih.gov/articles/PMC12203604/>
21. A method for the experimental determination of, AIP Publishing, <https://pubs.aip.org/aip/jap/article-pdf/doi/10.1063/1.1948508/14953026/014908_1_online.pdf>
22. Definition of a new (Doniach-Sunjic-Shirley) peak shape for fitting asymmetric signals applied to reduced graphene oxide/graphene oxide XPS spectra, ResearchGate, <https://www.researchgate.net/publication/355447633_Definition_of_a_new_Doniach-Sunjic-Shirley_peak_shape_for_fitting_asymmetric_signals_applied_to_reduced_graphene_oxidegraphene_oxide_XPS_spectra>
23. Alberto Herrera-Gomez Ph.D. Professor at Center for Research and Advanced Studies of the National Polytechnic Institute, ResearchGate, <https://www.researchgate.net/profile/Alberto-Herrera-Gomez>
24. A (Very Incomplete) Report of AVS 2015, Physical Electronics, <https://www.phi.com/assets/documents/Published-Papers/TOF-SIMS/vacuumtech-and-coating-january-2016-3d-fib-tof-of-or.pdf>
25. The active background method in XPS data peak fitting, Cinvestav Qro, <https://cia.qro.cinvestav.mx/~aherrera/reportesInternos/activeBackground.pdf>
26. AAnalyzer Manual, <https://xpsoasis.org/aanalyzer_manual>
27. The active background method in XPS data peak-fitting, Semantic Scholar, <https://www.semanticscholar.org/paper/The-active-background-method-in-XPS-data-Herrera%E2%80%90Gomez/1eb6cd6d60a73ebd1e781f1b7a6ab7b358e88b0a>
28. Characterizing the Intrinsic Background in XPS Using the Narrow-Shirley Approach, PMC, <https://pmc.ncbi.nlm.nih.gov/articles/PMC12746447/>
29. Linford, Best Practices for XPS Peak Fitting (slides, 21 December 2015; read from a third-party copy, link omitted)
30. XPS problem with calibration, Linkoping University, <https://liu.se/en/news-item/xps-problem-with-calibration>
31. (PDF) Binding energy referencing in X-ray photoelectron spectroscopy: Expanded data set confirms that adventitious carbon aligns to the sample vacuum level, ResearchGate, <https://www.researchgate.net/publication/382399907_Binding_energy_referencing_in_X-ray_photoelectron_spectroscopy_Expanded_data_set_confirms_that_adventitious_carbon_aligns_to_the_sample_vacuum_level>
32. Binding energy referencing in X-ray photoelectron spectroscopy, Semantic Scholar, <https://www.semanticscholar.org/paper/Binding-energy-referencing-in-X-ray-photoelectron-Greczynski-Hultman/bb0d32fc4ac73c4bc5f5e7258afd43a58d6d5ad5>
33. Binding energy referencing in X-ray photoelectron spectroscopy, Request PDF, <https://www.researchgate.net/publication/385756157_Binding_energy_referencing_in_X-ray_photoelectron_spectroscopy>
34. An experimental study of charge distribution in, AIP Publishing, <https://pubs.aip.org/aip/jap/article-pdf/doi/10.1063/1.2832630/13434335/024308_1_online.pdf>
35. Supporting Information, DORAS, DCU Research Repository, <https://doras.dcu.ie/27870/2/1-s2.0-S0167931722001824-mmc1.pdf>
37. An Investigation of the Formation and Growth of Oxide-Embedded Silicon Nanocrystals in Hydrogen Silsesquioxane-Derived Nanocomposites, The Journal of Physical Chemistry C, ACS Publications, <https://pubs.acs.org/doi/10.1021/jp070908c>
38. Microscopic Structure Of The SiO2/Si Interface, Request PDF, ResearchGate, <https://www.researchgate.net/publication/221720528_Microscopic_Structure_Of_The_SiO2Si_Interface>
39. Metal-free silicon boride catalyst for oxidative dehydrogenation of, <https://anhuilu.dlut.edu.cn/ky/article/183.pdf>
40. The effect of ruthenium oxidation on the decomposition of SiH4, The Royal Society of Chemistry, <https://pubs.rsc.org/cp/article/28/27/16709/1266281/The-effect-of-ruthenium-oxidation-on-the>
41. Poleval: A Python package for HAXPES analysis, arXiv, <https://arxiv.org/html/2505.14194>
42. lmfitxps, PyPI, <https://pypi.org/project/lmfitxps/>
43. PikaXPS, free XPS peak fitting for Mac and Windows, <https://contact993.github.io/pikaxps/>
44. LG4X, Zenodo, <https://zenodo.org/records/10477914>
45. lmfitxps (websites/lmfitxps_readthedocs_io_en), Context7, <https://context7.com/websites/lmfitxps_readthedocs_io_en>
46. LG4X: lmfit GUI for XPS, GitHub, <https://github.com/hidecode221b/LG4X>
47. LG4X-V2, GitHub Pages, <https://julian-hochhaus.github.io/LG4X-V2/>
48. KherveFitting, GitHub, <https://github.com/KherveFitting/KherveFitting>
49. xps, GitHub Topics, <https://github.com/topics/xps?l=python&o=asc&s=stars>
50. Poleval: A Python package for HAXPES analysis, ResearchGate, <https://www.researchgate.net/publication/391910840_Poleval_A_Python_package_for_HAXPES_analysis>
51. spect_em_dsgmm function, RDocumentation, <https://www.rdocumentation.org/packages/EMpeaksR/versions/0.3.1/topics/spect_em_dsgmm>
52. Help for package EMpeaksR, <https://ftp.sun.ac.za/ftp/ftp/pub/mirrorsites/cran.za.r/web/packages/EMpeaksR/refman/EMpeaksR.html>
