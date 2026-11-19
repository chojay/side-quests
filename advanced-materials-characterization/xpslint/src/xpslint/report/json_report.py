"""Machine-readable renderer."""

from __future__ import annotations

import json
from dataclasses import asdict

from xpslint.engine import Report
from xpslint.models import Outcome


def to_dict(report: Report) -> dict[str, object]:
    return {
        "source": report.fit.source,
        "summary": {
            "failed": len(report.by_outcome(Outcome.FAIL)),
            "passed": len(report.by_outcome(Outcome.PASS)),
            "cannot_check": report.uncovered,
            "not_applicable": len(report.by_outcome(Outcome.NOT_APPLICABLE)),
            "prompt": len(report.by_outcome(Outcome.PROMPT)),
            "checked": report.checked,
            "coverage": report.coverage,
            "disabled": list(report.disabled),
        },
        "diagnostics": [
            {
                **asdict(d),
                "tier": int(d.tier),
                "outcome": d.outcome.value,
                "severity": d.severity.value,
            }
            for d in report.diagnostics
        ],
    }


def render_json(report: Report) -> str:
    return json.dumps(to_dict(report), indent=2)
