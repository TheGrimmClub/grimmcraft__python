"""A first-class diagnostics system for redstone circuits.

The machinery comes from ``grimmclub-diagnostics``; what stays here is the
``RS####`` catalogue and :func:`analyze`, which walks a
:class:`~grimmcraft_redstone.circuit.Circuit` and reports the usual redstone
mistakes.

A circuit fault has a real position, so these diagnostics carry the
:class:`~grimmcraft_core.coordinates.BlockPos` in ``location`` and its readable
form — ``(3, 1, 2)`` — in ``source``. The structured value survives for tools
that want to jump to the fault; the label is what a person reads.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from grimmclub_diagnostics import Code, Diagnostic, DiagnosticBag, Severity
from grimmcraft_core.coordinates import BlockPos

if TYPE_CHECKING:
    from grimmcraft_redstone.circuit import Circuit

# Re-exported so `from grimmcraft_redstone.diagnostics import DiagnosticBag`
# keeps working: the machinery moved to grimmclub-diagnostics, the RS catalogue
# below stayed here. Naming them also stops ruff pruning the imports.
__all__ = ["Code", "Codes", "Diagnostic", "DiagnosticBag", "Severity", "analyze"]


def _position_label(pos: BlockPos) -> str:
    """A position as it reads in a report: ``(3, 1, 2)``.

    `str(BlockPos(...))` gives the dataclass repr, which is noise in a message
    aimed at someone looking at a circuit.
    """
    return f"({pos.x}, {pos.y}, {pos.z})"


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
                    source=_position_label(pos),
                    location=pos,
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
                    source=_position_label(pos),
                    location=pos,
                )
        if isinstance(component, Repeater):
            if circuit.get(component.read_pos) is None and not any(
                circuit.get(pos.step(d)) for d in (component.facing.opposite,)
            ):
                bag.emit(
                    Codes.INVALID_ORIENTATION,
                    "repeater has nothing wired to its input (back) face",
                    hint="wire redstone into the back of the repeater",
                    source=_position_label(pos),
                    location=pos,
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
                source=_position_label(pos),
                location=pos,
            )

    return bag


def _is_source(component: object) -> bool:
    """Whether ``component`` originates power (so being 'unpowered' is fine)."""
    from grimmcraft_redstone.inputs.base import Source

    return isinstance(component, Source)
