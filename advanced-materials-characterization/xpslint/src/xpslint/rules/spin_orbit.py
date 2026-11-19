"""Tier 1: spin-orbit coupling constraints."""

from __future__ import annotations

from collections.abc import Iterable

from xpslint.config import Config
from xpslint.models import DOUBLET_RATIOS, Component, Diagnostic, FitResult, Severity, Tier
from xpslint.refdata import spin_orbit_separation, spin_orbit_state_dependent
from xpslint.rules.base import Rule, register

Pair = tuple[str, Component, Component]


def _pairs(fit: FitResult) -> list[Pair]:
    """Every spin-orbit doublet in the fit, as (target, lower-j, higher-j)."""
    out: list[Pair] = []
    for spectrum in fit.spectra:
        for lo, hi in spectrum.doublet_pairs():
            out.append((f"{spectrum.name}:{lo.id}+{hi.id}", lo, hi))
    return out


@register
class SO001(Rule):
    code = "SO001"
    tier = Tier.ONE
    severity = Severity.ERROR
    summary = "doublet area ratio follows (2j+1) degeneracy"
    citation = "(2j+1) state degeneracy; Major et al., JVST A 38, 061203 (2020)"

    def targets(self, fit: FitResult) -> list[str]:
        return [target for target, _, _ in _pairs(fit)]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        tol = cfg.tolerance("so001_area_ratio")
        for target, lo, hi in _pairs(fit):
            expected = DOUBLET_RATIOS.get(hi.subshell)
            if expected is None:
                yield self.unknown(target, f"no theoretical ratio for subshell {hi.subshell!r}")
                continue
            if lo.area == 0:
                yield self.fail(target, "lower-j component has zero area")
                continue
            observed = hi.area / lo.area
            if abs(observed - expected) > tol:
                yield self.fail(
                    target,
                    "doublet area ratio deviates from the (2j+1) multiplicity ratio",
                    observed=f"{observed:.3f}",
                    expected=f"{expected:.3f} +/- {tol:.2f}",
                    hint="departure from the statistical ratio needs a named physical "
                    "mechanism, not a better residual",
                )
            else:
                yield self.ok(
                    target,
                    f"area ratio {observed:.3f} within {tol:.2f} of {expected:.3f}",
                )


@register
class SO002(Rule):
    code = "SO002"
    tier = Tier.ONE
    severity = Severity.ERROR
    summary = "doublet separation matches the tabulated spin-orbit splitting"
    citation = "element-specific spin-orbit splitting; xpsdatabase.com reference protocol"

    def targets(self, fit: FitResult) -> list[str]:
        return [target for target, _, _ in _pairs(fit)]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        tol = cfg.tolerance("so002_separation_ev")
        for target, lo, hi in _pairs(fit):
            if spin_orbit_state_dependent(hi.element, hi.orbital):
                yield self.unknown(
                    target,
                    f"{hi.transition} splitting depends on chemical state by more than the "
                    "tolerance, and no state-resolved value is tabulated",
                    hint="add state-resolved values to refdata/spin_orbit.toml once verified "
                    "against a primary source",
                )
                continue
            reference = spin_orbit_separation(hi.element, hi.orbital)
            if reference is None:
                yield self.unknown(
                    target,
                    f"no tabulated spin-orbit separation for {hi.transition}",
                    hint="add it to refdata/spin_orbit.toml once verified against a primary source",
                )
                continue
            observed = abs(lo.binding_energy - hi.binding_energy)
            if abs(observed - reference) > tol:
                yield self.fail(
                    target,
                    f"{hi.transition} doublet separation is not the tabulated value",
                    observed=f"{observed:.3f} eV",
                    expected=f"{reference:.3f} +/- {tol:.2f} eV",
                )
            else:
                yield self.ok(target, f"separation {observed:.3f} eV matches {reference:.3f} eV")
