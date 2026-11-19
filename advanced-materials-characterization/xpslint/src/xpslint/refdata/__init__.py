"""Reference data.

A missing entry here is reported as ``cannot-check``, never guessed. Reference data
that is absent is a knowable-but-unknown quantity, which is exactly what Tier 2 means.
"""

from __future__ import annotations

import tomllib
from functools import cache
from pathlib import Path

_DIR = Path(__file__).parent


@cache
def _load(name: str) -> dict[str, dict[str, float]]:
    raw = tomllib.loads((_DIR / name).read_text(encoding="utf-8"))
    return {
        element: {orbital: float(v) for orbital, v in orbitals.items()}
        for element, orbitals in raw.items()
        if isinstance(orbitals, dict)
    }


def spin_orbit_separation(element: str, orbital: str) -> float | None:
    """Spin-orbit splitting in eV, or None if not tabulated."""
    return _load("spin_orbit.toml").get(element, {}).get(orbital)


def lifetime_width(element: str, orbital: str) -> float | None:
    """Core-hole lifetime Lorentzian FWHM in eV, or None if not tabulated."""
    return _load("lifetimes.toml").get(element, {}).get(orbital)


@cache
def _state_dependent() -> frozenset[str]:
    raw = tomllib.loads((_DIR / "spin_orbit.toml").read_text(encoding="utf-8"))
    entries = raw.get("state_dependent", [])
    return frozenset(str(e) for e in entries) if isinstance(entries, list) else frozenset()


def spin_orbit_state_dependent(element: str, orbital: str) -> bool:
    """True when one tabulated splitting cannot hold across chemical states."""
    return f"{element} {orbital}" in _state_dependent()
