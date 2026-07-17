"""A first-class diagnostics system: stable codes, severities, and a report.

Every problem the compiler finds becomes a :class:`Diagnostic` carrying *what* is
wrong (``message``), *where* it came from (``source``) and *how* to fix it
(``hint``), under a stable ``GC####`` :class:`Code`.  Diagnostics collect into a
:class:`DiagnosticBag`, which renders a grouped, colourised report via ``rich``.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import IntEnum

from rich.console import Console
from rich.text import Text


class Severity(IntEnum):
    """Diagnostic severity, ordered so the max is the most serious."""

    INFO = 0
    WARNING = 1
    ERROR = 2

    @property
    def label(self) -> str:
        return {Severity.INFO: "info", Severity.WARNING: "warning",
                Severity.ERROR: "error"}[self]

    @property
    def style(self) -> str:
        return {Severity.INFO: "cyan", Severity.WARNING: "yellow",
                Severity.ERROR: "bold red"}[self]


@dataclass(frozen=True, slots=True)
class Code:
    """A stable diagnostic code (``GC1001``) with a human title."""

    id: str
    title: str
    default_severity: Severity

    def __str__(self) -> str:
        return self.id


# --- the code registry (also the source for docs/diagnostics.md) -------------
class Codes:
    """The catalogue of every diagnostic the compiler can emit."""

    UNKNOWN_ID = Code("GC1001", "Unknown registry id", Severity.ERROR)
    INVALID_RESOURCE_LOCATION = Code(
        "GC1002", "Invalid resource location", Severity.ERROR
    )
    UNRESOLVED_FUNCTION = Code("GC1003", "Unresolved function reference", Severity.ERROR)
    UNRESOLVED_TAG_MEMBER = Code(
        "GC1004", "Unresolved function-tag member", Severity.ERROR
    )
    UNAVAILABLE_FEATURE = Code(
        "GC1005", "Feature unavailable in target version", Severity.ERROR
    )
    UNKNOWN_COMMAND = Code("GC1006", "Unknown command (cannot lower)", Severity.ERROR)
    DEPRECATED_ID = Code("GC2001", "Deprecated id", Severity.WARNING)
    FLAVOR_MISMATCH = Code("GC2002", "Command not portable to this flavor",
                           Severity.WARNING)
    NON_COMPILABLE_GUARD = Code(
        "GC2003", "Runtime guard cannot be compiled", Severity.WARNING
    )
    EMPTY_MACHINE = Code("GC2004", "Machine has no transitions", Severity.WARNING)
    STATS = Code("GC3001", "Compilation summary", Severity.INFO)
    VERIFY_FAILED = Code("GC4001", "Output verification failed", Severity.ERROR)

    @classmethod
    def all(cls) -> list[Code]:
        """Every registered code, in id order."""
        codes = [v for v in vars(cls).values() if isinstance(v, Code)]
        return sorted(codes, key=lambda c: c.id)


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One problem: severity, stable code, message, actionable hint, and source."""

    severity: Severity
    code: Code
    message: str
    hint: str | None = None
    source: str | None = None

    def render(self) -> Text:
        """A single ``rich`` line: ``severity CODE: message`` + hint/source."""
        text = Text()
        text.append(f"{self.severity.label} ", style=self.severity.style)
        text.append(f"{self.code.id}", style="bold")
        text.append(f": {self.message}")
        if self.source:
            text.append(f"\n    at {self.source}", style="dim")
        if self.hint:
            text.append("\n    hint: ", style="green")
            text.append(self.hint, style="green")
        return text


class DiagnosticBag:
    """An ordered collection of diagnostics with counts and a rendered report."""

    def __init__(self) -> None:
        self._items: list[Diagnostic] = []

    def add(self, diagnostic: Diagnostic) -> None:
        """Append a diagnostic."""
        self._items.append(diagnostic)

    def emit(
        self,
        code: Code,
        message: str,
        *,
        hint: str | None = None,
        source: str | None = None,
        severity: Severity | None = None,
    ) -> None:
        """Build and append a diagnostic, defaulting severity from ``code``."""
        self.add(
            Diagnostic(severity or code.default_severity, code, message, hint, source)
        )

    def extend(self, other: DiagnosticBag) -> None:
        """Merge another bag's diagnostics into this one."""
        self._items.extend(other._items)

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def of(self, severity: Severity) -> list[Diagnostic]:
        """Every diagnostic of exactly ``severity``."""
        return [d for d in self._items if d.severity is severity]

    @property
    def errors(self) -> list[Diagnostic]:
        return self.of(Severity.ERROR)

    @property
    def warnings(self) -> list[Diagnostic]:
        return self.of(Severity.WARNING)

    @property
    def has_errors(self) -> bool:
        return any(d.severity is Severity.ERROR for d in self._items)

    def promoted(self) -> DiagnosticBag:
        """A copy with every warning promoted to an error (``--strict``)."""
        bag = DiagnosticBag()
        for d in self._items:
            if d.severity is Severity.WARNING:
                bag.add(Diagnostic(Severity.ERROR, d.code, d.message, d.hint, d.source))
            else:
                bag.add(d)
        return bag

    def counts(self) -> dict[Severity, int]:
        """Number of diagnostics per severity."""
        result = {s: 0 for s in Severity}
        for d in self._items:
            result[d.severity] += 1
        return result

    def report(self, console: Console) -> None:
        """Print a grouped, colourised report ending in a counts summary."""
        for severity in (Severity.ERROR, Severity.WARNING, Severity.INFO):
            group = self.of(severity)
            if not group:
                continue
            for diagnostic in group:
                console.print(diagnostic.render())
        counts = self.counts()
        summary = Text()
        summary.append(f"{counts[Severity.ERROR]} error(s)", style=Severity.ERROR.style)
        summary.append(", ")
        summary.append(
            f"{counts[Severity.WARNING]} warning(s)", style=Severity.WARNING.style
        )
        if counts[Severity.INFO]:
            summary.append(", ")
            summary.append(f"{counts[Severity.INFO]} info", style=Severity.INFO.style)
        console.print(summary)
