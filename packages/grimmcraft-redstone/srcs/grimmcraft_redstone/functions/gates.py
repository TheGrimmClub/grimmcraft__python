"""Composite logic gates, modelled as single logic components.

The primitive redstone gate is the torch inverter (:class:`NotGate` *is* a
:class:`~grimmcraft_redstone.functions.torch.RedstoneTorch` in silicon); AND/OR/
XOR/NAND are the standard torch-and-dust builds.  Here each gate is expressed as
one :class:`LogicGate` component whose boolean function is evaluated *through the
simulator* — the faithful abstraction of those primitive builds, so truth-table
tests drive real ticks.  See ``docs/`` for the equivalent primitive layouts.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import ClassVar

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block
from grimmcraft_redstone.component import RedstoneComponent, SignalChange, SimContext
from grimmcraft_redstone.signal import OFF, Signal


class LogicGate(RedstoneComponent):
    """A gate whose full-strength output is a boolean function of its inputs."""

    EMITS_POWER = True
    BLOCK = Block.REDSTONE_TORCH

    #: Number of boolean inputs this gate reads.
    ARITY: ClassVar[int] = 2

    def __init__(
        self,
        position: BlockPos,
        *,
        input_dirs: Iterable[Direction] | None = None,
        facing: Direction = Direction.NORTH,
    ) -> None:
        super().__init__(position, facing=facing)
        self._input_dirs = (
            tuple(input_dirs) if input_dirs is not None else self._default_inputs()
        )
        if len(self._input_dirs) != self.ARITY:
            raise ValueError(
                f"{self.name} needs {self.ARITY} input(s), got {len(self._input_dirs)}"
            )

    def _default_inputs(self) -> tuple[Direction, ...]:
        if self.ARITY == 1:
            return (Direction.WEST,)
        return (Direction.WEST, Direction.EAST)

    def inputs(self) -> Iterable[Direction]:
        return self._input_dirs

    def evaluate(self, values: Sequence[bool]) -> bool:
        """The gate's boolean output for its ordered input values."""
        raise NotImplementedError

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        values = [ctx.power_into(self.position, d).is_on for d in self._input_dirs]
        result = self.evaluate(values)
        return self._set_output(Signal.strong() if result else OFF)


class NotGate(LogicGate):
    """NOT — a torch inverter."""

    ARITY = 1

    def evaluate(self, values: Sequence[bool]) -> bool:
        return not values[0]


class AndGate(LogicGate):
    """AND — true only when every input is on."""

    def evaluate(self, values: Sequence[bool]) -> bool:
        return all(values)


class OrGate(LogicGate):
    """OR — true when any input is on."""

    def evaluate(self, values: Sequence[bool]) -> bool:
        return any(values)


class NandGate(LogicGate):
    """NAND — the negation of AND."""

    def evaluate(self, values: Sequence[bool]) -> bool:
        return not all(values)


class XorGate(LogicGate):
    """XOR — true when an odd number of inputs are on (a two-input difference)."""

    def evaluate(self, values: Sequence[bool]) -> bool:
        return sum(1 for v in values if v) % 2 == 1
