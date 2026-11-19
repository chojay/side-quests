"""Report renderers."""

from __future__ import annotations

from xpslint.report.json_report import render_json
from xpslint.report.text import render_text

__all__ = ["render_json", "render_text"]
