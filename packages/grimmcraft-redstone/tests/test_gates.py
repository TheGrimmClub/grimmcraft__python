"""Logic-gate truth tables, driven through the real simulator."""

import pytest
from grimmcraft_core.coordinates import BlockPos, Direction

from grimmcraft_redstone import (
    AndGate,
    Circuit,
    Lever,
    NandGate,
    NotGate,
    OrGate,
    Simulator,
    XorGate,
)
from grimmcraft_redstone.functions.gates import LogicGate

ORIGIN = BlockPos(0, 0, 0)
WEST = BlockPos(-1, 0, 0)
EAST = BlockPos(1, 0, 0)


def _run_binary(gate_cls: type[LogicGate], a: bool, b: bool) -> bool:
    circuit = Circuit()
    gate = circuit.place(gate_cls(ORIGIN))
    circuit.place(Lever(WEST, on=a))
    circuit.place(Lever(EAST, on=b))
    Simulator(circuit).run_until_stable()
    return gate.output_signal().is_on


def _run_unary(a: bool) -> bool:
    circuit = Circuit()
    gate = circuit.place(NotGate(ORIGIN))
    circuit.place(Lever(WEST, on=a))
    Simulator(circuit).run_until_stable()
    return gate.output_signal().is_on


@pytest.mark.parametrize("a,expected", [(False, True), (True, False)])
def test_not_truth_table(a: bool, expected: bool) -> None:
    assert _run_unary(a) is expected


@pytest.mark.parametrize(
    "a,b,expected",
    [(False, False, False), (False, True, False), (True, False, False), (True, True, True)],
)
def test_and_truth_table(a: bool, b: bool, expected: bool) -> None:
    assert _run_binary(AndGate, a, b) is expected


@pytest.mark.parametrize(
    "a,b,expected",
    [(False, False, False), (False, True, True), (True, False, True), (True, True, True)],
)
def test_or_truth_table(a: bool, b: bool, expected: bool) -> None:
    assert _run_binary(OrGate, a, b) is expected


@pytest.mark.parametrize(
    "a,b,expected",
    [(False, False, True), (False, True, True), (True, False, True), (True, True, False)],
)
def test_nand_truth_table(a: bool, b: bool, expected: bool) -> None:
    assert _run_binary(NandGate, a, b) is expected


@pytest.mark.parametrize(
    "a,b,expected",
    [(False, False, False), (False, True, True), (True, False, True), (True, True, False)],
)
def test_xor_truth_table(a: bool, b: bool, expected: bool) -> None:
    assert _run_binary(XorGate, a, b) is expected


def test_custom_input_directions() -> None:
    circuit = Circuit()
    gate = circuit.place(AndGate(ORIGIN, input_dirs=(Direction.NORTH, Direction.SOUTH)))
    circuit.place(Lever(BlockPos(0, 0, -1), on=True))
    circuit.place(Lever(BlockPos(0, 0, 1), on=True))
    Simulator(circuit).run_until_stable()
    assert gate.output_signal().is_on
