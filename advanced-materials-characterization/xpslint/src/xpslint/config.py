"""Configuration, read from ``[tool.xpslint]`` in pyproject.toml.

Tier 1 rules cannot be disabled or downgraded. That is not a policy preference; it is
the definition of Tier 1. Attempting either raises, rather than being silently ignored,
so a misconfigured project fails loudly instead of quietly weakening its own checks.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from xpslint.models import Severity, Tier

# The three defaults are placeholders, not sourced values. Each is a round number chosen
# during development so the rules can run; none has been derived or validated. Set them
# for your instrument and material, and treat a verdict near a limit as unsettled.
DEFAULT_TOLERANCES: dict[str, float] = {
    # Absolute tolerance on the doublet area ratio (dimensionless). Placeholder.
    "so001_area_ratio": 0.10,
    # Absolute tolerance on the spin-orbit separation, in eV. Placeholder.
    "so002_separation_ev": 0.05,
    # How much broader than the physical Voigt floor a component may be before it is
    # flagged, as a multiple of the floor. Accounts for phonon broadening and structural
    # disorder. Placeholder; a real value depends on the material.
    "fw001_broadening_allowance": 2.5,
}

# Smallest accepted value per tolerance. A negative tolerance would make every check
# fail, and an allowance below 1 would put the ceiling under the physical floor.
_TOLERANCE_MINIMUM: dict[str, float] = {
    "so001_area_ratio": 0.0,
    "so002_separation_ev": 0.0,
    "fw001_broadening_allowance": 1.0,
}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Config:
    tolerances: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_TOLERANCES))
    severity: dict[str, Severity] = field(default_factory=dict)
    disable: frozenset[str] = frozenset()

    def tolerance(self, key: str) -> float:
        try:
            return self.tolerances[key]
        except KeyError as exc:
            raise ConfigError(f"unknown tolerance {key!r}") from exc

    def severity_for(self, code: str, default: Severity) -> Severity:
        return self.severity.get(code.upper(), default)

    def validate(self, tiers: dict[str, Tier]) -> None:
        """Reject unknown rule codes and any attempt to weaken a Tier 1 rule.

        An unknown code is an error, not a no-op: ``disable = ["FW01"]`` (a typo) would
        otherwise disable nothing and report success.
        """
        for code in sorted(self.disable | self.severity.keys()):
            if code.upper() not in tiers:
                known = ", ".join(sorted(tiers))
                raise ConfigError(f"unknown rule code {code!r}; known codes: {known}")
        for code in self.disable:
            if tiers.get(code.upper()) is Tier.ONE:
                raise ConfigError(
                    f"{code} is Tier 1 (derivable physics) and cannot be disabled. "
                    "If the rule is wrong for your case, the fit needs a stated physical "
                    "mechanism, not a suppressed check."
                )
        for code in self.severity:
            if tiers.get(code.upper()) is Tier.ONE:
                raise ConfigError(f"{code} is Tier 1 and its severity cannot be overridden.")

    @classmethod
    def from_pyproject(cls, path: Path | str) -> Config:
        p = Path(path)
        try:
            data = tomllib.loads(p.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ConfigError(f"{p}: cannot read: {exc.strerror or exc}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"{p}: not valid TOML: {exc}") from exc
        tool = data.get("tool", {})
        if not isinstance(tool, dict):
            raise ConfigError(f"{p}: [tool] must be a table")
        section = tool.get("xpslint", {})
        if not isinstance(section, dict):
            raise ConfigError(f"{p}: [tool.xpslint] must be a table")
        try:
            return cls.from_dict(section)
        except ConfigError as exc:
            raise ConfigError(f"{p}: {exc}") from exc

    @classmethod
    def from_dict(cls, section: dict[str, object]) -> Config:
        """Build a config, rejecting every value whose shape is wrong.

        A wrong shape is never skipped. ``disable = "SO001"`` (a string, not a list) used
        to be accepted while it disabled nothing: a config that silently differs from what
        its author wrote is the failure this module exists to stop.
        """
        tolerances = dict(DEFAULT_TOLERANCES)
        for key, value in _table(section, "tolerances").items():
            if key not in DEFAULT_TOLERANCES:
                raise ConfigError(f"unknown tolerance {key!r}")
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ConfigError(f"tolerance {key!r} must be a number, got {value!r}")
            if value < _TOLERANCE_MINIMUM[key]:
                raise ConfigError(
                    f"tolerance {key!r} must be at least {_TOLERANCE_MINIMUM[key]:g}, got {value!r}"
                )
            tolerances[key] = float(value)

        severity: dict[str, Severity] = {}
        for code, value in _table(section, "severity").items():
            if not isinstance(value, str) or value not in _SEVERITY_VALUES:
                allowed = ", ".join(repr(s.value) for s in Severity)
                raise ConfigError(f"severity for {code} must be one of {allowed}, got {value!r}")
            severity[code.upper()] = Severity(value)

        raw_disable = section.get("disable", [])
        if not isinstance(raw_disable, list):
            raise ConfigError(
                'disable must be a list of rule codes, such as disable = ["BG002"], '
                f"got {raw_disable!r}"
            )
        codes: list[str] = []
        for code in raw_disable:
            if not isinstance(code, str):
                raise ConfigError(f"disable entries must be rule codes (strings), got {code!r}")
            codes.append(code.upper())
        return cls(tolerances=tolerances, severity=severity, disable=frozenset(codes))


_SEVERITY_VALUES = frozenset(s.value for s in Severity)


def _table(section: dict[str, object], name: str) -> dict[str, object]:
    raw = section.get(name, {})
    if not isinstance(raw, dict):
        raise ConfigError(f"[tool.xpslint.{name}] must be a table, got {raw!r}")
    return raw
