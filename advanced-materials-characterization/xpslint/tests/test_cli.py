"""End-to-end behaviour on the shipped examples."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from xpslint.cli import main
from xpslint.engine import run
from xpslint.io import load
from xpslint.models import Outcome

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_clean_example_is_clean(capsys):
    assert main(["check", str(EXAMPLES / "clean_SiO2_on_Si.toml"), "--no-color"]) == 0
    out = capsys.readouterr().out
    assert "no findings" in out
    assert "coverage: " in out


def test_questionable_example_fails(capsys):
    assert main(["check", str(EXAMPLES / "questionable_TiO2_Ti2p.toml"), "--no-color"]) == 1
    out = capsys.readouterr().out
    for code in ("SO001", "SO002", "LS001", "LS003", "ST001"):
        assert code in out


def test_questionable_example_reports_every_outcome():
    report = run(load(EXAMPLES / "questionable_TiO2_Ti2p.toml"))
    present = {d.outcome for d in report.diagnostics}
    assert present == set(Outcome), sorted(o.value for o in set(Outcome) - present)


def test_coverage_is_always_printed(capsys):
    main(["check", str(EXAMPLES / "questionable_TiO2_Ti2p.toml"), "--no-color"])
    assert "coverage:" in capsys.readouterr().out


def test_json_output_is_valid(capsys):
    main(["check", str(EXAMPLES / "clean_SiO2_on_Si.toml"), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["coverage"] == 1.0
    assert payload["summary"]["failed"] == 0


def test_rules_command_groups_by_tier(capsys):
    assert main(["rules"]) == 0
    out = capsys.readouterr().out
    assert "Tier 1" in out and "Tier 2" in out and "Tier 3" in out
    assert "cannot-check" in out


@pytest.mark.parametrize("flag", [[], ["--strict"]])
def test_clean_example_passes_regardless_of_strictness(flag, capsys):
    assert main(["check", str(EXAMPLES / "clean_SiO2_on_Si.toml"), *flag]) == 0
