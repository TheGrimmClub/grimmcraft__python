"""The redstone torch — the fundamental inverter (NOT), with delay and burnout.

A torch is mounted on an attachment block and emits strong power *unless* that
block is powered — i.e. it inverts.  It reacts one redstone tick (2 game ticks)
after its input changes, and, like the real thing, **burns out** (goes dark) if it
is forced to flip too many times in a short window, recovering after a cool-down.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block

from grimmcraft_redstone.component import RedstoneComponent, SignalChange, SimContext
from grimmcraft_redstone.signal import OFF, Signal, redstone_ticks

#: Reaction delay of a torch: one redstone tick.
TORCH_DELAY = redstone_ticks(1)

#: Burnout fires if a torch changes state more than this many times…
BURNOUT_LIMIT = 8
#: …within this many game ticks…
BURNOUT_WINDOW = 60
#: …and then stays dark for this long before recovering.
BURNOUT_COOLDOWN = 60


class RedstoneTorch(RedstoneComponent):
    """A redstone torch: strong power out when its attachment block is *un*powered.

    ``facing`` is the direction the torch points *away* from its support, so the
    attachment block is one step the other way (a floor torch faces up and is
    attached below).
    """

    BLOCK = Block.REDSTONE_TORCH
    EMITS_POWER = True

    def __init__(
        self, position: BlockPos, *, facing: Direction = Direction.UP, lit: bool = True
    ) -> None:
        super().__init__(position, facing=facing)
        self.on = lit
        self.burned_out = False
        self._delay_left = 0
        self._cooldown = 0
        self._flips: list[int] = []
        self._output = Signal.strong() if lit else OFF

    def inputs(self) -> Iterable[Direction]:
        """A torch takes no face input; it reads its attachment block instead."""
        return ()

    @property
    def attachment_pos(self) -> BlockPos:
        """The block this torch is mounted on."""
        return self.position.step(self.facing.opposite)

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        if self.burned_out:
            self._cooldown -= 1
            if self._cooldown <= 0:
                self.burned_out = False
                self._flips.clear()
            return self._set_output(OFF)

        powered = ctx.block_powered(self.attachment_pos)
        desired = not powered  # the inverter

        if desired != self.on:
            if self._delay_left == 0:
                self._delay_left = TORCH_DELAY
            self._delay_left -= 1
            if self._delay_left == 0:
                self._flip(tick)
        else:
            self._delay_left = 0

        signal = Signal.strong() if self.on and not self.burned_out else OFF
        return self._set_output(signal)

    def _flip(self, tick: int) -> None:
        """Toggle the torch and register the flip for burnout tracking."""
        self.on = not self.on
        self._flips = [t for t in self._flips if tick - t <= BURNOUT_WINDOW]
        self._flips.append(tick)
        if len(self._flips) > BURNOUT_LIMIT:
            self.burned_out = True
            self._cooldown = BURNOUT_COOLDOWN
            self.on = False

    def state_key(self) -> tuple[object, ...]:
        return (
            *super().state_key(),
            self.on,
            self.burned_out,
            self._delay_left,
            self._cooldown,
        )
