"""Example: a 1-bit half-adder — sum = A XOR B, carry = A AND B.

Built from real gate components and evaluated through the simulator.
Run with ``uv run --package grimmcraft-redstone python examples/half_adder.py``.
"""

from __future__ import annotations

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_redstone import AndGate, Circuit, Lever, Simulator, XorGate

# Sum row (z=0): levers A/B either side of the XOR gate.
A_POS = BlockPos(-1, 0, 0)
B_POS = BlockPos(1, 0, 0)
SUM_POS = BlockPos(0, 0, 0)
# Carry row (z=2): a copy of the inputs either side of the AND gate.
CARRY_A_POS = BlockPos(-1, 0, 2)
CARRY_B_POS = BlockPos(1, 0, 2)
CARRY_POS = BlockPos(0, 0, 2)


def evaluate(a_on: bool, b_on: bool) -> tuple[bool, bool]:
    """Return ``(sum_bit, carry_bit)`` for inputs ``a_on`` and ``b_on``."""
    circuit = Circuit()
    circuit.place(Lever(A_POS, on=a_on))
    circuit.place(Lever(B_POS, on=b_on))
    sum_gate = circuit.place(XorGate(SUM_POS))
    circuit.place(Lever(CARRY_A_POS, on=a_on))
    circuit.place(Lever(CARRY_B_POS, on=b_on))
    carry_gate = circuit.place(
        AndGate(CARRY_POS, input_dirs=(Direction.WEST, Direction.EAST))
    )
    Simulator(circuit).run_until_stable()
    return sum_gate.output_signal().is_on, carry_gate.output_signal().is_on


def main() -> None:
    print(" A B | sum carry")
    print("-----+----------")
    for a_on in (False, True):
        for b_on in (False, True):
            sum_bit, carry_bit = evaluate(a_on, b_on)
            print(f" {int(a_on)} {int(b_on)} |  {int(sum_bit)}    {int(carry_bit)}")


if __name__ == "__main__":
    main()
