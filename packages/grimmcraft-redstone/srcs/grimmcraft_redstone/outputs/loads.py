"""Concrete loads — the *outputs* family.

Each reacts to incoming power: level-triggered devices follow the power (lamp,
door, rails, TNT), edge-triggered devices fire once per rising edge (dispenser,
dropper, note block, bell), the hopper is *locked while powered*, and the piston
extends/retracts with the sticky-retract quirk and a 12-block push limit.
"""

from __future__ import annotations

from collections.abc import Sequence

from grimmcraft_core.coordinates import BlockPos, Direction
from grimmcraft_data.block import Block
from grimmcraft_redstone.component import SignalChange, SimContext
from grimmcraft_redstone.outputs.base import Load

#: A piston can push at most this many blocks.
PISTON_PUSH_LIMIT = 12


class RedstoneLamp(Load):
    """A lamp: lit exactly while it is powered."""

    BLOCK = Block.REDSTONE_LAMP

    @property
    def lit(self) -> bool:
        """Whether the lamp is currently lit."""
        return self.active


class Piston(Load):
    """A piston: extends its head while powered, retracts when unpowered.

    ``sticky`` pistons pull the pushed block back on retract; a normal piston
    leaves it behind.  ``quasi_connectivity`` enables the **Java-only** BUD quirk
    where the piston is also powered *through* the block directly above it (off by
    default, matching Bedrock — see the package docs for the Java/Bedrock split).
    """

    BLOCK = Block.PISTON

    def __init__(
        self,
        position: BlockPos,
        *,
        facing: Direction = Direction.UP,
        sticky: bool = False,
        quasi_connectivity: bool = False,
    ) -> None:
        block = Block.STICKY_PISTON if sticky else Block.PISTON
        super().__init__(position, facing=facing, block_type=block)
        self.sticky = sticky
        self.quasi_connectivity = quasi_connectivity
        self.extended = False
        #: The block the head pulled (sticky pistons only), if any.
        self.holding = False

    @property
    def head_pos(self) -> BlockPos:
        """Where the piston head sits when extended (one block along ``facing``)."""
        return self.position.step(self.facing)

    def update(self, ctx: SimContext, tick: int) -> Sequence[SignalChange]:
        powered = ctx.incoming_power(self).is_on
        if not powered and self.quasi_connectivity:
            # BUD: also read power from the block one above (Java-only).
            powered = ctx.block_powered(self.position.step(Direction.UP))
        was = self.extended
        self.extended = powered
        if powered and not was:
            self.holding = True  # pushed a block out
        elif not powered and was:
            self.holding = self.sticky  # sticky keeps the block, normal drops it
        self.active = powered
        self._was_powered = powered
        return ()

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.extended, self.holding)


class StickyPiston(Piston):
    """A sticky piston: a :class:`Piston` that pulls its block back on retract."""

    BLOCK = Block.STICKY_PISTON

    def __init__(
        self,
        position: BlockPos,
        *,
        facing: Direction = Direction.UP,
        quasi_connectivity: bool = False,
    ) -> None:
        super().__init__(
            position,
            facing=facing,
            sticky=True,
            quasi_connectivity=quasi_connectivity,
        )


class _EdgeMachine(Load):
    """A load that *fires* once on each rising power edge (base for triggerables)."""

    def __init__(self, position: BlockPos, **kwargs: object) -> None:
        super().__init__(position, **kwargs)  # type: ignore[arg-type]
        self.fire_count = 0

    def _on_power(self, powered: bool, *, rising: bool, falling: bool) -> None:
        if rising:
            self.fire_count += 1

    @property
    def fired(self) -> bool:
        """Whether the device has fired at least once."""
        return self.fire_count > 0

    def state_key(self) -> tuple[object, ...]:
        return (*super().state_key(), self.fire_count)


class Dispenser(_EdgeMachine):
    """A dispenser: dispenses one item on each rising power edge."""

    BLOCK = Block.DISPENSER


class Dropper(_EdgeMachine):
    """A dropper: drops one item on each rising power edge."""

    BLOCK = Block.DROPPER


class NoteBlock(_EdgeMachine):
    """A note block: plays its note on each rising power edge."""

    BLOCK = Block.NOTE_BLOCK

    @property
    def plays(self) -> int:
        """How many times the note has played."""
        return self.fire_count


class Bell(_EdgeMachine):
    """A bell: rings on each rising power edge."""

    BLOCK = Block.BELL

    @property
    def rings(self) -> int:
        """How many times the bell has rung."""
        return self.fire_count


class Hopper(Load):
    """A hopper: transfers items unless powered — powering it *locks* it."""

    BLOCK = Block.HOPPER

    @property
    def locked(self) -> bool:
        """Whether item transfer is currently disabled (i.e. powered)."""
        return self.active


class Door(Load):
    """A door: open while powered."""

    BLOCK = Block.IRON_DOOR

    @property
    def open(self) -> bool:
        """Whether the door is currently open."""
        return self.active


class Trapdoor(Load):
    """A trapdoor: open while powered."""

    BLOCK = Block.OAK_TRAPDOOR

    @property
    def open(self) -> bool:
        return self.active


class FenceGate(Load):
    """A fence gate: open while powered."""

    BLOCK = Block.OAK_FENCE_GATE

    @property
    def open(self) -> bool:
        return self.active


class Tnt(Load):
    """TNT: ignites (primes) while powered."""

    BLOCK = Block.TNT

    @property
    def primed(self) -> bool:
        """Whether the TNT is currently primed to explode."""
        return self.active


class PoweredRail(Load):
    """A powered rail: propels carts while powered."""

    BLOCK = Block.POWERED_RAIL

    @property
    def propelling(self) -> bool:
        return self.active


class ActivatorRail(Load):
    """An activator rail: activates carts while powered."""

    BLOCK = Block.ACTIVATOR_RAIL

    @property
    def activating(self) -> bool:
        return self.active
