"""A first-class diagnostics system for redstone circuits.

Mirrors the ``grimmcraft-compiler`` diagnostics design — stable ``RS####`` codes,
ordered :class:`Severity`, a :class:`Diagnostic` carrying *what* is wrong, *where*
(a :class:`~grimmcraft_core.coordinates.BlockPos`) and *how* to fix it, gathered
in a :class:`DiagnosticBag` — but stays dependency-light (plain-text rendering,
no ``rich``).  :func:`analyze` walks a :class:`~grimmcraft_redstone.circuit.Circuit`
and reports the usual redstone mistakes.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

from grimmcraft_core.coordinates import BlockPos

if TYPE_CHECKING:
    from grimmcraft_redstone.circuit import Circuit


class Severity(IntEnum):
    """Diagnostic severity, ordered so ``max`` is the most serious."""

    INFO = 0
    WARNING = 1
    ERROR = 2

    @property
    def label(self) -> str:
        return {Severity.INFO: "info", Severity.WARNING: "warning",
                Severity.ERROR: "error"}[self]


@dataclass(frozen=True, slots=True)
class Code:
    """A stable diagnostic code (``RS1001``) with a human title."""

    id: str
    title: str
    default_severity: Severity

    def __str__(self) -> str:
        return self.id


class Codes:
    """The catalogue of every diagnostic a circuit analysis can emit."""

    FLOATING_COMPONENT = Code("RS2001", "Component is never powered", Severity.WARNING)
    UNPOWERED_LOAD = Code("RS2002", "Load can never activate", Severity.WARNING)
    COMPARATOR_NO_CONTAINER = Code(
        "RS2003", "Comparator does not read a container", Severity.WARNING
    )
    TORCH_BAD_ATTACHMENT = Code(
        "RS2004", "Redstone torch attached to an invalid block", Severity.WARNING
    )
    LIKELY_CLOCK = Code("RS2005", "Circuit likely oscillates (clock)", Severity.WARNING)
    INVALID_ORIENTATION = Code(
        "RS1001", "Diode faces nothing it can read", Severity.ERROR
    )

    @classmethod
    def all(cls) -> list[Code]:
        """Every registered code, in id order."""
        codes = [v for v in vars(cls).values() if isinstance(v, Code)]
        return sorted(codes, key=lambda c: c.id)


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One problem: severity, stable code, message, actionable hint, and location."""

    severity: Severity
    code: Code
    message: str
    hint: str | None = None
    at: BlockPos | None = None

    def render(self) -> str:
        """A single plain-text line: ``severity CODE: message`` + location/hint."""
        parts = [f"{self.severity.label} {self.code.id}: {self.message}"]
        if self.at is not None:
            parts.append(f"    at ({self.at.x}, {self.at.y}, {self.at.z})")
        if self.hint:
            parts.append(f"    hint: {self.hint}")
        return "\n".join(parts)


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
        at: BlockPos | None = None,
        severity: Severity | None = None,
    ) -> None:
        """Build and append a diagnostic, defaulting severity from ``code``."""
        self.add(
            Diagnostic(severity or code.default_severity, code, message, hint, at)
        )

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def of(self, severity: Severity) -> list[Diagnostic]:
        """Every diagnostic of exactly ``severity``."""
        return [d for d in self._items if d.severity is severity]

    @property
    def warnings(self) -> list[Diagnostic]:
        return self.of(Severity.WARNING)

    @property
    def errors(self) -> list[Diagnostic]:
        return self.of(Severity.ERROR)

    @property
    def has_errors(self) -> bool:
        return any(d.severity is Severity.ERROR for d in self._items)

    def report(self) -> str:
        """A grouped, plain-text report ending in a counts summary."""
        lines: list[str] = []
        for severity in (Severity.ERROR, Severity.WARNING, Severity.INFO):
            for diagnostic in self.of(severity):
                lines.append(diagnostic.render())
        lines.append(
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)"
        )
        return "\n".join(lines)


def analyze(circuit: Circuit) -> DiagnosticBag:
    """Statically inspect ``circuit`` for common redstone mistakes.

    Reports floating (never-powered) components and loads, comparators that do
    not face a container, torches on an invalid attachment block, diodes facing
    nothing readable, and circuits that oscillate (a likely unintended clock, via
    a short bounded simulation).  Messages say what is wrong, where, and how to
    fix it.
    """
    # Imported here (not at module top) to avoid an import cycle: the family
    # modules and simulator import diagnostics' types, not the other way round.
    from grimmcraft_redstone.functions.comparator import Comparator
    from grimmcraft_redstone.functions.repeater import Repeater
    from grimmcraft_redstone.functions.torch import RedstoneTorch
    from grimmcraft_redstone.outputs.base import Load as LoadComponent
    from grimmcraft_redstone.simulation import Simulator

    bag = DiagnosticBag()

    # Run a bounded simulation so "is it ever powered?" and "does it oscillate?"
    # are answered from real behaviour rather than guessed structurally.
    sim = Simulator(circuit)
    result = sim.run_until_stable(max_ticks=200)
    ever_powered = sim.components_ever_powered

    if result.oscillating:
        bag.emit(
            Codes.LIKELY_CLOCK,
            "circuit never stabilised within the tick budget — it oscillates",
            hint="if this clock is intentional, ignore; otherwise break the "
            "feedback loop (e.g. remove a torch or add a repeater lock)",
        )

    for pos, component in circuit.items():
        if isinstance(component, RedstoneTorch):
            if not circuit.is_solid(component.attachment_pos):
                bag.emit(
                    Codes.TORCH_BAD_ATTACHMENT,
                    f"{component.name} at is not attached to a solid block",
                    hint="place the torch on the side/top of a full solid block",
                    at=pos,
                )
        if isinstance(component, Comparator):
            read_pos = component.read_pos
            target = circuit.get(read_pos)
            if target is None or not getattr(target, "IS_CONTAINER", False):
                bag.emit(
                    Codes.COMPARATOR_NO_CONTAINER,
                    f"comparator reads {target.name if target else 'empty space'} "
                    "behind it, which has no container signal",
                    hint="face the comparator away from a container (chest, "
                    "barrel, furnace) to measure its fullness",
                    at=pos,
                )
        if isinstance(component, Repeater):
            if circuit.get(component.read_pos) is None and not any(
                circuit.get(pos.step(d)) for d in (component.facing.opposite,)
            ):
                bag.emit(
                    Codes.INVALID_ORIENTATION,
                    "repeater has nothing wired to its input (back) face",
                    hint="wire redstone into the back of the repeater",
                    at=pos,
                )
        # Floating: a non-source component that never sees power in 200 ticks.
        if pos not in ever_powered and not _is_source(component):
            code = (
                Codes.UNPOWERED_LOAD
                if isinstance(component, LoadComponent)
                else Codes.FLOATING_COMPONENT
            )
            bag.emit(
                code,
                f"{component.name} is never powered during simulation",
                hint="connect it to a power source via dust, a block, or a diode",
                at=pos,
            )

    return bag


def _is_source(component: object) -> bool:
    """Whether ``component`` originates power (so being 'unpowered' is fine)."""
    from grimmcraft_redstone.inputs.base import Source

    return isinstance(component, Source)
