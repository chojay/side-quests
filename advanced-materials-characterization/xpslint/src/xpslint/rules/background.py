"""Tier 3: background choice.

BG002 is Tier 3 and RS001 (residual randomness) is Tier 2, and the pairing is the
sharpest thing this tool encodes. Shirley backgrounds have been shown to produce
completely wrong component areas while still yielding satisfying residual functions and
Abbe criteria, so the statistical check cannot catch the background error. A smooth
background error absorbs into peak areas without leaving structured residuals. It can
only be prompted for.
"""

from __future__ import annotations

from collections.abc import Iterable

from xpslint.config import Config
from xpslint.models import Diagnostic, FitResult, Severity, Tier
from xpslint.rules.base import Rule, register


@register
class BG002(Rule):
    code = "BG002"
    tier = Tier.THREE
    severity = Severity.PROMPT
    summary = "Shirley background used for quantification without a Tougaard cross-check"
    citation = (
        "Hesse et al., J. Electron Spectrosc. Relat. Phenom. 186, 44 (2013); "
        "Shirley vs improved Tougaard"
    )

    def targets(self, fit: FitResult) -> list[str]:
        return [
            s.name
            for s in fit.spectra
            if s.quantified and (s.background or "").lower().startswith("shirley")
        ]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        for spectrum in fit.spectra:
            if not spectrum.quantified:
                continue
            if not (spectrum.background or "").lower().startswith("shirley"):
                continue
            yield self.prompt(
                spectrum.name,
                "Shirley is an empirical approximation, not a physical model, and has "
                "been shown to return wrong areas while passing residual and Abbe tests. "
                "State why it is appropriate here, or cross-check against a wider-window "
                "Tougaard treatment.",
                observed=f"background={spectrum.background}, quantified=True",
            )


@register
class BG003(Rule):
    code = "BG003"
    tier = Tier.THREE
    severity = Severity.PROMPT
    summary = "background model is declared"
    citation = "Rule 5, active background methodology"

    def targets(self, fit: FitResult) -> list[str]:
        return [s.name for s in fit.spectra if s.background is None]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        for spectrum in fit.spectra:
            if spectrum.background is None:
                yield self.prompt(
                    spectrum.name,
                    "no background model declared; the choice materially changes every "
                    "reported area",
                )
