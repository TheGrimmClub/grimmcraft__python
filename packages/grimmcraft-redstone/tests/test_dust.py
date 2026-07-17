"""Redstone dust: 1 level lost per block, 15-block range."""

from grimmcraft_core.coordinates import BlockPos

from grimmcraft_redstone import Circuit, Lever, RedstoneDust, Simulator, dust_field


def _line(length: int) -> tuple[Circuit, list[BlockPos]]:
    circuit = Circuit()
    circuit.place(Lever(BlockPos(0, 0, 0), on=True))
    positions = [BlockPos(x, 0, 0) for x in range(1, length + 1)]
    for pos in positions:
        circuit.place(RedstoneDust(pos))
    Simulator(circuit).run_until_stable()
    return circuit, positions


def test_first_dust_is_full_strength() -> None:
    circuit, positions = _line(3)
    field = dust_field(circuit)
    assert field[positions[0]] == 15


def test_attenuation_is_one_per_block() -> None:
    circuit, positions = _line(16)
    field = dust_field(circuit)
    # positions[i] is x = i+1, so power should be 15 - i.
    for i, pos in enumerate(positions):
        assert field[pos] == max(0, 15 - i)


def test_range_is_fifteen_blocks() -> None:
    circuit, positions = _line(16)
    field = dust_field(circuit)
    assert field[BlockPos(15, 0, 0)] == 1
    assert field[BlockPos(16, 0, 0)] == 0


def test_dust_off_when_source_off() -> None:
    circuit = Circuit()
    circuit.place(Lever(BlockPos(0, 0, 0), on=False))
    circuit.place(RedstoneDust(BlockPos(1, 0, 0)))
    Simulator(circuit).run_until_stable()
    assert dust_field(circuit)[BlockPos(1, 0, 0)] == 0
