"""grimmclub-diagnostics — stable codes, severities, and a readable report.

Domain-agnostic machinery for telling someone what is wrong with their input in
a way they can act on: a stable code, a severity, a message, a *hint*, and where
it came from.

    from grimmclub_diagnostics import Code, DiagnosticBag, Severity

    class Codes:
        UNKNOWN_ID = Code("GC1001", "Unknown registry id", Severity.ERROR)

    bag = DiagnosticBag()
    bag.emit(Codes.UNKNOWN_ID, "block 'x' does not exist", hint="did you mean 'y'?")
    bag.report(console)

Each domain declares its own catalogue and prefix; nothing here knows what any
code means. That is what lets one explanation layer — `grimmclub-mentor` — teach
# Includes standard
from all of them without special-casing each producer.
"""

from __future__ import annotations

from grimmclub_diagnostics.core import (
    Code,
    Diagnostic,
    DiagnosticBag,
    Severity,
)

__all__ = [
    "Code",
    "Diagnostic",
    "DiagnosticBag",
    "Severity",
]
