"""Fail-closed behaviour found in review: fit-file shapes, rule codes, LS001, SO001, SO002."""

from __future__ import annotations

from pathlib import Path

import pytest

from xpslint.cli import main
from xpslint.config import Config, ConfigError
from xpslint.engine import run
from xpslint.io.declarative import FitFormatError, loads
from xpslint.models import Outcome
from xpslint.report import render_json, render_text

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
CLEAN_PATH = EXAMPLES / "clean_SiO2_on_Si.toml"
CLEAN = CLEAN_PATH.read_text(encoding="utf-8")
QUESTIONABLE = str(EXAMPLES / "questionable_TiO2_Ti2p.toml")


# -- fit files: every wrong shape is a FitFormatError -----------------------------------


@pytest.mark.parametrize(
    ("old", "new", "match"),
    [
        ("gaussian_width =", "gaussian_widht =", "unknown key 'gaussian_widht'"),
        ('lineshape = "voigt"', 'lineshap = "voigt"', "unknown key 'lineshap'"),
        ('elements = ["Si", "O", "C"]', 'elements = "SiO"', "survey.elements must be a list"),
        ('elements = ["Si", "O", "C"]', "elements = [1, 2]", "survey.elements must be a list"),
        ("gaussian_width = 0.45", 'gaussian_width = "0.45"', "must be a number"),
        ("fwhm = 0.62", 'fwhm = "0.62"', "must be a number"),
        ("quantified = true", 'quantified = "yes"', "must be true or false"),
        ('method = "internal"\n', "", "needs a method"),
    ],
)
def test_malformed_fit_file_is_rejected(old, new, match):
    assert old in CLEAN
    with pytest.raises(FitFormatError, match=match):
        loads(CLEAN.replace(old, new, 1))


def test_invalid_toml_fit_is_a_fit_format_error():
    with pytest.raises(FitFormatError, match="not valid TOML"):
        loads("[instrument\n")


def test_cli_exits_2_on_malformed_fit_without_traceback(tmp_path, capsys):
    path = tmp_path / "typo.toml"
    path.write_text(CLEAN.replace("gaussian_width =", "gaussian_widht ="), encoding="utf-8")
    assert main(["check", str(path)]) == 2
    err = capsys.readouterr().err
    assert "unknown key 'gaussian_widht'" in err
    assert "Traceback" not in err


def test_clean_example_still_loads():
    assert loads(CLEAN).survey_elements == frozenset({"Si", "O", "C"})


# -- config: unknown rule codes and out-of-range tolerances ------------------------------


@pytest.mark.parametrize(
    "section",
    [{"disable": ["FW01"]}, {"disable": ["XX999"]}, {"severity": {"ZZ001": "info"}}],
)
def test_unknown_rule_code_is_a_config_error(section):
    cfg = Config.from_dict(section)
    with pytest.raises(ConfigError, match="unknown rule code"):
        run(loads(CLEAN), cfg)


def test_cli_exits_2_on_unknown_rule_code(tmp_path, capsys):
    path = tmp_path / "pyproject.toml"
    path.write_text('[tool.xpslint]\ndisable = ["FW01"]\n', encoding="utf-8")
    assert main(["check", str(CLEAN_PATH), "--config", str(path)]) == 2
    assert "unknown rule code 'FW01'" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("key", "value"),
    [("so001_area_ratio", -1), ("so002_separation_ev", -0.01), ("fw001_broadening_allowance", 0.9)],
)
def test_out_of_range_tolerance_is_rejected(key, value):
    with pytest.raises(ConfigError, match="must be at least"):
        Config.from_dict({"tolerances": {key: value}})


# -- disabled rules stay visible ---------------------------------------------------------


def test_disabled_rule_is_reported():
    report = run(
        loads(Path(QUESTIONABLE).read_text(encoding="utf-8")),
        Config.from_dict({"disable": ["FW001"]}),
    )
    assert report.disabled == ("FW001",)
    assert "1 rule disabled by config, not in coverage: FW001" in render_text(report, color=False)
    assert '"disabled": [\n      "FW001"\n    ]' in render_json(report)


# -- LS001 fails closed on unknown classes and ignores case ------------------------------

_DS = """
[[spectrum]]
name = "X"
background = "tougaard"
quantified = false
[[spectrum.component]]
id = "c"
element = "Ti"
orbital = "2p"
binding_energy = 458.7
fwhm = 1.1
area = 1.0
gl_mix = 0.3
lineshape = "dss"
asymmetry = 0.1
material_class = "{cls}"
"""


def _ls001(cls: str) -> Outcome:
    report = run(loads(_DS.format(cls=cls)))
    (diag,) = [d for d in report.diagnostics if d.code == "LS001"]
    return diag.outcome


@pytest.mark.parametrize(
    ("cls", "outcome"),
    [
        ("Oxide", Outcome.FAIL),
        ("oxide", Outcome.FAIL),
        ("Metal", Outcome.PASS),
        ("semiconductor", Outcome.CANNOT_CHECK),
        ("oxyde", Outcome.CANNOT_CHECK),
    ],
)
def test_ls001_material_class(cls, outcome):
    assert _ls001(cls) is outcome


# -- SO001 orders a doublet by binding energy when j is omitted --------------------------

_DOUBLET = """
[[spectrum]]
name = "Si2p"
background = "tougaard"
[[spectrum.component]]
id = "{first}"
element = "Si"
orbital = "2p"
binding_energy = {be_first}
fwhm = 0.62
area = {area_first}
gl_mix = 0.25
doublet_partner = "{second}"
[[spectrum.component]]
id = "{second}"
element = "Si"
orbital = "2p"
binding_energy = {be_second}
fwhm = 0.62
area = {area_second}
gl_mix = 0.25
doublet_partner = "{first}"
"""


@pytest.mark.parametrize("three_halves_first", [True, False])
def test_so001_correct_doublet_passes_in_either_file_order(three_halves_first):
    hi = {"id": "p32", "be": 99.5, "area": 1000.0}
    lo = {"id": "p12", "be": 100.1, "area": 500.0}
    a, b = (hi, lo) if three_halves_first else (lo, hi)
    text = _DOUBLET.format(
        first=a["id"],
        second=b["id"],
        be_first=a["be"],
        be_second=b["be"],
        area_first=a["area"],
        area_second=b["area"],
    )
    report = run(loads(text))
    outcomes = {d.code: d.outcome for d in report.diagnostics if d.code in ("SO001", "SO002")}
    assert outcomes == {"SO001": Outcome.PASS, "SO002": Outcome.PASS}


# -- SO002 does not issue a Tier 1 error from a state-dependent splitting ----------------


def test_so002_is_cannot_check_for_state_dependent_ti_2p():
    report = run(loads(Path(QUESTIONABLE).read_text(encoding="utf-8")))
    (diag,) = [d for d in report.diagnostics if d.code == "SO002"]
    assert diag.outcome is Outcome.CANNOT_CHECK
    assert "depends on chemical state" in diag.message
