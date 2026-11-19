"""Rule protocol and registry."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from xpslint.config import Config
from xpslint.models import Diagnostic, FitResult, Outcome, Severity, Tier

_REGISTRY: list[type[Rule]] = []


def register(cls: type[Rule]) -> type[Rule]:
    _REGISTRY.append(cls)
    return cls


def registry() -> list[Rule]:
    return [cls() for cls in _REGISTRY]


class Rule:
    """A single check.

    ``requires`` names the fit metadata keys the rule needs. The engine compares it
    against what the fit declares and short-circuits to ``cannot-check`` when anything
    is missing, so no rule body has to remember to handle absent metadata.
    """

    code: ClassVar[str] = ""
    tier: ClassVar[Tier] = Tier.TWO
    severity: ClassVar[Severity] = Severity.WARNING
    summary: ClassVar[str] = ""
    citation: ClassVar[str] = ""
    requires: ClassVar[frozenset[str]] = frozenset()

    def targets(self, fit: FitResult) -> list[str]:
        """Identifiers this rule would evaluate. Empty means not-applicable."""
        raise NotImplementedError

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        raise NotImplementedError

    def missing_hint(self, missing: frozenset[str]) -> str | None:
        return _HINTS.get(next(iter(sorted(missing))))

    # -- diagnostic constructors -------------------------------------------------
    def _diag(self, outcome: Outcome, target: str, message: str, **kw: object) -> Diagnostic:
        return Diagnostic(
            code=self.code,
            tier=self.tier,
            outcome=outcome,
            severity=self.severity if outcome is Outcome.FAIL else Severity.INFO,
            target=target,
            message=message,
            **kw,  # type: ignore[arg-type]
        )

    def ok(self, target: str, message: str = "", **kw: object) -> Diagnostic:
        return self._diag(Outcome.PASS, target, message or self.summary, **kw)

    def fail(self, target: str, message: str, **kw: object) -> Diagnostic:
        kw.setdefault("citation", self.citation)
        return self._diag(Outcome.FAIL, target, message, **kw)

    def unknown(self, target: str, message: str, **kw: object) -> Diagnostic:
        """Emit cannot-check from inside a rule.

        Used when the *reference data*, rather than the fit metadata, is what is
        missing. Guessing a tabulated constant would be precisely the failure this
        project exists to name.
        """
        return self._diag(Outcome.CANNOT_CHECK, target, message, **kw)

    def prompt(self, target: str, message: str, **kw: object) -> Diagnostic:
        kw.setdefault("citation", self.citation)
        return Diagnostic(
            code=self.code,
            tier=self.tier,
            outcome=Outcome.PROMPT,
            severity=Severity.PROMPT,
            target=target,
            message=message,
            **kw,  # type: ignore[arg-type]
        )


_HINTS: dict[str, str] = {
    "instrument.gaussian_width": (
        "set gaussian_width = <eV at your pass energy> in the fit file's [instrument] table; "
        "measure it on Ag 3d5/2 (clean silver) or the Fermi edge"
    ),
    "instrument.work_function": (
        "measure the sample work function by UPS and declare instrument.work_function"
    ),
    "survey.elements": "declare the elements detected in the survey scan",
}
