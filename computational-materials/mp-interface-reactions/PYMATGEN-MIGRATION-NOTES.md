# Interface Reaction Script - Debug & Fix Notes
**Date**: 2026-02-17
**Fixed Script**: `run_interface_reactions.py`

---

## Summary

The original `materials_project_reaction.py` was producing **incorrect results** - all reactions fell through to a hardcoded fallback function (`get_predefined_reaction`) that returned generic placeholder text and fabricated energy values. The actual Materials Project API calculations via `InterfacialReactivity` never executed successfully.

Previous output showed every pair collapsing to one of two fabrications:
a hardcoded "-0.5000 eV/atom" placeholder energy with generic reaction text,
or "No reaction" whenever the reference element's symbol appeared inside the
counterparty formula - a string containment check standing in for
thermodynamics.

---

## Issues Identified

### Issue 1: Broken Python Environment (pydantic v1/v2 incompatibility)

**Symptom**: `MPRester` import fails with `PydanticImportError: BaseSettings has been moved to pydantic-settings`

**Root Cause**: The system anaconda Python 3.8 had `pymatgen` installed alongside `pydantic>=2.0`, but the `emmet-core` package still imported `BaseSettings` from `pydantic` (v1 location) instead of `pydantic-settings`.

**Fix**: Created a fresh Python 3.12 venv (`/opt/homebrew/bin/python3.12`) with compatible versions:
- `pymatgen==2025.10.7`
- `mp-api==0.46.0`
- `pydantic==2.12.5` + `pydantic-settings==2.13.0`

---

### Issue 2: `InterfacialReactivity` API Changed - Wrong Constructor Arguments

**Symptom**: `InterfacialReactivity()` silently failed or raised exceptions, falling to the `except` block.

**Root Cause**: The original code used the **old** constructor signature:
```python
# OLD (broken)
analyzer = InterfacialReactivity(
    ref_entry.composition,
    mat_entry.composition,
    processed_entries,           # <-- list of entries (WRONG for new API)
    norm=True,
    include_no_mixing_energy=True,  # <-- removed parameter
    pd_non_grand=True               # <-- removed parameter
)
```

The **current** pymatgen signature is:
```python
# NEW (correct)
InterfacialReactivity(
    c1: Composition,
    c2: Composition,
    pd: PhaseDiagram,    # <-- requires a PhaseDiagram object, not raw entries
    norm: bool = True,
    use_hull_energy: bool = False
)
```

**Changes**:
1. Build a `PhaseDiagram` object first from processed entries
2. Pass `pd_obj` instead of entry list
3. Removed `include_no_mixing_energy` and `pd_non_grand` kwargs (no longer exist)
4. Added `use_hull_energy=False` (new optional parameter)

---

### Issue 3: `analyzer.minimum()` - Property vs Method

**Symptom**: `TypeError: 'tuple' object is not callable`

**Root Cause**: `minimum` is a **property** (returns a tuple), not a method. The old code called `analyzer.minimum()` with parentheses.

**Fix**: Use `analyzer.minimum` (no parentheses). Returns `(x_fraction, energy_eV_per_atom)`.

---

### Issue 4: `get_kinks()` Return Format Changed

**Symptom**: Incorrect indexing of kinks data.

**Root Cause**: The old code accessed `analyzer.get_kinks()[0][1]` assuming a different structure. The current format is a list of 5-tuples:
```
(index, x_fraction, energy_eV_per_atom, Reaction_object, energy_kJ_per_mol)
```

**Fix**: Updated indexing to correctly extract all five fields from each kink tuple.

---

### Issue 5: Fallback Function Masks Real Errors

**Symptom**: Script appeared to "work" but returned fabricated data.

**Root Cause**: `get_predefined_reaction()` catches any failure and returns hardcoded values:
- `-0.5 eV/atom` for anything containing "O" (oxygen)
- `-0.7 eV/atom` for anything containing "F"
- `0.0 eV/atom` (stable!) for anything containing the reference element name as a substring

This meant any pair whose counterparty formula contained the reference element's symbol was reported as "Stable" (the same check would call Si | SiO2 stable) - a string match, not thermodynamics. The real minimum-energy reactions for such pairs are often strongly exothermic.

**Fix**: Removed the entire fallback function. Errors now propagate and are reported clearly in the output.

---

### Issue 6: `has_reaction` Attribute No Longer Exists

**Symptom**: `AttributeError` on `analyzer.has_reaction`

**Root Cause**: This attribute was removed from `InterfacialReactivity`. Reaction presence is now determined by checking if any kink has negative energy.

**Fix**: Check interior kinks (0 < x < 1) for negative reaction energies instead.

---

### Issue 7: `critical_comp_rxn` Attribute Removed

**Symptom**: `AttributeError` when trying to format products.

**Root Cause**: The old code accessed `analyzer.critical_comp_rxn` to build reaction strings. This attribute no longer exists.

**Fix**: Use `get_kinks()` which returns `Reaction` objects directly with proper `__str__` formatting (e.g., `"0.213 Ta2O5 + 0.787 Si -> 0.085 Ta5Si3 + 0.532 SiO2"`).

---

## Validation after the fixes

The repaired script was validated by re-running a four-material benchmark
of textbook-reactive interfaces and checking every minimum-energy reaction
and magnitude against known chemistry and the Materials Project website's
own interface-reaction app; all four matched. The example figures shipped
with this export were then regenerated with the current script on the
foundry-chemistry defaults described in the README (Si | Ta2O5 and
Si | Si3N4).

## Files (as exported here)

| File | Description |
|------|-------------|
| `run_interface_reactions.py` | The fixed script with correct API usage |
| `compare_0K_vs_300K.py` | 0 K vs 300 K results comparator |
| `PYMATGEN-MIGRATION-NOTES.md` | This file |
