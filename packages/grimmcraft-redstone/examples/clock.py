"""Example: a 2-tick clock, and how the simulator reports oscillation.

Run with ``uv run --package grimmcraft-redstone python examples/clock.py``.
"""

from __future__ import annotations

from grimmcraft_core.coordinates import BlockPos
from grimmcraft_redstone import Circuit, Clock, Simulator


def main() -> None:
    circuit = Circuit()
    clock = circuit.place(Clock(BlockPos(0, 0, 0), period=2))
    sim = Simulator(circuit)

    print("output per game tick:")
    for _ in range(8):
        sim.step()
        state = "ON " if clock.output_signal().is_on else "off"
        print(f"  tick {sim.tick:2d}: {state}")

    fresh = Simulator(Circuit())
    fresh.circuit.place(Clock(BlockPos(0, 0, 0), period=2))
    result = fresh.run_until_stable(max_ticks=100)
    print(
        f"\nrun_until_stable: oscillating={result.oscillating} "
        f"period={result.period} (detected, not hung)"
    )


if __name__ == "__main__":
    main()
