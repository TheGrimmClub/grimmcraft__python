"""Simulator: stability, oscillation detection, and determinism."""

from grimmcraft_core.coordinates import BlockPos
from grimmcraft_redstone import (
    Circuit,
    Clock,
    Lever,
    RedstoneDust,
    RedstoneLamp,
    Simulator,
)


def _lever_lamp(on: bool) -> tuple[Circuit, RedstoneLamp]:
    circuit = Circuit()
    circuit.place(Lever(BlockPos(0, 0, 0), on=on))
    circuit.place(RedstoneDust(BlockPos(1, 0, 0)))
    lamp = circuit.place(RedstoneLamp(BlockPos(2, 0, 0)))
    return circuit, lamp


def test_simple_circuit_stabilises() -> None:
    circuit, lamp = _lever_lamp(on=True)
    result = Simulator(circuit).run_until_stable()
    assert result.stable
    assert not result.oscillating
    assert lamp.lit


def test_unpowered_circuit_is_dark() -> None:
    circuit, lamp = _lever_lamp(on=False)
    Simulator(circuit).run_until_stable()
    assert not lamp.lit


def test_clock_is_detected_as_oscillating() -> None:
    circuit = Circuit()
    circuit.place(Clock(BlockPos(0, 0, 0), period=2))
    result = Simulator(circuit).run_until_stable(max_ticks=100)
    assert result.oscillating
    assert not result.stable
    assert result.period is not None


def test_determinism_same_result_regardless_of_run() -> None:
    circuit1, lamp1 = _lever_lamp(on=True)
    circuit2, lamp2 = _lever_lamp(on=True)
    Simulator(circuit1).run_until_stable()
    # Step the second one by hand a different number of times, then finish.
    sim2 = Simulator(circuit2)
    sim2.run(3)
    sim2.run_until_stable()
    assert lamp1.lit == lamp2.lit is True
