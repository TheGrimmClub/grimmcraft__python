"""The *connectors* family: components that transmit signal without originating it.

:class:`RedstoneDust` is the wire — the engine resolves its power globally (one
level lost per block, 15-block range) and this component just reports the level it
was assigned.  :class:`SolidBlock` is a full block that can be *strongly* powered
and re-emit to everything adjacent; it is how power crosses from a diode into a
wire on the far side.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block
from grimmcraft_redstone.component import RedstoneComponent, SignalChange, SimContext
from grimmcraft_redstone.signal import OFF, Signal


class RedstoneDust(RedstoneComponent):
    """Redstone wire: carries power between components, attenuating 1 per block.

    Dust neither originates nor consumes power; the :class:`Simulator` computes
    each dust cell's level (see ``_resolve_dust``) and this component republishes
    it as a weak signal so it is observable and included in oscillation state.
    """

    BLOCK = Block.REDSTONE_WIRE
    IS_DUST = True
    EMITS_POWER = False

    def __init__(self, position: BlockPos) -> None:
        super().__init__(position)
        self.level = 0

    def inputs(self) -> Iterable[Direction]:
        """Dust connects to all four horizontal neighbours (and up/down ramps)."""
        return tuple(Direction)

    def conducts(self, direction: Direction) -> bool:
        """Dust conducts signal out of every face it is wired along."""
        return True

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        self.level = ctx.dust_power(self.position)
        signal = Signal.weak(self.level) if self.level > 0 else OFF
        return self._set_output(signal)

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.level)


class SolidBlock(RedstoneComponent):
    """A full opaque block: conducts strong power and holds torches.

    Passive on its own; it matters because a *strongly* powered solid block
    re-emits power to adjacent dust and components (and gives a redstone torch a
    valid attachment).
    """

    BLOCK = Block.STONE
    IS_SOLID = True
    EMITS_POWER = False

    def conducts(self, direction: Direction) -> bool:
        """A solid block conducts strong power to every face."""
        return True
