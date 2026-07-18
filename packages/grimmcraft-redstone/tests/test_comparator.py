"""Comparator: compare vs subtract modes, and container reading."""

from grimmcraft_core.coordinates import BlockPos, Direction

from grimmcraft_redstone import Circuit, Comparator, ComparatorMode, Container, Simulator
from grimmcraft_redstone.inputs.sources import AnalogSource
from grimmcraft_data.block import Block

ORIGIN = BlockPos(0, 0, 0)
BACK = BlockPos(0, 0, 1)  # south of origin (comparator faces north)
SIDE = BlockPos(1, 0, 0)  # east of origin


def _analog(pos: BlockPos, level: int) -> AnalogSource:
    source = AnalogSource(pos, block_type=Block.REDSTONE_BLOCK)
    source.emit(level)
    return source


def _output_level(comparator: Comparator, circuit: Circuit) -> int:
    Simulator(circuit).run_until_stable()
    return comparator.output_signal().level


def test_compare_passes_main_through() -> None:
    circuit = Circuit()
    comparator = circuit.place(Comparator(ORIGIN, facing=Direction.NORTH))
    circuit.place(_analog(BACK, 9))
    assert _output_level(comparator, circuit) == 9


def test_compare_blocks_when_side_stronger() -> None:
    circuit = Circuit()
    comparator = circuit.place(Comparator(ORIGIN, facing=Direction.NORTH))
    circuit.place(_analog(BACK, 9))
    circuit.place(_analog(SIDE, 12))
    assert _output_level(comparator, circuit) == 0


def test_compare_passes_when_side_weaker_or_equal() -> None:
    circuit = Circuit()
    comparator = circuit.place(Comparator(ORIGIN, facing=Direction.NORTH))
    circuit.place(_analog(BACK, 9))
    circuit.place(_analog(SIDE, 9))
    assert _output_level(comparator, circuit) == 9


def test_subtract_mode() -> None:
    circuit = Circuit()
    comparator = circuit.place(
        Comparator(ORIGIN, facing=Direction.NORTH, mode=ComparatorMode.SUBTRACT)
    )
    circuit.place(_analog(BACK, 9))
    circuit.place(_analog(SIDE, 4))
    assert _output_level(comparator, circuit) == 5


def test_subtract_floors_at_zero() -> None:
    circuit = Circuit()
    comparator = circuit.place(
        Comparator(ORIGIN, facing=Direction.NORTH, mode=ComparatorMode.SUBTRACT)
    )
    circuit.place(_analog(BACK, 3))
    circuit.place(_analog(SIDE, 10))
    assert _output_level(comparator, circuit) == 0


def test_reads_container_fullness() -> None:
    circuit = Circuit()
    comparator = circuit.place(Comparator(ORIGIN, facing=Direction.NORTH))
    circuit.place(Container(BACK, fullness=7))
    assert _output_level(comparator, circuit) == 7


def test_container_minus_side() -> None:
    circuit = Circuit()
    comparator = circuit.place(
        Comparator(ORIGIN, facing=Direction.NORTH, mode=ComparatorMode.SUBTRACT)
    )
    circuit.place(Container(BACK, fullness=7))
    circuit.place(_analog(SIDE, 2))
    assert _output_level(comparator, circuit) == 5
