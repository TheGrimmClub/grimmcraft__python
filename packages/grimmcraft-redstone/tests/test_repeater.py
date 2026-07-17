"""Repeater: delay timing, one-way diode, and side-lock."""

from grimmcraft_core.coordinates import BlockPos, Direction

from grimmcraft_redstone import Circuit, Lever, Repeater, Simulator


def _ticks_until_on(delay: int) -> int:
    circuit = Circuit()
    lever = circuit.place(Lever(BlockPos(0, 0, 0), on=False))
    repeater = circuit.place(
        Repeater(BlockPos(1, 0, 0), facing=Direction.EAST, delay=delay)
    )
    sim = Simulator(circuit)
    sim.run_until_stable()
    lever.set(True)
    for _ in range(40):
        sim.step()
        if repeater.output_signal().is_on:
            return sim.tick
    raise AssertionError("repeater never turned on")


def test_delay_increases_with_setting() -> None:
    timings = [_ticks_until_on(d) for d in (1, 2, 3, 4)]
    assert timings == sorted(timings)
    assert len(set(timings)) == 4  # each delay is distinct
    assert timings[0] >= 2  # even the shortest delay is not instantaneous


def test_repeater_is_one_way_diode() -> None:
    circuit = Circuit()
    repeater = circuit.place(Repeater(BlockPos(1, 0, 0), facing=Direction.EAST))
    # Lever on the OUTPUT (front, east) side must not feed back through the diode.
    circuit.place(Lever(BlockPos(2, 0, 0), on=True))
    Simulator(circuit).run_until_stable()
    assert not repeater.output_signal().is_on


def test_repeater_passes_from_back() -> None:
    circuit = Circuit()
    circuit.place(Lever(BlockPos(0, 0, 0), on=True))
    repeater = circuit.place(Repeater(BlockPos(1, 0, 0), facing=Direction.EAST))
    Simulator(circuit).run_until_stable()
    assert repeater.output_signal().is_on
    assert repeater.output_signal().level == 15  # re-emits full strength


def test_side_lock_holds_output() -> None:
    circuit = Circuit()
    lever = circuit.place(Lever(BlockPos(0, 0, 0), on=True))
    main = circuit.place(Repeater(BlockPos(1, 0, 0), facing=Direction.EAST))
    # Locking repeater points north into the side of `main`.
    lock_lever = circuit.place(Lever(BlockPos(1, 0, 2), on=False))
    circuit.place(Repeater(BlockPos(1, 0, 1), facing=Direction.NORTH))
    sim = Simulator(circuit)
    sim.run_until_stable()
    assert main.output_signal().is_on

    # Engage the lock, then drop the main input: output must stay latched on.
    lock_lever.set(True)
    sim.run_until_stable()
    lever.set(False)
    sim.run(6)
    assert main.output_signal().is_on
