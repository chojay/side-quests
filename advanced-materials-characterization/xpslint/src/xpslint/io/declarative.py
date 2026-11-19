"""Declarative TOML fit description.

Every value is checked for shape before it reaches the model. An unknown key (a typo
such as ``gaussian_widht``), a string where a list belongs (``elements = "TiO"``) or a
string where a number belongs (``gaussian_width = "0.4"``) raises ``FitFormatError``
with one line, instead of a traceback or, worse, a quietly different fit.
"""

from __future__ import annotations

import tomllib
from dataclasses import fields
from pathlib import Path
from typing import Any

from xpslint.models import ChargeReference, Component, FitResult, Instrument, Spectrum


class FitFormatError(ValueError):
    pass


def load(path: Path | str) -> FitResult:
    p = Path(path)
    return loads(p.read_text(encoding="utf-8"), source=str(p))


def loads(text: str, source: str = "<string>") -> FitResult:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise FitFormatError(f"not valid TOML: {exc}") from exc
    return _fit(data, source)


_TOP_KEYS = frozenset({"source", "instrument", "survey", "spectrum"})
_INSTRUMENT_NUMBERS = frozenset(
    {"gaussian_width", "pass_energy", "source_linewidth", "work_function"}
)
_INSTRUMENT_STRINGS = frozenset({"transmission_function"})
_SPECTRUM_KEYS = frozenset(
    {
        "name",
        "component",
        "background",
        "background_mode",
        "step_size",
        "charge_reference",
        "quantified",
    }
)
_REFERENCE_KEYS = frozenset({"method", "value", "basis"})
_COMPONENT_REQUIRED = frozenset({"id", "element", "orbital", "binding_energy", "fwhm", "area"})
_COMPONENT_NUMBERS = frozenset({"binding_energy", "fwhm", "area", "gl_mix", "asymmetry"})
_COMPONENT_STRINGS = frozenset({f.name for f in fields(Component)}) - _COMPONENT_NUMBERS


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _check_keys(raw: dict[str, Any], allowed: frozenset[str], where: str) -> None:
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise FitFormatError(
            f"{where}: unknown key {', '.join(repr(k) for k in unknown)}; "
            f"allowed: {', '.join(sorted(allowed))}"
        )


def _table(raw: object, where: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise FitFormatError(f"{where} must be a table, got {raw!r}")
    return raw


def _array_of_tables(raw: object, where: str) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not all(isinstance(t, dict) for t in raw):
        raise FitFormatError(f"{where} must be an array of tables ([[{where}]]), got {raw!r}")
    return raw


def _number(raw: dict[str, Any], key: str, where: str) -> None:
    if key in raw and not _is_number(raw[key]):
        raise FitFormatError(f"{where}.{key} must be a number, got {raw[key]!r}")


def _string(raw: dict[str, Any], key: str, where: str) -> None:
    if key in raw and not isinstance(raw[key], str):
        raise FitFormatError(f"{where}.{key} must be a string, got {raw[key]!r}")


def _fit(data: dict[str, Any], source: str) -> FitResult:
    _check_keys(data, _TOP_KEYS, "fit file")
    _string(data, "source", "fit file")

    inst = _table(data.get("instrument", {}), "[instrument]")
    _check_keys(inst, _INSTRUMENT_NUMBERS | _INSTRUMENT_STRINGS, "[instrument]")
    for key in _INSTRUMENT_NUMBERS:
        _number(inst, key, "instrument")
    for key in _INSTRUMENT_STRINGS:
        _string(inst, key, "instrument")
    instrument = Instrument(**inst)

    survey_raw = _table(data.get("survey", {}), "[survey]")
    _check_keys(survey_raw, frozenset({"elements"}), "[survey]")
    elements = survey_raw.get("elements", [])
    if not isinstance(elements, list) or not all(isinstance(e, str) for e in elements):
        raise FitFormatError(
            f'survey.elements must be a list of element symbols, such as ["Ti", "O"], '
            f"got {elements!r}"
        )

    spectra = tuple(_spectrum(s) for s in _array_of_tables(data.get("spectrum", []), "spectrum"))
    return FitResult(
        source=data.get("source", source),
        spectra=spectra,
        instrument=instrument,
        survey_elements=frozenset(elements),
    )


def _spectrum(raw: dict[str, Any]) -> Spectrum:
    if "name" not in raw:
        raise FitFormatError("every [[spectrum]] needs a name")
    where = f"spectrum {raw['name']!r}"
    _check_keys(raw, _SPECTRUM_KEYS, where)
    for key in ("name", "background", "background_mode"):
        _string(raw, key, where)
    _number(raw, "step_size", where)
    if "quantified" in raw and not isinstance(raw["quantified"], bool):
        raise FitFormatError(f"{where}.quantified must be true or false, got {raw['quantified']!r}")

    reference: ChargeReference | None = None
    if "charge_reference" in raw:
        ref = _table(raw["charge_reference"], f"{where}.charge_reference")
        rwhere = f"{where}.charge_reference"
        _check_keys(ref, _REFERENCE_KEYS, rwhere)
        if "method" not in ref:
            raise FitFormatError(f"{rwhere} needs a method")
        _string(ref, "method", rwhere)
        _number(ref, "value", rwhere)
        _string(ref, "basis", rwhere)
        reference = ChargeReference(**ref)

    components = tuple(
        _component(c) for c in _array_of_tables(raw.get("component", []), "spectrum.component")
    )
    return Spectrum(
        name=raw["name"],
        components=components,
        background=raw.get("background"),
        background_mode=raw.get("background_mode"),
        step_size=raw.get("step_size"),
        charge_reference=reference,
        quantified=raw.get("quantified", True),
    )


def _component(raw: dict[str, Any]) -> Component:
    missing = _COMPONENT_REQUIRED - raw.keys()
    if missing:
        raise FitFormatError(
            f"component {raw.get('id', '?')} is missing {', '.join(sorted(missing))}"
        )
    where = f"component {raw['id']!r}"
    _check_keys(raw, _COMPONENT_NUMBERS | _COMPONENT_STRINGS, where)
    for key in _COMPONENT_NUMBERS:
        _number(raw, key, where)
    for key in _COMPONENT_STRINGS:
        _string(raw, key, where)
    return Component(**raw)
