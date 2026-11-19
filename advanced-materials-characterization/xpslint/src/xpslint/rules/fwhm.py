"""Tier 2: peak width.

The published envelopes (metals 0.4-1.0 eV, oxides 1.1-2.0 eV) are inherited heuristics
from other people's spectrometers. This rule does not use them. It derives the floor
from two things that are actually knowable: your measured instrumental Gaussian width,
and the tabulated core-hole lifetime Lorentzian width. Without the first it reports
cannot-check; without the second it reports cannot-check.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

from xpslint.config import Config
from xpslint.models import Diagnostic, FitResult, Severity, Tier
from xpslint.refdata import lifetime_width
from xpslint.rules.base import Rule, register


def voigt_fwhm(gaussian: float, lorentzian: float) -> float:
    """Olivero and Longbothum (1977) approximation, accurate to about 0.02%."""
    return 0.5346 * lorentzian + math.sqrt(0.2166 * lorentzian**2 + gaussian**2)


@register
class FW001(Rule):
    code = "FW001"
    tier = Tier.TWO
    severity = Severity.WARNING
    summary = "FWHM lies within the envelope implied by instrumental and lifetime widths"
    citation = "Rule 3, FWHM constraints and phonon broadening"
    requires = frozenset({"instrument.gaussian_width"})

    def targets(self, fit: FitResult) -> list[str]:
        return [f"{s.name}:{c.id}" for s, c in fit.components()]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        allowance = cfg.tolerance("fw001_broadening_allowance")
        gaussian = fit.instrument.gaussian_width
        assert gaussian is not None  # guaranteed by requires
        for spectrum, comp in fit.components():
            target = f"{spectrum.name}:{comp.id}"
            lorentzian = lifetime_width(comp.element, comp.orbital)
            if lorentzian is None:
                yield self.unknown(
                    target,
                    f"no tabulated core-hole lifetime width for {comp.transition}",
                    hint="add it to refdata/lifetimes.toml (Campbell and Papp 2001) once "
                    "verified; the physical floor cannot be computed without it",
                )
                continue
            floor = voigt_fwhm(gaussian, lorentzian)
            ceiling = floor * allowance
            if comp.fwhm < floor - 1e-9:
                yield self.fail(
                    target,
                    "FWHM is narrower than the instrumental and lifetime widths permit",
                    observed=f"{comp.fwhm:.3f} eV",
                    expected=f">= {floor:.3f} eV",
                    hint="a peak cannot be narrower than the response function that measured it",
                )
            elif comp.fwhm > ceiling:
                yield self.fail(
                    target,
                    "FWHM exceeds the physical floor by more than the broadening allowance",
                    observed=f"{comp.fwhm:.3f} eV",
                    expected=f"<= {ceiling:.3f} eV ({allowance:g} x floor {floor:.3f} eV)",
                    hint="justify with a named mechanism (differential charging, multiplet "
                    "splitting, structural disorder) or raise fw001_broadening_allowance",
                )
            else:
                yield self.ok(target, f"{comp.fwhm:.3f} eV within [{floor:.3f}, {ceiling:.3f}] eV")
