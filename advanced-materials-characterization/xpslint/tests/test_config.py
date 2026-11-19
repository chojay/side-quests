"""Malformed configuration must fail loudly, never fall back to a weaker config."""

from __future__ import annotations

from pathlib import Path

import pytest

from xpslint.cli import main
from xpslint.config import Config, ConfigError
from xpslint.models import Severity

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
CLEAN = str(EXAMPLES / "clean_SiO2_on_Si.toml")


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(body, encoding="utf-8")
    return path


# -- from_dict: each malformed shape raises ConfigError ------------------------------


@pytest.mark.parametrize("value", ["SO001", "FW002", 1, {"FW002": True}])
def test_disable_that_is_not_a_list_is_rejected(value):
    with pytest.raises(ConfigError, match="disable must be a list"):
        Config.from_dict({"disable": value})


@pytest.mark.parametrize("entry", [1, True, ["FW002"]])
def test_disable_entry_that_is_not_a_string_is_rejected(entry):
    with pytest.raises(ConfigError, match="disable entries"):
        Config.from_dict({"disable": [entry]})


@pytest.mark.parametrize("value", ["info", ["FW002"], 3])
def test_severity_section_that_is_not_a_table_is_rejected(value):
    with pytest.raises(ConfigError, match=r"\[tool\.xpslint\.severity\] must be a table"):
        Config.from_dict({"severity": value})


@pytest.mark.parametrize("value", [0.1, ["so001_area_ratio"], "strict"])
def test_tolerances_section_that_is_not_a_table_is_rejected(value):
    with pytest.raises(ConfigError, match=r"\[tool\.xpslint\.tolerances\] must be a table"):
        Config.from_dict({"tolerances": value})


@pytest.mark.parametrize("value", ["informational", "INFO", 1, True])
def test_bad_severity_value_is_a_config_error(value):
    with pytest.raises(ConfigError, match="severity for FW002 must be one of"):
        Config.from_dict({"severity": {"FW002": value}})


@pytest.mark.parametrize("value", ["0.1", True, [0.1]])
def test_tolerance_that_is_not_a_number_is_rejected(value):
    with pytest.raises(ConfigError, match="must be a number"):
        Config.from_dict({"tolerances": {"so001_area_ratio": value}})


def test_well_formed_config_still_loads():
    cfg = Config.from_dict(
        {
            "disable": ["bg002"],
            "severity": {"fw001": "info"},
            "tolerances": {"so001_area_ratio": 0.2, "so002_separation_ev": 1},
        }
    )
    assert cfg.disable == frozenset({"BG002"})
    assert cfg.severity == {"FW001": Severity.INFO}
    assert cfg.tolerance("so001_area_ratio") == 0.2
    assert cfg.tolerance("so002_separation_ev") == 1.0


# -- from_pyproject: file-level problems -------------------------------------------------


def test_xpslint_key_that_is_not_a_table_is_rejected(tmp_path):
    path = _write(tmp_path, '[tool]\nxpslint = "on"\n')
    with pytest.raises(ConfigError, match=r"\[tool\.xpslint\] must be a table"):
        Config.from_pyproject(path)


def test_invalid_toml_is_a_config_error(tmp_path):
    path = _write(tmp_path, "[tool.xpslint\ndisable = []\n")
    with pytest.raises(ConfigError, match="not valid TOML"):
        Config.from_pyproject(path)


def test_missing_config_file_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="cannot read"):
        Config.from_pyproject(tmp_path / "absent.toml")


def test_error_names_the_file(tmp_path):
    path = _write(tmp_path, '[tool.xpslint]\ndisable = "SO001"\n')
    with pytest.raises(ConfigError, match=r"pyproject\.toml: disable must be a list"):
        Config.from_pyproject(path)


# -- CLI: exit 2 with a one-line message, no traceback ------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        '[tool.xpslint]\ndisable = "SO001"\n',
        '[tool.xpslint]\nseverity = "info"\n',
        "[tool.xpslint]\ntolerances = 0.1\n",
        '[tool.xpslint.severity]\nFW002 = "informational"\n',
        "[tool.xpslint\n",
    ],
)
def test_cli_exits_2_on_malformed_config(tmp_path, capsys, body):
    path = _write(tmp_path, body)
    assert main(["check", CLEAN, "--config", str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("xpslint: configuration error: ")
    assert "Traceback" not in captured.err
    assert captured.out == ""


def test_cli_reports_a_broken_default_pyproject(tmp_path, monkeypatch, capsys):
    _write(tmp_path, '[tool.xpslint]\ndisable = "SO001"\n')
    monkeypatch.chdir(tmp_path)
    assert main(["check", CLEAN]) == 2
    assert "pyproject.toml: disable must be a list" in capsys.readouterr().err


def test_cli_accepts_a_pyproject_without_an_xpslint_section(tmp_path, monkeypatch, capsys):
    _write(tmp_path, '[project]\nname = "unrelated"\n')
    monkeypatch.chdir(tmp_path)
    assert main(["check", CLEAN, "--no-color"]) == 0
    assert "no findings" in capsys.readouterr().out
