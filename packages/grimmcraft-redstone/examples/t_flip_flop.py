"""Example: a T-flip-flop — each input pulse toggles a latched output.

A piston T-flip-flop is fiddly to wire block-by-block; here it is expressed as a
small custom :class:`~grimmcraft_redstone.component.RedstoneComponent`, which also
shows how to extend the model with your own behaviour.  Run with
``uv run --package grimmcraft-redstone python examples/t_flip_flop.py``.
"""

from __future__ import annotations

from collections.abc import Sequence

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block

from grimmcraft_redstone import Button, Circuit, Simulator
from grimmcraft_redstone.component import RedstoneComponent, SignalChange, SimContext
from grimmcraft_redstone.signal import OFF, Signal


class TFlipFlop(RedstoneComponent):
    """Latches; toggles its output on every rising edge of its input face."""

    BLOCK = Block.STICKY_PISTON
    EMITS_POWER = True

    def __init__(self, position: BlockPos, *, listen: Direction = Direction.WEST) -> None:
        super().__init__(position)
        self._listen = listen
        self._state = False
        self._was_powered = False

    def inputs(self) -> tuple[Direction, ...]:
        return (self._listen,)

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        powered = ctx.power_into(self.position, self._listen).is_on
        if powered and not self._was_powered:  # rising edge
            self._state = not self._state
        self._was_powered = powered
        return self._set_output(Signal.strong() if self._state else OFF)

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self._state, self._was_powered)


def main() -> None:
    circuit = Circuit()
    button = circuit.place(Button(BlockPos(-1, 0, 0), material="stone"))
    flip = circuit.place(TFlipFlop(BlockPos(0, 0, 0)))
    sim = Simulator(circuit)

    print("each button press flips the latch:")
    for press in range(1, 5):
        button.press()
        sim.run_until_stable()
        print(f"  press {press}: output = {'ON' if flip.output_signal().is_on else 'off'}")


if __name__ == "__main__":
    main()
