"""Circuit analysis: floating components, comparator-without-container, clocks."""

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_redstone import (
    Circuit,
    Clock,
    Comparator,
    Container,
    Lever,
    RedstoneDust,
    RedstoneLamp,
)
from grimmcraft_redstone.diagnostics import Codes, Severity, analyze


def test_floating_load_is_reported() -> None:
    circuit = Circuit()
    circuit.place(RedstoneLamp(BlockPos(5, 0, 0)))  # nothing powers it
    bag = analyze(circuit)
    codes = {d.code.id for d in bag}
    assert Codes.UNPOWERED_LOAD.id in codes


def test_powered_load_is_not_reported_floating() -> None:
    circuit = Circuit()
    circuit.place(Lever(BlockPos(0, 0, 0), on=True))
    circuit.place(RedstoneDust(BlockPos(1, 0, 0)))
    circuit.place(RedstoneLamp(BlockPos(2, 0, 0)))
    bag = analyze(circuit)
    floating = [d for d in bag if d.code.id == Codes.UNPOWERED_LOAD.id]
    assert not floating


def test_comparator_without_container_is_reported() -> None:
    circuit = Circuit()
    circuit.place(Comparator(BlockPos(0, 0, 0), facing=Direction.NORTH))
    bag = analyze(circuit)
    assert Codes.COMPARATOR_NO_CONTAINER.id in {d.code.id for d in bag}


def test_comparator_with_container_is_ok() -> None:
    circuit = Circuit()
    circuit.place(Comparator(BlockPos(0, 0, 0), facing=Direction.NORTH))
    circuit.place(Container(BlockPos(0, 0, 1), fullness=4))
    bag = analyze(circuit)
    assert Codes.COMPARATOR_NO_CONTAINER.id not in {d.code.id for d in bag}


def test_clock_reported_as_likely_oscillation() -> None:
    circuit = Circuit()
    circuit.place(Clock(BlockPos(0, 0, 0), period=2))
    bag = analyze(circuit)
    assert Codes.LIKELY_CLOCK.id in {d.code.id for d in bag}


def test_diagnostic_render_has_location_and_hint() -> None:
    circuit = Circuit()
    circuit.place(RedstoneLamp(BlockPos(3, 1, 2)))
    bag = analyze(circuit)
    text = bag.report()
    assert "warning" in text
    assert "(3, 1, 2)" in text
    assert "hint:" in text
    assert bag.of(Severity.WARNING)
