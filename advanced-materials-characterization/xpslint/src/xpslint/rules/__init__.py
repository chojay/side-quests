"""Rule registry.

Importing this package registers every built-in rule. Third-party rule packs will
attach through an entry point group (``xpslint.rules``) at a later milestone.
"""

from __future__ import annotations

from xpslint.rules import (  # noqa: F401  (imported for registration side effects)
    background,
    fwhm,
    lineshape,
    referencing,
    spin_orbit,
    stoichiometry,
)
from xpslint.rules.base import Rule, register, registry


def all_rules() -> list[Rule]:
    return sorted(registry(), key=lambda r: (r.tier.value, r.code))


__all__ = ["Rule", "all_rules", "register", "registry"]
