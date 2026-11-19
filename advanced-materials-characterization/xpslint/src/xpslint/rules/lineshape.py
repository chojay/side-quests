"""Tier 1: line shape constraints."""

from __future__ import annotations

from collections.abc import Iterable

from xpslint.config import Config
from xpslint.models import Diagnostic, FitResult, Severity, Tier
from xpslint.rules.base import Rule, register

ASYMMETRIC = {"doniach-sunjic", "ds", "dss", "doniach-sunjic-shirley"}
TRUNCATED = {"dss", "doniach-sunjic-shirley"}


@register
class LS001(Rule):
    code = "LS001"
    tier = Tier.ONE
    severity = Severity.ERROR
    summary = "Doniach-Sunjic asymmetry only on materials with states at the Fermi level"
    citation = "core-hole screening requires conduction electrons; see Rule 4"

    def targets(self, fit: FitResult) -> list[str]:
        return [
            f"{s.name}:{c.id}"
            for s, c in fit.components()
            if c.asymmetry is not None and c.asymmetry > 0
        ]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        for spectrum, comp in fit.components():
            if comp.asymmetry is None or comp.asymmetry <= 0:
                continue
            target = f"{spectrum.name}:{comp.id}"
            if comp.material_class is None:
                yield self.unknown(
                    target,
                    "asymmetry declared but material_class is not",
                    hint="set material_class (metal, oxide, insulator, conductive-oxide, ...) "
                    "so the physical basis for asymmetry can be checked",
                )
            elif comp.is_insulating is None:
                yield self.unknown(
                    target,
                    f"unknown material_class {comp.material_class!r}",
                    hint="use a known class: metal, graphitic, conductive-oxide, "
                    "doped-semiconductor (asymmetry admissible) or insulator, oxide, "
                    "polymer, ceramic, glass (not admissible)",
                )
            elif comp.is_insulating:
                yield self.fail(
                    target,
                    "Doniach-Sunjic asymmetry applied to a material with no density of "
                    "states at the Fermi level",
                    observed=f"alpha={comp.asymmetry:g}, material_class={comp.material_class}",
                    expected="alpha only on metallic or conductive materials",
                    hint="a conductive oxide must be declared as material_class = "
                    '"conductive-oxide" rather than "oxide"',
                )
            else:
                yield self.ok(
                    target, f"asymmetry on {comp.material_class} is physically admissible"
                )


@register
class LS002(Rule):
    code = "LS002"
    tier = Tier.ONE
    severity = Severity.ERROR
    summary = "every peak carries a Lorentzian component (finite core-hole lifetime)"
    citation = "core-hole lifetime broadening is unavoidable; see Rule 4"

    def targets(self, fit: FitResult) -> list[str]:
        return [f"{s.name}:{c.id}" for s, c in fit.components()]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        for spectrum, comp in fit.components():
            target = f"{spectrum.name}:{comp.id}"
            pure_gaussian = comp.lineshape.lower() == "gaussian" or (
                comp.gl_mix is not None and comp.gl_mix <= 0
            )
            if pure_gaussian:
                yield self.fail(
                    target,
                    "pure Gaussian line shape has no Lorentzian contribution",
                    observed=f"lineshape={comp.lineshape}, gl_mix={comp.gl_mix}",
                    expected="a Voigt or pseudo-Voigt with a non-zero Lorentzian fraction",
                    hint="the Lorentzian width is set by the tabulated core-hole lifetime; "
                    "it is not a free parameter",
                )
            else:
                yield self.ok(target, f"lineshape {comp.lineshape} includes a Lorentzian term")


@register
class LS003(Rule):
    code = "LS003"
    tier = Tier.ONE
    severity = Severity.ERROR
    summary = "un-truncated Doniach-Sunjic cannot be used for quantification"
    citation = "the DS integral diverges; the DSS form truncates it (OSTI 1976397)"

    def targets(self, fit: FitResult) -> list[str]:
        return [
            f"{s.name}:{c.id}" for s, c in fit.components() if c.lineshape.lower() in ASYMMETRIC
        ]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        for spectrum, comp in fit.components():
            shape = comp.lineshape.lower()
            if shape not in ASYMMETRIC:
                continue
            target = f"{spectrum.name}:{comp.id}"
            if shape not in TRUNCATED and spectrum.quantified:
                yield self.fail(
                    target,
                    "un-truncated Doniach-Sunjic used in a quantified spectrum; its "
                    "integral diverges, so the area is not defined",
                    observed=f"lineshape={comp.lineshape}, quantified=True",
                    expected="dss (Doniach-Sunjic-Shirley), or quantified = false",
                )
            else:
                yield self.ok(target, f"{comp.lineshape} integrates to a finite area")
