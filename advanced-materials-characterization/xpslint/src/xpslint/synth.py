"""Synthetic forward model.

The hard question for any validator is: how do you know the validator is right? The
answer is to generate fits whose ground truth you control, then assert that a valid fit
produces no failures and that a single injected perturbation produces exactly one.

Building this is also the point of the exercise. You cannot generate a physically
correct fit without stating precisely what "correct" means.
"""

from __future__ import annotations

from dataclasses import replace

from xpslint.models import (
    ChargeReference,
    Component,
    FitResult,
    Instrument,
    Spectrum,
)
from xpslint.rules.fwhm import voigt_fwhm

# Reference instrument: a monochromated Al K-alpha source at moderate pass energy.
INSTRUMENT = Instrument(
    gaussian_width=0.45,
    pass_energy=20.0,
    source_linewidth=0.26,
    transmission_function="vendor-calibrated",
    work_function=4.6,
)


def _doublet(
    prefix: str,
    element: str,
    orbital: str,
    be_low_j: float,
    separation: float,
    fwhm: float,
    area_low_j: float,
    ratio: float,
    **kw: object,
) -> tuple[Component, Component]:
    """Build a physically consistent spin-orbit doublet.

    ``be_low_j`` is the binding energy of the lower-j (higher binding energy) partner.
    """
    lo = Component(
        id=f"{prefix}_1_2",
        element=element,
        orbital=orbital,
        j="1/2",
        binding_energy=be_low_j,
        fwhm=fwhm,
        area=area_low_j,
        doublet_partner=f"{prefix}_3_2",
        **kw,  # type: ignore[arg-type]
    )
    hi = Component(
        id=f"{prefix}_3_2",
        element=element,
        orbital=orbital,
        j="3/2",
        binding_energy=be_low_j - separation,
        fwhm=fwhm,
        area=area_low_j * ratio,
        doublet_partner=f"{prefix}_1_2",
        **kw,  # type: ignore[arg-type]
    )
    return lo, hi


def valid_fit() -> FitResult:
    """A native oxide on silicon, fully declared and physically consistent.

    Widths are derived rather than chosen: each is the Voigt floor implied by the
    instrument's Gaussian width and the tabulated core-hole lifetime width, scaled by a
    factor inside the broadening allowance. Elemental silicon sits near the floor
    (ordered crystalline lattice); the oxide is broader (amorphous, disordered).
    """
    g = INSTRUMENT.gaussian_width
    assert g is not None
    si_floor = voigt_fwhm(g, 0.05)
    o_floor = voigt_fwhm(g, 0.16)

    si0_lo, si0_hi = _doublet(
        "Si0",
        "Si",
        "2p",
        be_low_j=100.1,
        separation=0.60,
        fwhm=si_floor * 1.3,
        area_low_j=500.0,
        ratio=2.0,
        lineshape="voigt",
        gl_mix=0.25,
        assignment="Si",
        material_class="semiconductor",
    )
    si4_lo, si4_hi = _doublet(
        "Si4",
        "Si",
        "2p",
        be_low_j=104.1,
        separation=0.60,
        fwhm=si_floor * 2.2,
        area_low_j=250.0,
        ratio=2.0,
        lineshape="voigt",
        gl_mix=0.20,
        assignment="SiO2",
        material_class="oxide",
    )
    o1s = Component(
        id="O1s_SiO2",
        element="O",
        orbital="1s",
        binding_energy=532.6,
        fwhm=o_floor * 2.0,
        area=1500.0,
        lineshape="voigt",
        gl_mix=0.20,
        assignment="SiO2",
        material_class="oxide",
    )
    reference = ChargeReference(
        method="internal",
        value=99.5,
        basis="bulk Si 2p3/2 of the substrate",
    )
    return FitResult(
        source="synthetic:SiO2-on-Si",
        instrument=INSTRUMENT,
        survey_elements=frozenset({"Si", "O", "C"}),
        spectra=(
            Spectrum(
                name="Si2p",
                components=(si0_lo, si0_hi, si4_lo, si4_hi),
                background="active-shirley",
                background_mode="active",
                step_size=0.05,
                charge_reference=reference,
                quantified=True,
            ),
            Spectrum(
                name="O1s",
                components=(o1s,),
                background="tougaard",
                background_mode="active",
                step_size=0.05,
                charge_reference=reference,
                quantified=True,
            ),
        ),
    )


# -- perturbation helpers -------------------------------------------------------


def with_component(fit: FitResult, component_id: str, **changes: object) -> FitResult:
    """Return a copy with one component modified. Injects exactly one violation."""
    found = False
    spectra = []
    for spectrum in fit.spectra:
        components = []
        for comp in spectrum.components:
            if comp.id == component_id:
                comp = replace(comp, **changes)  # type: ignore[arg-type]
                found = True
            components.append(comp)
        spectra.append(replace(spectrum, components=tuple(components)))
    if not found:
        raise KeyError(f"no component {component_id!r}")
    return replace(fit, spectra=tuple(spectra))


def with_spectrum(fit: FitResult, name: str, **changes: object) -> FitResult:
    spectra = tuple(
        replace(s, **changes) if s.name == name else s  # type: ignore[arg-type]
        for s in fit.spectra
    )
    return replace(fit, spectra=spectra)


def undeclare(fit: FitResult, *fields: str) -> FitResult:
    """Strip declared metadata, to exercise cannot-check."""
    instrument = fit.instrument
    survey = fit.survey_elements
    for name in fields:
        if name == "survey.elements":
            survey = frozenset()
        else:
            instrument = replace(instrument, **{name.removeprefix("instrument."): None})
    return replace(fit, instrument=instrument, survey_elements=survey)
