"""Fit ingestion.

Only the declarative TOML format at this stage. VAMAS (ISO 14976) via pynxtools-xps,
a CasaXPS adapter, and an lmfit ModelResult adapter arrive at M5. Deferring them is
deliberate: the rule layer is the novel surface, and it is cheaper to iterate on rules
against hand-written TOML than against a binary vendor format.
"""

from __future__ import annotations

from xpslint.io.declarative import load, loads

__all__ = ["load", "loads"]
