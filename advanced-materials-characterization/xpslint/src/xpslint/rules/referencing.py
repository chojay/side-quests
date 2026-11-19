"""Tier 3: binding energy referencing.

The 284.8 eV adventitious carbon value is the clearest case in the field of a Tier 3
habit treated as Tier 1. 284.6 eV was the value under the older convention where
Cu 2p3/2 is set to 932.47 eV; 284.8 eV is the value where Cu 2p3/2 sits at 932.67 eV.
They are the same measurement on two energy scales. ISO recommends a range of
284.6 to 285.2 eV, not a point value, and observed adventitious carbon positions vary
by as much as 1.4 eV in correlation with the substrate work function.
"""

from __future__ import annotations

from collections.abc import Iterable

from xpslint.config import Config
from xpslint.models import Diagnostic, FitResult, Severity, Tier
from xpslint.rules.base import Rule, register


@register
class CA001(Rule):
    code = "CA001"
    tier = Tier.THREE
    severity = Severity.PROMPT
    summary = "adventitious carbon referenced to a point value without a measured work function"
    citation = "Greczynski and Hultman; adventitious carbon aligns to the vacuum level"

    def targets(self, fit: FitResult) -> list[str]:
        return [
            s.name
            for s in fit.spectra
            if s.charge_reference is not None and s.charge_reference.method == "adventitious_carbon"
        ]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        measured = fit.instrument.work_function is not None
        for spectrum in fit.spectra:
            ref = spectrum.charge_reference
            if ref is None or ref.method != "adventitious_carbon":
                continue
            if measured and ref.basis:
                continue
            missing = []
            if not measured:
                missing.append("a measured work function")
            if not ref.basis:
                missing.append("the calibration chain the value derives from")
            value = f"{ref.value:g} eV" if ref.value is not None else "an unstated value"
            yield self.prompt(
                spectrum.name,
                f"referenced to adventitious carbon at {value} without "
                f"{' and '.join(missing)}. State the basis.",
                observed=f"method=adventitious_carbon, value={ref.value}, basis={ref.basis}",
                expected="ISO recommends a range of 284.6 to 285.2 eV, not a point value",
            )


@register
class CA002(Rule):
    code = "CA002"
    tier = Tier.THREE
    severity = Severity.PROMPT
    summary = "charge referencing method is declared"
    citation = "Rule 7, binding energy referencing"

    def targets(self, fit: FitResult) -> list[str]:
        return [s.name for s in fit.spectra if s.charge_reference is None]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        for spectrum in fit.spectra:
            if spectrum.charge_reference is None:
                yield self.prompt(
                    spectrum.name,
                    "no charge referencing method declared; every binding energy in this "
                    "region is unanchored without it",
                )
