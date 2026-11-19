"""Rule-level details worth pinning down."""

from __future__ import annotations

import math

import pytest

from xpslint.models import DOUBLET_RATIOS
from xpslint.rules.fwhm import voigt_fwhm
from xpslint.rules.stoichiometry import formula_elements


@pytest.mark.parametrize(
    ("subshell", "ratio"),
    [("p", 2.0), ("d", 1.5), ("f", 4 / 3)],
)
def test_doublet_ratios_follow_2j_plus_1(subshell, ratio):
    assert DOUBLET_RATIOS[subshell] == pytest.approx(ratio)


def test_voigt_floor_exceeds_both_widths():
    """A convolution is wider than either of its inputs."""
    g, lorentz = 0.45, 0.16
    floor = voigt_fwhm(g, lorentz)
    assert floor > g
    assert floor > lorentz


def test_voigt_floor_reduces_to_gaussian_when_lifetime_vanishes():
    assert voigt_fwhm(0.45, 0.0) == pytest.approx(0.45)


def test_voigt_floor_reduces_to_lorentzian_when_instrument_is_perfect():
    assert voigt_fwhm(0.0, 0.30) == pytest.approx(0.30, rel=1e-3)


def test_voigt_floor_is_monotonic():
    widths = [voigt_fwhm(0.45, lorentz) for lorentz in (0.0, 0.1, 0.2, 0.4)]
    assert widths == sorted(widths)
    assert all(math.isfinite(w) for w in widths)


@pytest.mark.parametrize(
    ("assignment", "expected"),
    [
        ("SiO2", {"Si", "O"}),
        ("TiO2", {"Ti", "O"}),
        ("Si2O3", {"Si", "O"}),
        ("Al2O3", {"Al", "O"}),
        ("HfO2", {"Hf", "O"}),
        ("TiN", {"Ti", "N"}),
        ("Si", {"Si"}),
        ("Adventitious carbon", set()),
        ("metallic", set()),
    ],
)
def test_formula_parsing(assignment, expected):
    assert formula_elements(assignment) == expected
