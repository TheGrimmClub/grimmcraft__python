"""A first-class diagnostics system: stable codes, severities, and a report.

Domain-agnostic on purpose. A problem becomes a :class:`Diagnostic` carrying
*what* is wrong (``message``), *where* it came from (``source`` / ``location``)
and *how* to fix it (``hint``), under a stable :class:`Code`. Diagnostics
collect into a :class:`DiagnosticBag`, which renders a grouped, colourised
report via ``rich``.

Each domain supplies its own catalogue and code prefix — ``GC####`` for the
compiler, ``GD####`` for the decompiler, ``RS####`` for redstone — by declaring
a class of :class:`Code` constants. Nothing here knows what any of them mean,
which is what lets `grimmclub-mentor` explain all of them the same way.

Two fields describe *where*, because domains differ in what they can say:

* ``source`` — a human label, printed in the report ("door--open-->OPEN").
* ``location`` — the structured original, when there is one (a ``BlockPos``, a
  line number). Untyped here deliberately: this package must not learn about
  anyone's coordinate class.
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
    """A stable diagnostic code (``GC1001``, ``RS2003``) with a human title.

    The id is the contract: it appears in reports, in documentation, and is what
    `grimmclub-mentor` keys an explanation on. Change a message freely; changing
    an id breaks every link to it.
    """

    id: str
    title: str
    default_severity: Severity

    def __str__(self) -> str:
        return self.id


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One problem: severity, stable code, message, actionable hint, and source."""

    severity: Severity
    code: Code
    message: str
    hint: str | None = None
    #: A human label for where the problem is, as printed in the report.
    source: str | None = None
    #: The structured original of `source`, when the domain has one — a
    #: `BlockPos`, a line number, a node. Kept untyped so this package never
    #: has to know about a caller's types; only `source` is ever rendered.
    location: object | None = None

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
        location: object | None = None,
    ) -> None:
        """Build and append a diagnostic, defaulting severity from ``code``."""
        self.add(
            Diagnostic(
                severity or code.default_severity, code, message, hint, source, location
            )
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
                bag.add(
                    Diagnostic(
                        Severity.ERROR, d.code, d.message, d.hint, d.source, d.location
                    )
                )
            else:
                bag.add(d)
        return bag

    def counts(self) -> dict[Severity, int]:
        """Number of diagnostics per severity."""
        result = {s: 0 for s in Severity}
        for d in self._items:
            result[d.severity] += 1
        return result

    def render(self) -> str:
        """The whole report as plain text, for tests, logs and non-rich callers.

        `report()` prints through rich; this returns the same content as a
        string. Both exist because a diagnostics system is used both to show a
        person something and to assert on it.
        """
        lines: list[str] = []
        for severity in (Severity.ERROR, Severity.WARNING, Severity.INFO):
            for diagnostic in self.of(severity):
                lines.append(diagnostic.render().plain)
        counts = self.counts()
        summary = (
            f"{counts[Severity.ERROR]} error(s), "
            f"{counts[Severity.WARNING]} warning(s)"
        )
        if counts[Severity.INFO]:
            summary += f", {counts[Severity.INFO]} info"
        lines.append(summary)
        return "\n".join(lines)

    def report(self, console: Console | None = None) -> str:
        """Print a grouped, colourised report ending in a counts summary.

        Returns the plain-text form too, so a caller that only wants the string
        can pass no console — which is how the redstone analysis is tested.
        """
        if console is None:
            return self.render()
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
        return self.render()
