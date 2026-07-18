"""The :class:`RedstoneComponent` base and the structural role protocols.

Every placed redstone thing is a :class:`RedstoneComponent`: it has a
:class:`~grimmcraft_core.coordinates.BlockPos` in the world, a
:class:`~grimmcraft_core.coordinates.Direction` it faces, and a
:class:`~grimmcraft_data.block.Block` type.  Its behaviour is expressed through
three methods the engine calls — :meth:`~RedstoneComponent.output_signal`,
:meth:`~RedstoneComponent.inputs` and :meth:`~RedstoneComponent.update`.

Rather than a deep class tree, components advertise *roles* through the small
:class:`typing.Protocol` types here (:class:`PowerSource`, :class:`Conductor`,
:class:`Load`, :class:`LogicGate`); the four family sub-packages implement them.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import ClassVar, Protocol, runtime_checkable

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block
from grimmcraft_redstone.signal import OFF, Signal


class SignalChange:
    """A record that a component's published output changed this tick.

    Emitted by :meth:`RedstoneComponent.update` and consumed by the simulator to
    know what to re-evaluate (and by tests/examples to observe activity).
    """

    __slots__ = ("pos", "old", "new")

    def __init__(self, pos: BlockPos, old: Signal, new: Signal) -> None:
        self.pos = pos
        self.old = old
        self.new = new

    def __repr__(self) -> str:
        return f"SignalChange({self.pos}, {self.old} -> {self.new})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SignalChange):
            return NotImplemented
        return (self.pos, self.old, self.new) == (other.pos, other.old, other.new)


@runtime_checkable
class SimContext(Protocol):
    """The read-only view of the circuit the simulator hands to each component.

    A component's :meth:`RedstoneComponent.update` reads *only* through this
    interface, which keeps components pure with respect to the engine and makes
    them unit-testable with a stub context.
    """

    tick: int

    def output_at(self, pos: BlockPos) -> Signal:
        """The signal currently published by the component at ``pos`` (or off)."""
        ...

    def component_at(self, pos: BlockPos) -> RedstoneComponent | None:
        """The component placed at ``pos``, if any."""
        ...

    def power_into(self, pos: BlockPos, direction: Direction) -> Signal:
        """The signal arriving at ``pos`` from its neighbour toward ``direction``."""
        ...

    def incoming_power(self, component: RedstoneComponent) -> Signal:
        """The strongest signal arriving on any of ``component``'s input faces."""
        ...

    def dust_power(self, pos: BlockPos) -> int:
        """The redstone-wire power level (0-15) resolved at ``pos``."""
        ...

    def block_powered(self, pos: BlockPos) -> bool:
        """Whether the (solid) block at ``pos`` is powered, strongly or weakly."""
        ...


class RedstoneComponent:
    """Base class for every placed redstone component.

    Subclasses set the class attribute :attr:`BLOCK` and override
    :meth:`output_signal`, :meth:`inputs` and/or :meth:`update`.  Runtime state
    (a lever's on/off, a repeater's delay buffer) lives on the instance; the
    published output is cached in ``_output`` and mutated only via
    :meth:`_set_output`, which also produces the :class:`SignalChange` records.
    """

    #: The Minecraft block this component represents.
    BLOCK: ClassVar[Block]

    #: Whether this component emits power *into adjacent redstone dust* (sources,
    #: torches and diode outputs do; dust and passive loads do not).
    EMITS_POWER: ClassVar[bool] = False

    #: Whether this component is a full solid block that can conduct/attach power.
    IS_SOLID: ClassVar[bool] = False

    #: Whether this component is a redstone-dust wire (special-cased by the engine).
    IS_DUST: ClassVar[bool] = False

    #: Whether a comparator behind this component can read a container signal.
    IS_CONTAINER: ClassVar[bool] = False

    def __init__(
        self,
        position: BlockPos,
        *,
        facing: Direction = Direction.UP,
        block_type: Block | None = None,
    ) -> None:
        self.position = position
        self.facing = facing
        self.block_type = block_type if block_type is not None else type(self).BLOCK
        self._output: Signal = OFF

    # -- identity -------------------------------------------------------------
    @property
    def name(self) -> str:
        """The component's class name (used in diagnostics and reprs)."""
        return type(self).__name__

    def __repr__(self) -> str:
        return f"{self.name}(pos={self.position}, facing={self.facing.value})"

    # -- the component interface ---------------------------------------------
    def output_signal(self) -> Signal:
        """The signal this component currently emits (its cached output)."""
        return self._output

    def inputs(self) -> Iterable[Direction]:
        """The faces this component reads incoming power from.

        Defaults to all six faces; sources override to ``()`` and diodes
        (repeaters/comparators) to their single back face.
        """
        return tuple(Direction)

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        """Recompute internal state from ``ctx`` and return any output changes.

        The default is inert (a plain block).  ``tick`` is the current game tick.
        """
        return ()

    # -- helpers for subclasses ----------------------------------------------
    def _set_output(self, new: Signal) -> list[SignalChange]:
        """Publish ``new`` as the output, returning a change record iff it moved."""
        if new == self._output:
            return []
        change = SignalChange(self.position, self._output, new)
        self._output = new
        return [change]

    def reset(self) -> None:
        """Return the component to its powered-off initial state."""
        self._output = OFF

    def state_key(self) -> tuple[object, ...]:
        """A hashable snapshot of *all* runtime state, for oscillation detection.

        The default covers the published output; components with internal timing
        (repeater/comparator buffers, torch burnout, button countdowns) extend it
        so a mid-delay circuit is not mistaken for a stable one.
        """
        return (self._output.level, self._output.kind.value)


# --- role protocols ----------------------------------------------------------
@runtime_checkable
class PowerSource(Protocol):
    """A component that *originates* signal (lever, button, redstone block, …)."""

    def output_signal(self) -> Signal: ...


@runtime_checkable
class Conductor(Protocol):
    """A component that *carries* signal between others (dust, solid blocks)."""

    def conducts(self, direction: Direction) -> bool:
        """Whether signal may travel out of this conductor toward ``direction``."""
        ...


@runtime_checkable
class Load(Protocol):
    """A component that *consumes* signal and does something (lamp, piston, …)."""

    @property
    def active(self) -> bool:
        """Whether the load is currently switched on by incoming power."""
        ...


@runtime_checkable
class LogicGate(Protocol):
    """A component whose output is a boolean function of its inputs."""

    def evaluate(self, inputs: Sequence[bool]) -> bool:
        """The gate's output for the given ordered boolean ``inputs``."""
        ...
