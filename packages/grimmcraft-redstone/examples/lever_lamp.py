"""Example: a lever powering a lamp through a run of redstone dust.

Run with ``uv run --package grimmcraft-redstone python examples/lever_lamp.py``.
"""

from __future__ import annotations

from grimmcraft_core.coordinates import BlockPos

from grimmcraft_redstone import (
    Circuit,
    Lever,
    RedstoneDust,
    RedstoneLamp,
    Simulator,
    dust_field,
)


def build() -> tuple[Circuit, Lever, RedstoneLamp]:
    """A lever, four dust, and a lamp in a straight line."""
    circuit = Circuit()
    lever = circuit.place(Lever(BlockPos(0, 0, 0), on=False))
    for x in range(1, 5):
        circuit.place(RedstoneDust(BlockPos(x, 0, 0)))
    lamp = circuit.place(RedstoneLamp(BlockPos(5, 0, 0)))
    return circuit, lever, lamp


def main() -> None:
    circuit, lever, lamp = build()
    sim = Simulator(circuit)

    print("flip the lever on:")
    lever.set(True)
    sim.run_until_stable()
    field = dust_field(circuit)
    wire = " ".join(str(field[BlockPos(x, 0, 0)]) for x in range(1, 5))
    print(f"  dust levels: {wire}")
    print(f"  lamp lit:    {lamp.lit}")

    print("flip the lever off:")
    lever.set(False)
    sim.run_until_stable()
    print(f"  lamp lit:    {lamp.lit}")


if __name__ == "__main__":
    main()
