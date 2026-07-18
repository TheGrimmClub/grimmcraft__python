"""Loads: piston extend/retract + sticky quirk, edge-triggered devices, hopper lock."""

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_redstone import (
    Circuit,
    Hopper,
    Lever,
    NoteBlock,
    Piston,
    Simulator,
    StickyPiston,
)


def test_piston_extends_and_retracts_with_power() -> None:
    circuit = Circuit()
    lever = circuit.place(Lever(BlockPos(0, 0, 0), on=False))
    piston = circuit.place(Piston(BlockPos(1, 0, 0), facing=Direction.EAST))
    sim = Simulator(circuit)

    sim.run_until_stable()
    assert not piston.extended

    lever.set(True)
    sim.run_until_stable()
    assert piston.extended

    lever.set(False)
    sim.run_until_stable()
    assert not piston.extended


def test_sticky_piston_holds_block_on_retract() -> None:
    circuit = Circuit()
    lever = circuit.place(Lever(BlockPos(0, 0, 0), on=True))
    piston = circuit.place(StickyPiston(BlockPos(1, 0, 0), facing=Direction.EAST))
    sim = Simulator(circuit)

    sim.run_until_stable()
    assert piston.extended and piston.holding

    lever.set(False)
    sim.run_until_stable()
    assert not piston.extended
    assert piston.holding  # sticky keeps the pulled block


def test_normal_piston_drops_block_on_retract() -> None:
    circuit = Circuit()
    lever = circuit.place(Lever(BlockPos(0, 0, 0), on=True))
    piston = circuit.place(Piston(BlockPos(1, 0, 0), facing=Direction.EAST))
    sim = Simulator(circuit)
    sim.run_until_stable()
    lever.set(False)
    sim.run_until_stable()
    assert not piston.holding


def test_hopper_is_locked_only_while_powered() -> None:
    circuit = Circuit()
    lever = circuit.place(Lever(BlockPos(0, 0, 0), on=False))
    hopper = circuit.place(Hopper(BlockPos(1, 0, 0)))
    sim = Simulator(circuit)
    sim.run_until_stable()
    assert not hopper.locked
    lever.set(True)
    sim.run_until_stable()
    assert hopper.locked


def test_note_block_fires_once_per_rising_edge() -> None:
    circuit = Circuit()
    lever = circuit.place(Lever(BlockPos(0, 0, 0), on=False))
    note = circuit.place(NoteBlock(BlockPos(1, 0, 0)))
    sim = Simulator(circuit)
    sim.run_until_stable()
    assert note.plays == 0

    lever.set(True)
    sim.run_until_stable()
    assert note.plays == 1

    # Holding power does not replay.
    sim.run(5)
    assert note.plays == 1

    lever.set(False)
    sim.run_until_stable()
    lever.set(True)
    sim.run_until_stable()
    assert note.plays == 2
