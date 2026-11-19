"""Negative controls, injected violations, and the outcome model."""

from __future__ import annotations

import pytest

from xpslint.config import Config, ConfigError
from xpslint.engine import run
from xpslint.models import Outcome, Severity, Tier
from xpslint.rules import all_rules
from xpslint.synth import undeclare, valid_fit, with_component, with_spectrum


def codes(report, outcome):
    return {d.code for d in report.by_outcome(outcome)}


# -- negative control -----------------------------------------------------------
# A false positive is the worst possible defect in a tool whose purpose is trust,
# so this is the highest-priority test in the suite.


def test_valid_fit_produces_no_failures():
    report = run(valid_fit())
    assert report.failures == (), [d.code + ": " + d.message for d in report.failures]


def test_valid_fit_is_fully_covered():
    report = run(valid_fit())
    assert report.uncovered == 0
    assert report.coverage == 1.0
    assert report.exit_code() == 0


def test_valid_fit_passes_strict():
    assert run(valid_fit()).exit_code(strict=True, min_coverage=1.0) == 0


# -- injected violations: exactly one rule fires --------------------------------


@pytest.mark.parametrize(
    ("code", "mutate"),
    [
        ("SO001", lambda f: with_component(f, "Si4_3_2", area=427.0)),
        ("SO002", lambda f: with_component(f, "Si4_1_2", binding_energy=105.0)),
        ("LS001", lambda f: with_component(f, "O1s_SiO2", asymmetry=0.08)),
        ("LS002", lambda f: with_component(f, "O1s_SiO2", lineshape="gaussian")),
        ("LS003", lambda f: with_component(f, "O1s_SiO2", lineshape="doniach-sunjic")),
        ("FW001", lambda f: with_component(f, "O1s_SiO2", fwhm=4.0)),
        ("FW001", lambda f: with_component(f, "O1s_SiO2", fwhm=0.1)),
    ],
)
def test_single_injection_fires_exactly_one_rule(code, mutate):
    report = run(mutate(valid_fit()))
    assert codes(report, Outcome.FAIL) == {code}


def test_missing_heteroatom_is_caught():
    fit = valid_fit()
    report = run(fit.__class__(**{**fit.__dict__, "survey_elements": frozenset({"Si", "C"})}))
    assert "ST001" in codes(report, Outcome.FAIL)


# -- cannot-check ---------------------------------------------------------------


def test_missing_instrument_width_yields_cannot_check_not_a_warning():
    report = run(undeclare(valid_fit(), "instrument.gaussian_width"))
    assert "FW001" in codes(report, Outcome.CANNOT_CHECK)
    assert "FW001" not in codes(report, Outcome.FAIL)
    assert "FW001" not in codes(report, Outcome.PASS)


def test_cannot_check_names_the_missing_key_and_how_to_get_it():
    report = run(undeclare(valid_fit(), "instrument.gaussian_width"))
    diag = next(d for d in report.by_outcome(Outcome.CANNOT_CHECK) if d.code == "FW001")
    assert "instrument.gaussian_width" in diag.message
    assert diag.hint and "Ag 3d5/2" in diag.hint


def test_missing_survey_yields_cannot_check():
    report = run(undeclare(valid_fit(), "survey.elements"))
    assert "ST001" in codes(report, Outcome.CANNOT_CHECK)


def test_missing_reference_data_also_yields_cannot_check():
    """Absent tabulated data is cannot-check, never a guessed constant."""
    fit = with_component(valid_fit(), "O1s_SiO2", element="Xx")
    report = run(fit)
    unknown = [d for d in report.by_outcome(Outcome.CANNOT_CHECK) if d.code == "FW001"]
    assert unknown and "lifetime" in unknown[0].message


def test_coverage_falls_when_metadata_is_absent():
    full = run(valid_fit())
    partial = run(undeclare(valid_fit(), "instrument.gaussian_width"))
    assert partial.coverage is not None
    assert partial.coverage < full.coverage


def test_undeclared_everything_does_not_silently_pass():
    """The failure mode of the honest default, and its mitigation."""
    fit = undeclare(valid_fit(), "instrument.gaussian_width", "survey.elements")
    report = run(fit)
    assert report.exit_code() == 0, "cannot-check alone must not fail the build"
    assert report.exit_code(strict=True) == 1
    assert report.coverage is not None and report.coverage < 1.0


# -- not-applicable must not be folded into cannot-check ------------------------


def test_not_applicable_is_excluded_from_coverage():
    report = run(valid_fit())
    n_a = report.by_outcome(Outcome.NOT_APPLICABLE)
    assert n_a, "expected some rules to be inapplicable to this fit"
    assert report.checked + report.uncovered == sum(
        1
        for d in report.diagnostics
        if d.outcome.counts_as_checked or d.outcome.counts_as_uncovered
    )
    assert all(d.outcome is not Outcome.CANNOT_CHECK for d in n_a)


def test_prompts_are_excluded_from_coverage():
    fit = with_spectrum(valid_fit(), "Si2p", background="shirley")
    report = run(fit)
    assert "BG002" in codes(report, Outcome.PROMPT)
    assert report.coverage == 1.0
    assert report.exit_code() == 0, "a Tier 3 prompt must never fail the build"


# -- tier 1 is not negotiable ---------------------------------------------------


def test_tier1_cannot_be_disabled():
    with pytest.raises(ConfigError, match="Tier 1"):
        run(valid_fit(), Config(disable=frozenset({"SO001"})))


def test_tier1_severity_cannot_be_overridden():
    with pytest.raises(ConfigError, match="Tier 1"):
        run(valid_fit(), Config(severity={"SO001": Severity.INFO}))


def test_tier2_may_be_downgraded():
    fit = with_component(valid_fit(), "O1s_SiO2", fwhm=4.0)
    report = run(fit, Config(severity={"FW001": Severity.INFO}))
    assert report.errors() == ()
    assert report.exit_code() == 0


def test_every_rule_declares_its_metadata_and_tier():
    for rule in all_rules():
        assert rule.code and rule.summary
        assert isinstance(rule.tier, Tier)
        assert all(key.count(".") == 1 for key in rule.requires)
