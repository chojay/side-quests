"""Rule execution and the outcome model.

The engine, not the rule author, decides ``cannot-check``. A rule declares what fit
metadata it ``requires``; if that metadata is absent the rule body never executes.
This is deliberate: a new rule cannot accidentally claim a verdict it has not earned.
"""

from __future__ import annotations

from dataclasses import dataclass

from xpslint.config import Config
from xpslint.models import Diagnostic, FitResult, Outcome, Severity, Tier
from xpslint.rules import all_rules
from xpslint.rules.base import Rule


@dataclass(frozen=True)
class Report:
    fit: FitResult
    diagnostics: tuple[Diagnostic, ...]
    disabled: tuple[str, ...] = ()
    """Rule codes skipped because the config disabled them. They produce no diagnostic,
    so they are outside the coverage figure; the reports list them so that is visible."""

    def by_outcome(self, outcome: Outcome) -> tuple[Diagnostic, ...]:
        return tuple(d for d in self.diagnostics if d.outcome is outcome)

    @property
    def checked(self) -> int:
        return sum(1 for d in self.diagnostics if d.outcome.counts_as_checked)

    @property
    def uncovered(self) -> int:
        return sum(1 for d in self.diagnostics if d.outcome.counts_as_uncovered)

    @property
    def coverage(self) -> float | None:
        """(pass + fail) / (pass + fail + cannot-check).

        ``not-applicable`` and ``prompt`` are excluded from both numerator and
        denominator: neither represents a check that could have been performed.
        Returns None when nothing was checkable either way.
        """
        denominator = self.checked + self.uncovered
        if denominator == 0:
            return None
        return self.checked / denominator

    @property
    def failures(self) -> tuple[Diagnostic, ...]:
        return self.by_outcome(Outcome.FAIL)

    def errors(self) -> tuple[Diagnostic, ...]:
        return tuple(d for d in self.failures if d.severity is Severity.ERROR)

    def exit_code(self, *, strict: bool = False, min_coverage: float | None = None) -> int:
        """Exit status.

        ``cannot-check`` alone exits 0 by default. That is the honest reading: absent
        metadata is a statement about the report, not a defect in the fit. The coverage
        figure is always printed so a trivial pass is visibly a trivial pass, and
        --strict or --min-coverage are available for anyone wanting a hard gate.

        There is deliberately no default for min_coverage. An arbitrary threshold would
        be exactly the kind of unjustified round number this tool exists to eliminate.
        """
        if self.errors():
            return 1
        if strict and self.uncovered:
            return 1
        if min_coverage is not None:
            coverage = self.coverage
            if coverage is not None and coverage < min_coverage:
                return 1
        return 0


def _cannot_check(rule: Rule, target: str, missing: frozenset[str]) -> Diagnostic:
    keys = ", ".join(sorted(missing))
    return Diagnostic(
        code=rule.code,
        tier=rule.tier,
        outcome=Outcome.CANNOT_CHECK,
        severity=Severity.INFO,
        target=target,
        message=f"requires {keys}",
        hint=rule.missing_hint(missing),
    )


def run(fit: FitResult, config: Config | None = None, rules: list[Rule] | None = None) -> Report:
    cfg = config or Config()
    active = rules if rules is not None else all_rules()
    cfg.validate({r.code: r.tier for r in active})

    declared = fit.declared()
    diagnostics: list[Diagnostic] = []
    disabled: list[str] = []

    for rule in active:
        if rule.code in cfg.disable:
            disabled.append(rule.code)
            continue

        targets = rule.targets(fit)
        if not targets:
            diagnostics.append(
                Diagnostic(
                    code=rule.code,
                    tier=rule.tier,
                    outcome=Outcome.NOT_APPLICABLE,
                    severity=Severity.INFO,
                    target=fit.source,
                    message="no applicable targets in this fit",
                )
            )
            continue

        missing = rule.requires - declared
        if missing:
            diagnostics.extend(_cannot_check(rule, t, missing) for t in targets)
            continue

        for diag in rule.check(fit, cfg):
            severity = cfg.severity_for(diag.code, diag.severity)
            diagnostics.append(diag if severity is diag.severity else _resev(diag, severity))

    return Report(fit=fit, diagnostics=tuple(diagnostics), disabled=tuple(disabled))


def _resev(diag: Diagnostic, severity: Severity) -> Diagnostic:
    from dataclasses import replace

    return replace(diag, severity=severity)


__all__ = ["Report", "Tier", "run"]
