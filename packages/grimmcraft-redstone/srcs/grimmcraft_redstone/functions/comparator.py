"""The redstone comparator — signal-strength maths in two modes.

A comparator reads a *main* input from its back face (or the container behind it)
and a *side* input from its sides.  In **compare** mode it passes the main signal
through, but only if no side exceeds it; in **subtract** mode it outputs
``main - side`` (floored at 0).  Reacts after one redstone tick.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import Enum

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block
from grimmcraft_redstone.component import RedstoneComponent, SignalChange, SimContext
from grimmcraft_redstone.signal import OFF, Signal, clamp_power, redstone_ticks


class ComparatorMode(Enum):
    """A comparator's operating mode."""

    COMPARE = "compare"
    SUBTRACT = "subtract"


class Container(RedstoneComponent):
    """A block a comparator can read (chest, barrel, furnace, …).

    Its comparator signal strength scales with how full it is; set ``fullness``
    directly, or ``fill(slots_used, slots_total, ...)`` for the real formula.
    """

    BLOCK = Block.CHEST if hasattr(Block, "CHEST") else Block.STONE
    IS_CONTAINER = True
    EMITS_POWER = False

    def __init__(self, position: BlockPos, *, fullness: int = 0) -> None:
        super().__init__(position)
        self.fullness = clamp_power(fullness)

    def set_fullness(self, level: int) -> Container:
        """Set the comparator reading (0-15) directly; returns self."""
        self.fullness = clamp_power(level)
        return self

    def signal_strength(self) -> int:
        """The comparator signal strength (0-15) this container emits when read."""
        return self.fullness

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.fullness)


class Comparator(RedstoneComponent):
    """A comparator: passes or subtracts signals, and reads containers.

    ``facing`` is the output direction; the back (opposite) face is the main
    input, which reads a :class:`Container` behind it if present.
    """

    BLOCK = Block.COMPARATOR
    EMITS_POWER = True

    def __init__(
        self,
        position: BlockPos,
        *,
        facing: Direction = Direction.NORTH,
        mode: ComparatorMode = ComparatorMode.COMPARE,
    ) -> None:
        super().__init__(position, facing=facing)
        self.mode = mode
        self._buffer: list[int] = [0] * redstone_ticks(1)

    def toggle_mode(self) -> Comparator:
        """Switch between compare and subtract; returns self."""
        self.mode = (
            ComparatorMode.SUBTRACT
            if self.mode is ComparatorMode.COMPARE
            else ComparatorMode.COMPARE
        )
        return self

    def inputs(self) -> Iterable[Direction]:
        """Main (back) plus the two side faces."""
        return (self.facing.opposite, *self._side_dirs())

    @property
    def read_pos(self) -> BlockPos:
        """The cell behind the comparator (its main input / container)."""
        return self.position.step(self.facing.opposite)

    def _side_dirs(self) -> tuple[Direction, Direction]:
        if self.facing in (Direction.NORTH, Direction.SOUTH):
            return (Direction.EAST, Direction.WEST)
        if self.facing in (Direction.EAST, Direction.WEST):
            return (Direction.NORTH, Direction.SOUTH)
        return (Direction.NORTH, Direction.SOUTH)

    def _main_input(self, ctx: SimContext) -> int:
        target = ctx.component_at(self.read_pos)
        if isinstance(target, Container):
            return target.signal_strength()
        return ctx.power_into(self.position, self.facing.opposite).level

    def _side_input(self, ctx: SimContext) -> int:
        return max(
            (ctx.power_into(self.position, d).level for d in self._side_dirs()),
            default=0,
        )

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        main = self._main_input(ctx)
        side = self._side_input(ctx)
        if self.mode is ComparatorMode.SUBTRACT:
            result = clamp_power(main - side)
        else:  # COMPARE: pass main through unless a side is stronger
            result = main if main >= side else 0

        self._buffer.append(result)
        emitted = self._buffer.pop(0)
        return self._set_output(Signal.strong(emitted) if emitted > 0 else OFF)

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.mode.value, tuple(self._buffer))
