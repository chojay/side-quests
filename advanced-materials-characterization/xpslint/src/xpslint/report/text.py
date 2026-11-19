"""Terminal renderer.

The coverage line is not optional and not suppressible. A fit that declares no metadata
would otherwise pass silently, since every rule degrades to cannot-check. Printing
coverage makes a trivial pass visibly a trivial pass.
"""

from __future__ import annotations

import os
import sys

from xpslint.engine import Report
from xpslint.models import Diagnostic, Outcome

_COLORS = {
    Outcome.FAIL: "\033[31m",
    Outcome.CANNOT_CHECK: "\033[33m",
    Outcome.PROMPT: "\033[36m",
    Outcome.PASS: "\033[32m",
    Outcome.NOT_APPLICABLE: "\033[90m",
}
_DIM = "\033[90m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

_LABEL = {
    Outcome.FAIL: "fail",
    Outcome.CANNOT_CHECK: "cannot-check",
    Outcome.PROMPT: "prompt",
    Outcome.PASS: "pass",
    Outcome.NOT_APPLICABLE: "n/a",
}

_SHOWN_BY_DEFAULT = (Outcome.FAIL, Outcome.CANNOT_CHECK, Outcome.PROMPT)


def _use_color(stream: object) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return bool(getattr(stream, "isatty", lambda: False)())


def render_text(report: Report, *, show_all: bool = False, color: bool | None = None) -> str:
    if color is None:
        color = _use_color(sys.stdout)

    def paint(text: str, code: str) -> str:
        return f"{code}{text}{_RESET}" if color else text

    wanted = tuple(Outcome) if show_all else _SHOWN_BY_DEFAULT
    shown = [d for d in report.diagnostics if d.outcome in wanted]

    lines: list[str] = []
    lines.append(paint(report.fit.source, _BOLD))
    if not shown:
        lines.append("  no findings")
    else:
        for diag in sorted(shown, key=lambda d: (_order(d), d.target, d.code)):
            label = _LABEL[diag.outcome]
            head = (
                f"  {paint(label.rjust(12), _COLORS[diag.outcome])} "
                f"{diag.code}  [{diag.tier}] {diag.target}"
            )
            lines.append(head)
            lines.append(f"{'':>16}{diag.message}")
            if diag.observed:
                lines.append(f"{'':>16}{paint('observed: ' + diag.observed, _DIM)}")
            if diag.expected:
                lines.append(f"{'':>16}{paint('expected: ' + diag.expected, _DIM)}")
            if diag.hint:
                lines.append(f"{'':>16}{paint('hint:     ' + diag.hint, _DIM)}")
            if diag.citation:
                lines.append(f"{'':>16}{paint('cite:     ' + diag.citation, _DIM)}")
            lines.append("")

    counts = {outcome: len(report.by_outcome(outcome)) for outcome in Outcome}
    summary = (
        f"{counts[Outcome.FAIL]} failed, "
        f"{counts[Outcome.PASS]} passed, "
        f"{counts[Outcome.CANNOT_CHECK]} unchecked, "
        f"{counts[Outcome.NOT_APPLICABLE]} n/a, "
        f"{counts[Outcome.PROMPT]} prompt"
    )
    lines.append(summary)

    coverage = report.coverage
    if coverage is None:
        lines.append(paint("coverage: no checks were applicable", _DIM))
    else:
        total = report.checked + report.uncovered
        pct = f"{coverage * 100:.0f}%"
        text = f"coverage: {report.checked}/{total} checks ({pct})"
        lines.append(paint(text, _COLORS[Outcome.FAIL] if coverage < 0.5 else _DIM))
    if report.disabled:
        n = len(report.disabled)
        noun = "rule" if n == 1 else "rules"
        lines.append(
            f"{n} {noun} disabled by config, not in coverage: {', '.join(report.disabled)}"
        )
    return "\n".join(lines)


def _order(diag: Diagnostic) -> int:
    return {
        Outcome.FAIL: 0,
        Outcome.CANNOT_CHECK: 1,
        Outcome.PROMPT: 2,
        Outcome.PASS: 3,
        Outcome.NOT_APPLICABLE: 4,
    }[diag.outcome]
