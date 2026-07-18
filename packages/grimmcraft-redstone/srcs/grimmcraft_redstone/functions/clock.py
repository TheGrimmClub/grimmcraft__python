"""Clocks — self-oscillating signal generators.

:class:`Clock` is a compact oscillator: it flips its output every ``period`` game
ticks, so a "2-tick clock" is ``Clock(period=2)``.  Physically a clock is a
feedback loop (a torch driving its own attachment, or a repeater loop); the
:class:`~grimmcraft_redstone.simulation.Simulator` detects such feedback as
oscillation instead of hanging.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block
from grimmcraft_redstone.component import RedstoneComponent, SignalChange, SimContext
from grimmcraft_redstone.signal import OFF, Signal


class Clock(RedstoneComponent):
    """A clock that toggles its output every ``period`` game ticks.

    ``period`` is the half-cycle in game ticks (a full on/off cycle is
    ``2 * period``); ``start_on`` sets the initial phase.
    """

    BLOCK = Block.REPEATER
    EMITS_POWER = True

    def __init__(
        self, position: BlockPos, *, period: int = 2, start_on: bool = False
    ) -> None:
        super().__init__(position)
        if period < 1:
            raise ValueError(f"clock period must be >= 1 game tick, got {period}")
        self.period = period
        self.on = start_on
        self._counter = 0
        self._output = Signal.strong() if start_on else OFF

    def inputs(self) -> Iterable[Direction]:
        """A clock is self-driven; it reads nothing."""
        return ()

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        self._counter += 1
        if self._counter >= self.period:
            self._counter = 0
            self.on = not self.on
        return self._set_output(Signal.strong() if self.on else OFF)

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self._counter, self.on)
