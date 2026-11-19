"""Tier 1: chemical consistency across the whole sample, not one region in isolation."""

from __future__ import annotations

import re
from collections.abc import Iterable

from xpslint.config import Config
from xpslint.models import Diagnostic, FitResult, Severity, Tier
from xpslint.rules.base import Rule, register

_FORMULA = re.compile(r"([A-Z][a-z]?)(\d*)")


def formula_elements(assignment: str) -> set[str]:
    """Element symbols in a chemical formula. Returns an empty set for free text."""
    core = assignment.split()[0]
    if not core or not core[0].isupper():
        return set()
    found = {m.group(1) for m in _FORMULA.finditer(core) if m.group(1)}
    # Reject free-text assignments that merely start with a capital ("Adventitious").
    consumed = "".join(m.group(0) for m in _FORMULA.finditer(core))
    return found if consumed == core else set()


@register
class ST001(Rule):
    code = "ST001"
    tier = Tier.ONE
    severity = Severity.ERROR
    summary = "an assigned compound's heteroatoms must appear in the survey scan"
    citation = "Rule 1, stoichiometric validation; Guide to XPS data analysis, JVST A 40, 063201"
    requires = frozenset({"survey.elements"})

    def targets(self, fit: FitResult) -> list[str]:
        return [
            f"{s.name}:{c.id}"
            for s, c in fit.components()
            if c.assignment and formula_elements(c.assignment)
        ]

    def check(self, fit: FitResult, cfg: Config) -> Iterable[Diagnostic]:
        survey = {e.strip() for e in fit.survey_elements}
        for spectrum, comp in fit.components():
            if not comp.assignment:
                continue
            elements = formula_elements(comp.assignment)
            if not elements:
                continue
            target = f"{spectrum.name}:{comp.id}"
            missing = sorted(elements - survey)
            if missing:
                yield self.fail(
                    target,
                    f"{comp.assignment} requires {', '.join(missing)}, absent from the survey",
                    observed=f"survey = {', '.join(sorted(survey)) or '(empty)'}",
                    expected=f"survey containing {', '.join(sorted(elements))}",
                    hint="an assignment that no other region corroborates is a guess, "
                    "however well it fits",
                )
            else:
                yield self.ok(target, f"{comp.assignment} corroborated by the survey scan")
