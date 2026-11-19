"""xpslint: a physics-rule linter for XPS peak fits.

xpslint never performs fitting. It audits a finished fit against rules that carry an
epistemic *tier* as well as a severity:

    Tier 1  derivable physics       unconditional error, cannot be downgraded
    Tier 2  instrument-specific     requires declared metadata, else ``cannot-check``
    Tier 3  convention              never fails, only prompts for a declaration
"""

from xpslint.engine import Report, run
from xpslint.models import (
    ChargeReference,
    Component,
    Diagnostic,
    FitResult,
    Instrument,
    Outcome,
    Severity,
    Spectrum,
    Tier,
)

__version__ = "0.1.0"

__all__ = [
    "ChargeReference",
    "Component",
    "Diagnostic",
    "FitResult",
    "Instrument",
    "Outcome",
    "Report",
    "Severity",
    "Spectrum",
    "Tier",
    "run",
]
