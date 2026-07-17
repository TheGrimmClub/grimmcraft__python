"""The redstone repeater — a one-directional diode with adjustable delay and lock.

A repeater reads only its back face, outputs full strength toward its front after
a delay of **1-4 redstone ticks**, and can be *locked* (output frozen) by a
powered repeater or comparator facing into its side.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block

from grimmcraft_redstone.component import RedstoneComponent, SignalChange, SimContext
from grimmcraft_redstone.signal import OFF, Signal, redstone_ticks


class Repeater(RedstoneComponent):
    """A repeater: a delayed, one-way, full-strength diode.

    ``facing`` is the output direction; the input is the opposite (back) face.
    ``delay`` is in redstone ticks (1-4).  A repeater always re-emits full power,
    so it also cleans up an attenuated signal back to 15.
    """

    BLOCK = Block.REPEATER
    EMITS_POWER = True

    def __init__(
        self,
        position: BlockPos,
        *,
        facing: Direction = Direction.NORTH,
        delay: int = 1,
    ) -> None:
        super().__init__(position, facing=facing)
        self.delay = self._validate_delay(delay)
        self._buffer: list[bool] = [False] * redstone_ticks(self.delay)

    @staticmethod
    def _validate_delay(delay: int) -> int:
        if not 1 <= delay <= 4:
            raise ValueError(f"repeater delay must be 1-4 redstone ticks, got {delay}")
        return delay

    def set_delay(self, delay: int) -> Repeater:
        """Change the delay (1-4 rt), resizing the buffer; returns self."""
        self.delay = self._validate_delay(delay)
        target = redstone_ticks(self.delay)
        current = self._buffer[-1] if self._buffer else False
        self._buffer = ([current] * target)[:target] or [False] * target
        return self

    def inputs(self) -> Iterable[Direction]:
        """A repeater reads only its back face."""
        return (self.facing.opposite,)

    @property
    def read_pos(self) -> BlockPos:
        """The cell feeding this repeater (behind it)."""
        return self.position.step(self.facing.opposite)

    def _side_dirs(self) -> tuple[Direction, Direction]:
        """The two horizontal faces perpendicular to ``facing`` (lock inputs)."""
        horizontals = [
            Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST
        ]
        if self.facing in horizontals:
            axis = {Direction.NORTH, Direction.SOUTH}
            if self.facing in axis:
                return (Direction.EAST, Direction.WEST)
            return (Direction.NORTH, Direction.SOUTH)
        return (Direction.NORTH, Direction.SOUTH)

    def is_locked(self, ctx: SimContext) -> bool:
        """Whether a powered repeater/comparator faces into a side, locking output."""
        for direction in self._side_dirs():
            neighbor = ctx.component_at(self.position.step(direction))
            if neighbor is None or not neighbor.output_signal().is_on:
                continue
            # Only a diode pointing *into* this repeater locks it.
            if isinstance(neighbor, Repeater) and neighbor.facing is direction.opposite:
                return True
            if type(neighbor).__name__ == "Comparator" and (
                neighbor.facing is direction.opposite
            ):
                return True
        return False

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        if self.is_locked(ctx):
            return []  # frozen: neither sample nor shift
        sample = ctx.power_into(self.position, self.facing.opposite).is_on
        self._buffer.append(sample)
        emitted = self._buffer.pop(0)
        return self._set_output(Signal.strong() if emitted else OFF)

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), tuple(self._buffer))
