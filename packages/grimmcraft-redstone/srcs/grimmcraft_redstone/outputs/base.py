"""The :class:`Load` base for the *outputs* family — components that consume power.

A load reacts to the power arriving on its faces; it does not emit
(``EMITS_POWER`` stays false).  The base tracks the powered state and the
rising/falling edges so edge-triggered loads (dispensers, note blocks, bells) can
fire once per activation.
"""

from __future__ import annotations

from collections.abc import Sequence

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block

from grimmcraft_redstone.component import RedstoneComponent, SignalChange, SimContext


class Load(RedstoneComponent):
    """A component switched on by incoming power (lamp, piston, door, …)."""

    EMITS_POWER = False

    def __init__(
        self,
        position: BlockPos,
        *,
        facing: Direction = Direction.UP,
        block_type: Block | None = None,
    ) -> None:
        super().__init__(position, facing=facing, block_type=block_type)
        self.active = False
        self._was_powered = False

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        powered = ctx.incoming_power(self).is_on
        rising = powered and not self._was_powered
        falling = (not powered) and self._was_powered
        self._on_power(powered, rising=rising, falling=falling)
        self._was_powered = powered
        self.active = powered
        return ()

    def _on_power(self, powered: bool, *, rising: bool, falling: bool) -> None:
        """Hook for subclasses: react to the current power / its edges."""

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.active)
